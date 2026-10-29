from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


class DocumentMeta(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    status: DocumentStatus
    chunk_count: int = 0
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: DocumentStatus
    message: str


class DocumentListResponse(BaseModel):
    documents: List[DocumentMeta]
    total: int


class SourceChunk(BaseModel):
    document_id: str
    document_name: str
    chunk_index: int
    page_number: Optional[int] = None
    text: str
    score: float = 0.0


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    conversation_id: Optional[str] = None
    document_ids: Optional[List[str]] = None  # restrict to specific docs
    use_agent: bool = True


class AgentStep(BaseModel):
    tool: str
    reason: str
    result_summary: str
    sources_count: int
    success: bool


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceChunk] = []
    agent_steps: List[AgentStep] = []
    conversation_id: str
    no_answer: bool = False


class SummaryRequest(BaseModel):
    document_id: str


class SummaryResponse(BaseModel):
    document_id: str
    document_name: str
    summary: str
    key_points: List[str] = []


class CompareRequest(BaseModel):
    document_ids: List[str] = Field(..., min_length=2, max_length=5)
    question: Optional[str] = None


class CompareResponse(BaseModel):
    similarities: List[str]
    differences: List[str]
    summary: str
    sources: List[SourceChunk] = []


class HealthResponse(BaseModel):
    status: str
    version: str
    llm_provider: str
    llm_model: str
    embedding_model: str
    vector_db: str
    document_count: int


class ModelStatusResponse(BaseModel):
    llm_provider: str
    llm_model: str
    llm_ready: bool
    llm_local: bool
    embedding_model: str
    embedding_ready: bool
    vector_db_status: str
    document_count: int


class AgentToolInfo(BaseModel):
    name: str
    description: str
    enabled: bool
