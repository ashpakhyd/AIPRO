from fastapi import APIRouter, Depends
from app.schemas.models import HealthResponse, ModelStatusResponse, AgentToolInfo
from app.core.config import get_settings
from app.ingestion.vector_store import check_vector_db_ready, get_total_chunk_count
from app.ingestion.embeddings import check_embedding_ready
from app.models.llm_provider import check_llm_ready, is_llm_local
from app.database.db import get_db, AsyncSession
from app.database.repository import DocumentRepository
from typing import List

router = APIRouter()
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    repo = DocumentRepository(db)
    docs = await repo.list_all()
    return HealthResponse(
        status="ok",
        version="1.0.0",
        llm_provider=settings.llm_provider,
        llm_model=settings.llm_model_id,
        embedding_model=settings.embedding_model,
        vector_db=check_vector_db_ready(),
        document_count=len(docs),
    )


@router.get("/models/status", response_model=ModelStatusResponse)
async def model_status(db: AsyncSession = Depends(get_db)):
    repo = DocumentRepository(db)
    docs = await repo.list_all()
    return ModelStatusResponse(
        llm_provider=settings.llm_provider,
        llm_model=settings.llm_model_id,
        llm_ready=check_llm_ready(),
        llm_local=is_llm_local(),
        embedding_model=settings.embedding_model,
        embedding_ready=check_embedding_ready(),
        vector_db_status=check_vector_db_ready(),
        document_count=len(docs),
    )


@router.get("/agent/tools", response_model=List[AgentToolInfo])
async def list_agent_tools():
    return [
        AgentToolInfo(name="document_search", description="Search indexed documents for relevant information.", enabled=True),
        AgentToolInfo(name="document_summarizer", description="Generate a summary of a selected document.", enabled=True),
        AgentToolInfo(name="document_comparison", description="Compare information across multiple documents.", enabled=True),
        AgentToolInfo(name="web_search", description="Search the web for external information.", enabled=settings.web_search_enabled),
    ]
