import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.core.config import get_settings
from app.core.errors import ValidationError, ProcessingError
from app.core.logging import logger
from app.database.db import AsyncSession
from app.database.repository import DocumentRepository, record_to_meta
from app.ingestion.extractor import extract_text
from app.ingestion.chunker import chunk_pages
from app.ingestion.embeddings import embed_texts
from app.ingestion.vector_store import add_chunks, delete_document_chunks
from app.schemas.models import DocumentMeta, DocumentStatus

settings = get_settings()

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}
os.makedirs(settings.upload_dir, exist_ok=True)


def validate_file(filename: str, file_size: int) -> str:
    ext = Path(filename).suffix.lstrip(".").lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(f"Unsupported file type '.{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")
    if file_size > settings.max_upload_bytes:
        raise ValidationError(f"File too large. Max size: {settings.max_upload_size_mb}MB")
    return ext


async def ingest_document(
    file_bytes: bytes,
    original_filename: str,
    db: AsyncSession,
) -> DocumentMeta:
    file_size = len(file_bytes)
    ext = validate_file(original_filename, file_size)

    doc_id = str(uuid.uuid4())
    safe_filename = f"{doc_id}.{ext}"
    file_path = os.path.join(settings.upload_dir, safe_filename)

    # Save file
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    now = datetime.now(timezone.utc)
    meta = DocumentMeta(
        id=doc_id,
        filename=safe_filename,
        original_filename=original_filename,
        file_size=file_size,
        file_type=ext,
        status=DocumentStatus.PROCESSING,
        created_at=now,
        updated_at=now,
    )

    repo = DocumentRepository(db)
    await repo.create(meta)

    # Process asynchronously (inline for simplicity)
    try:
        pages = extract_text(file_path, ext)
        if not pages:
            raise ProcessingError("No text could be extracted from the document.")

        chunks = chunk_pages(pages, doc_id, original_filename)
        if not chunks:
            raise ProcessingError("Document produced no chunks after splitting.")

        texts = [c["text"] for c in chunks]
        embeddings = embed_texts(texts)
        add_chunks(chunks, embeddings)

        await repo.update_status(doc_id, DocumentStatus.INDEXED, chunk_count=len(chunks))
        meta.status = DocumentStatus.INDEXED
        meta.chunk_count = len(chunks)
        logger.info(f"Indexed document {doc_id} with {len(chunks)} chunks.")

    except Exception as e:
        logger.error(f"Failed to index document {doc_id}: {e}")
        await repo.update_status(doc_id, DocumentStatus.FAILED, error_message=str(e))
        meta.status = DocumentStatus.FAILED
        meta.error_message = str(e)

    return meta


async def delete_document(doc_id: str, db: AsyncSession) -> bool:
    repo = DocumentRepository(db)
    record = await repo.get(doc_id)
    if not record:
        return False

    # Remove vectors
    try:
        removed = delete_document_chunks(doc_id)
        logger.info(f"Removed {removed} vectors for document {doc_id}")
    except Exception as e:
        logger.warning(f"Vector deletion failed for {doc_id}: {e}")

    # Remove file
    file_path = os.path.join(settings.upload_dir, record.filename)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logger.warning(f"File deletion failed for {file_path}: {e}")

    await repo.delete(doc_id)
    return True
