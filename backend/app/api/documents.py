from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.schemas.models import (
    DocumentUploadResponse, DocumentListResponse, DocumentMeta,
    DocumentStatus, SummaryRequest, SummaryResponse,
)
from app.database.db import get_db, AsyncSession
from app.database.repository import DocumentRepository, record_to_meta
from app.ingestion.pipeline import ingest_document, delete_document
from app.core.errors import NotFoundError
from app.tools.agent_tools import tool_summarize_document

router = APIRouter(prefix="/documents")


@router.get("", response_model=DocumentListResponse)
async def list_documents(db: AsyncSession = Depends(get_db)):
    repo = DocumentRepository(db)
    records = await repo.list_all()
    docs = [record_to_meta(r) for r in records]
    return DocumentListResponse(documents=docs, total=len(docs))


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    meta = await ingest_document(content, file.filename or "upload", db)
    return DocumentUploadResponse(
        document_id=meta.id,
        filename=meta.original_filename,
        status=meta.status,
        message="Document indexed successfully." if meta.status == DocumentStatus.INDEXED else f"Processing failed: {meta.error_message}",
    )


@router.get("/{document_id}", response_model=DocumentMeta)
async def get_document(document_id: str, db: AsyncSession = Depends(get_db)):
    repo = DocumentRepository(db)
    record = await repo.get(document_id)
    if not record:
        raise NotFoundError("Document")
    return record_to_meta(record)


@router.delete("/{document_id}")
async def delete_doc(document_id: str, db: AsyncSession = Depends(get_db)):
    deleted = await delete_document(document_id, db)
    if not deleted:
        raise NotFoundError("Document")
    return {"message": "Document deleted successfully.", "document_id": document_id}


@router.post("/{document_id}/summary", response_model=SummaryResponse)
async def summarize_document(document_id: str, db: AsyncSession = Depends(get_db)):
    repo = DocumentRepository(db)
    record = await repo.get(document_id)
    if not record:
        raise NotFoundError("Document")
    if record.status != "indexed":
        raise HTTPException(status_code=400, detail="Document is not indexed yet.")

    result = tool_summarize_document(document_id, record.original_filename)
    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])

    return SummaryResponse(
        document_id=document_id,
        document_name=record.original_filename,
        summary=result.get("summary", ""),
        key_points=result.get("key_points", []),
    )
