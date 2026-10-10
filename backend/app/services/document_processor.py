from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk
from app.services.chunking import chunk_text
from app.services.embedding_service import generate_embeddings
from app.services.vector_store import store_chunk_embedding


def process_document_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[str]:
    """Split extracted document text into overlapping chunks."""
    if not text or not text.strip():
        return []

    return chunk_text(
        text=text,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )


def save_document_chunks(
    db: Session,
    document_id: int,
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    user_id: int | None = None,
) -> list[DocumentChunk]:
    """
    Save document chunks in PostgreSQL and their embeddings in Qdrant.

    PostgreSQL remains the source of truth for document chunks.
    """
    chunks = process_document_text(
        text=text,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    if not chunks:
        return []

    document_chunks = []

    try:
        for index, content in enumerate(chunks):
            document_chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=index,
                content=content,
            )
            db.add(document_chunk)
            document_chunks.append(document_chunk)

        # Generate embeddings for all chunks in one batch.
        embeddings = generate_embeddings(chunks)

        # Persist the database records first to obtain their IDs.
        db.flush()

        if user_id is None:
            from app.models.document import Document

            document = db.get(Document, document_id)
            if document is None:
                raise ValueError(f"Document {document_id} not found.")

            user_id = document.user_id

        # Save chunks and embeddings to Qdrant.
        for document_chunk, content, embedding in zip(
            document_chunks, chunks, embeddings
        ):
            store_chunk_embedding(
                chunk_id=document_chunk.id,
                document_id=document_id,
                user_id=user_id,
                chunk_text=content,
                embedding=embedding,
            )

        db.commit()

        for document_chunk in document_chunks:
            db.refresh(document_chunk)

        return document_chunks

    except Exception:
        db.rollback()
        raise