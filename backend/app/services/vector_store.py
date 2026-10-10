
import os

from qdrant_client import QdrantClient, models


QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
COLLECTION_NAME = "enterprise_documents"
VECTOR_SIZE = 384


def get_qdrant_client() -> QdrantClient:
    """Create a client for the Qdrant vector database."""
    return QdrantClient(url=QDRANT_URL, timeout=30)


def ensure_collection() -> None:
    """Create the vector collection if it does not exist."""
    client = get_qdrant_client()

    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=VECTOR_SIZE,
                distance=models.Distance.COSINE,
            ),
        )


def store_chunk_embedding(
    chunk_id: int,
    document_id: int,
    user_id: int,
    chunk_text: str,
    embedding: list[float],
) -> None:
    """Store a document chunk and its embedding in Qdrant."""
    if len(embedding) != VECTOR_SIZE:
        raise ValueError(
            f"Expected {VECTOR_SIZE} dimensions, got {len(embedding)}"
        )

    ensure_collection()
    client = get_qdrant_client()

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            models.PointStruct(
                id=chunk_id,
                vector=embedding,
                payload={
                    "document_id": document_id,
                    "user_id": user_id,
                    "chunk_id": chunk_id,
                    "text": chunk_text,
                },
            )
        ],
        wait=True,
    )


def search_similar_chunks(
    query_embedding: list[float],
    user_id: int,
    limit: int = 5,
) -> list[dict]:
    """Search only the current user's document chunks."""
    if len(query_embedding) != VECTOR_SIZE:
        raise ValueError(
            f"Expected {VECTOR_SIZE} dimensions, got {len(query_embedding)}"
        )

    if user_id <= 0:
        raise ValueError("user_id must be a positive integer")

    if limit < 1 or limit > 50:
        raise ValueError("limit must be between 1 and 50")

    client = get_qdrant_client()

    if not client.collection_exists(COLLECTION_NAME):
        return []

    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        query_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="user_id",
                    match=models.MatchValue(value=user_id),
                )
            ]
        ),
        limit=limit,
        with_payload=True,
    )

    results = []

    for point in response.points:
        payload = point.payload or {}

        results.append(
            {
                "chunk_id": payload.get("chunk_id"),
                "document_id": payload.get("document_id"),
                "text": payload.get("text", ""),
                "score": point.score,
            }
        )

    return results
