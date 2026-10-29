from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.database.db import DocumentRecord, ConversationRecord
from app.schemas.models import DocumentMeta, DocumentStatus
from datetime import datetime, timezone
from typing import Optional, List
import json


class DocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, doc: DocumentMeta) -> DocumentRecord:
        record = DocumentRecord(
            id=doc.id,
            filename=doc.filename,
            original_filename=doc.original_filename,
            file_size=doc.file_size,
            file_type=doc.file_type,
            status=doc.status.value,
            chunk_count=doc.chunk_count,
            error_message=doc.error_message,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def get(self, doc_id: str) -> Optional[DocumentRecord]:
        result = await self.db.execute(
            select(DocumentRecord).where(DocumentRecord.id == doc_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> List[DocumentRecord]:
        result = await self.db.execute(
            select(DocumentRecord).order_by(DocumentRecord.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        doc_id: str,
        status: DocumentStatus,
        chunk_count: int = 0,
        error_message: Optional[str] = None,
    ):
        record = await self.get(doc_id)
        if record:
            record.status = status.value
            record.chunk_count = chunk_count
            record.error_message = error_message
            record.updated_at = datetime.now(timezone.utc)
            await self.db.commit()

    async def delete(self, doc_id: str) -> bool:
        result = await self.db.execute(
            delete(DocumentRecord).where(DocumentRecord.id == doc_id)
        )
        await self.db.commit()
        return result.rowcount > 0


def record_to_meta(r: DocumentRecord) -> DocumentMeta:
    return DocumentMeta(
        id=r.id,
        filename=r.filename,
        original_filename=r.original_filename,
        file_size=r.file_size,
        file_type=r.file_type,
        status=DocumentStatus(r.status),
        chunk_count=r.chunk_count,
        error_message=r.error_message,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )
