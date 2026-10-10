from functools import lru_cache

from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Load the embedding model once and reuse it."""
    return SentenceTransformer(
        MODEL_NAME,
        device="cpu",
    )


def generate_embedding(text: str) -> list[float]:
    """Convert one text into a normalized 384-dimensional vector."""
    if not text or not text.strip():
        raise ValueError("Text cannot be empty.")

    model = get_embedding_model()

    vector = model.encode(
        text.strip(),
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    return vector.tolist()


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Convert multiple text chunks into vectors."""
    cleaned_texts = [
        text.strip() for text in texts
        if text and text.strip()
    ]

    if not cleaned_texts:
        return []

    model = get_embedding_model()

    vectors = model.encode(
        cleaned_texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )

    return vectors.tolist()