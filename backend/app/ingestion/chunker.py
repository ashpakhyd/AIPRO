from typing import List, Tuple, Dict, Any
from app.core.config import get_settings

settings = get_settings()


def chunk_pages(
    pages: List[Tuple[str, int]],
    document_id: str,
    original_filename: str,
    chunk_size: int = None,
    chunk_overlap: int = None,
) -> List[Dict[str, Any]]:
    """
    Split page/section texts into overlapping chunks.
    Returns list of chunk dicts with text and metadata.
    """
    chunk_size = chunk_size or settings.rag_chunk_size
    chunk_overlap = chunk_overlap or settings.rag_chunk_overlap

    chunks = []
    chunk_index = 0

    for text, page_num in pages:
        # Simple character-based sliding window
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(
                    {
                        "id": f"{document_id}_chunk_{chunk_index}",
                        "text": chunk_text,
                        "metadata": {
                            "document_id": document_id,
                            "document_name": original_filename,
                            "page_number": page_num,
                            "chunk_index": chunk_index,
                        },
                    }
                )
                chunk_index += 1
            if end >= len(text):
                break
            start = end - chunk_overlap

    return chunks
