from typing import List
from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()
_embedding_model = None


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        logger.info(f"Loading embedding model: {settings.embedding_model}")
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer(
            settings.embedding_model, device=settings.embedding_device
        )
        logger.info("Embedding model loaded.")
    return _embedding_model


def embed_texts(texts: List[str]) -> List[List[float]]:
    model = get_embedding_model()
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return embeddings.tolist()


def embed_query(text: str) -> List[float]:
    return embed_texts([text])[0]


def check_embedding_ready() -> bool:
    try:
        get_embedding_model()
        return True
    except Exception as e:
        logger.error(f"Embedding model not ready: {e}")
        return False
