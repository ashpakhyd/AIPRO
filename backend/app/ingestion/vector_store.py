import chromadb
from typing import List, Dict, Any, Optional
from app.core.config import get_settings
from app.core.logging import logger
import os

settings = get_settings()
_client = None
_collection = None


def get_chroma_client():
    global _client
    if _client is None:
        os.makedirs(settings.chroma_persist_dir, exist_ok=True)
        _client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        logger.info(f"ChromaDB initialized at {settings.chroma_persist_dir}")
    return _client


def get_collection():
    global _collection
    if _collection is None:
        client = get_chroma_client()
        _collection = client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def add_chunks(chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
    collection = get_collection()
    ids = [c["id"] for c in chunks]
    texts = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]
    collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)


def query_chunks(
    query_embedding: List[float],
    top_k: int = 5,
    document_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    collection = get_collection()
    where = {"document_id": {"$in": document_ids}} if document_ids else None
    if document_ids:
        filtered_count = len(collection.get(where=where)["ids"])
    else:
        filtered_count = collection.count()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, max(filtered_count, 1)),
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    return results


def delete_document_chunks(document_id: str) -> int:
    collection = get_collection()
    results = collection.get(where={"document_id": document_id})
    ids = results.get("ids", [])
    if ids:
        collection.delete(ids=ids)
    return len(ids)


def get_document_chunk_count(document_id: str) -> int:
    collection = get_collection()
    results = collection.get(where={"document_id": document_id})
    return len(results.get("ids", []))


def get_total_chunk_count() -> int:
    return get_collection().count()


def check_vector_db_ready() -> str:
    try:
        count = get_total_chunk_count()
        return f"ok ({count} chunks)"
    except Exception as e:
        return f"error: {e}"
