from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile
from xml.etree import ElementTree

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.models.base import get_db
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.user import User
from app.services.document_processor import save_document_chunks


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}


def extract_pdf_text(file_path: Path) -> str:
    reader = PdfReader(str(file_path))
    extracted_pages = []

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            extracted_pages.append(page_text)

    return "\n\n".join(extracted_pages).strip()


def extract_txt_text(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8-sig").strip()


def extract_docx_text(file_path: Path) -> str:
    with ZipFile(file_path) as archive:
        xml_content = archive.read("word/document.xml")

    root = ElementTree.fromstring(xml_content)
    namespace = {
        "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    }

    paragraphs = []

    for paragraph in root.findall(".//w:p", namespace):
        parts = [
            node.text or ""
            for node in paragraph.findall(".//w:t", namespace)
        ]
        paragraph_text = "".join(parts).strip()

        if paragraph_text:
            paragraphs.append(paragraph_text)

    return "\n\n".join(paragraphs).strip()


def extract_document_text(file_path: Path, extension: str) -> str:
    if extension == ".pdf":
        return extract_pdf_text(file_path)

    if extension == ".txt":
        return extract_txt_text(file_path)

    if extension == ".docx":
        return extract_docx_text(file_path)

    return ""


@router.post("/upload", status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    extension = Path(file.filename or "").suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Allowed: PDF, TXT, DOCX",
        )

    stored_filename = f"{uuid4().hex}{extension}"
    file_path = UPLOAD_DIR / stored_filename

    try:
        with file_path.open("wb") as buffer:
            while True:
                file_chunk = file.file.read(1024 * 1024)
                if not file_chunk:
                    break
                buffer.write(file_chunk)

        extracted_text = extract_document_text(file_path, extension)

    except Exception as exc:
        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read uploaded file: {type(exc).__name__}",
        ) from exc

    document = Document(
        user_id=current_user.id,
        filename=file.filename or stored_filename,
        file_path=str(file_path),
        file_type=extension,
        status="processed" if extracted_text else "uploaded",
        extracted_text=extracted_text or None,
    )

    try:
        db.add(document)
        db.commit()
        db.refresh(document)

        chunk_count = 0

        if extracted_text:
            chunks = save_document_chunks(
                db=db,
                document_id=document.id,
                text=extracted_text,
                user_id=current_user.id,
            )
            chunk_count = len(chunks)

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Document upload, chunking, or vector indexing failed: "
                f"{type(exc).__name__}. Check backend logs."
            ),
        ) from exc

    return {
        "id": document.id,
        "filename": document.filename,
        "file_type": document.file_type,
        "status": document.status,
        "text_extracted": bool(extracted_text),
        "text_length": len(extracted_text),
        "chunks_created": chunk_count,
        "created_at": document.created_at,
    }


@router.get("/")
def get_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    documents = (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
        .all()
    )

    return [
        {
            "id": document.id,
            "filename": document.filename,
            "file_type": document.file_type,
            "status": document.status,
            "text_extracted": bool(document.extracted_text),
            "text_length": len(document.extracted_text or ""),
            "created_at": document.created_at,
        }
        for document in documents
    ]


@router.get("/{document_id}")
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return {
        "id": document.id,
        "filename": document.filename,
        "file_type": document.file_type,
        "status": document.status,
        "text": document.extracted_text,
        "text_length": len(document.extracted_text or ""),
        "created_at": document.created_at,
    }


@router.get("/{document_id}/chunks")
def get_document_chunks(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index.asc())
        .all()
    )

    return [
        {
            "id": chunk.id,
            "document_id": chunk.document_id,
            "chunk_index": chunk.chunk_index,
            "content": chunk.content,
            "created_at": chunk.created_at,
        }
        for chunk in chunks
    ]
