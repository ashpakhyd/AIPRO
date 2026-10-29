from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.schemas.models import ChatRequest, ChatResponse, CompareRequest, CompareResponse
from app.agents.orchestrator import run_agent
from app.tools.agent_tools import tool_compare_documents
from app.database.db import get_db, AsyncSession
from app.database.repository import DocumentRepository, record_to_meta
from app.core.errors import NotFoundError
from app.ingestion.embeddings import embed_query
from app.ingestion.vector_store import query_chunks
from app.core.config import get_settings
from app.schemas.models import SourceChunk
import uuid, json

settings = get_settings()

router = APIRouter()


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    conversation_id = request.conversation_id or str(uuid.uuid4())

    # Resolve sources first
    query_emb = embed_query(request.question)
    results = query_chunks(query_emb, top_k=settings.rag_top_k, document_ids=request.document_ids or None)
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    sources = []
    for text, meta, dist in zip(docs, metas, distances):
        score = 1.0 - dist
        if score < settings.rag_similarity_threshold:
            continue
        sources.append(SourceChunk(
            document_id=meta.get("document_id", ""),
            document_name=meta.get("document_name", "Unknown"),
            chunk_index=meta.get("chunk_index", 0),
            page_number=meta.get("page_number"),
            text=text,
            score=round(score, 4),
        ))

    from app.rag.chain import build_rag_prompt
    from app.core.config import get_settings
    from langchain_openai import ChatOpenAI
    import os

    prompt = build_rag_prompt(request.question, sources) if sources else request.question

    async def generate():
        # Send sources + conversation_id first as metadata
        meta_chunk = json.dumps({
            "type": "meta",
            "conversation_id": conversation_id,
            "sources": [s.model_dump() for s in sources],
        })
        yield f"data: {meta_chunk}\n\n"

        # Stream LLM tokens
        llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            max_tokens=settings.llm_max_new_tokens,
            temperature=settings.llm_temperature,
            streaming=True,
        )
        async for chunk in llm.astream(prompt):
            token = chunk.content
            if token:
                yield f"data: {json.dumps({'type': 'token', 'text': token})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    conversation_id = request.conversation_id or str(uuid.uuid4())

    # Resolve doc name for summary intent
    doc_name = None
    doc_id_for_summary = None
    if request.document_ids and len(request.document_ids) == 1:
        repo = DocumentRepository(db)
        record = await repo.get(request.document_ids[0])
        if record:
            doc_name = record.original_filename
            doc_id_for_summary = record.id

    answer, sources, steps = run_agent(
        question=request.question,
        document_ids=request.document_ids,
        doc_id_for_summary=doc_id_for_summary,
        doc_name_for_summary=doc_name,
    )

    no_answer = (
        "could not find" in answer.lower()
        or "not enough information" in answer.lower()
        or "maximum iterations" in answer.lower()
    )

    return ChatResponse(
        answer=answer,
        sources=sources,
        agent_steps=steps,
        conversation_id=conversation_id,
        no_answer=no_answer,
    )


@router.post("/documents/compare", response_model=CompareResponse)
async def compare_documents(request: CompareRequest, db: AsyncSession = Depends(get_db)):
    repo = DocumentRepository(db)
    for doc_id in request.document_ids:
        record = await repo.get(doc_id)
        if not record:
            raise NotFoundError(f"Document {doc_id}")

    result = tool_compare_documents(request.document_ids, request.question)
    return CompareResponse(
        similarities=result.get("similarities", []),
        differences=result.get("differences", []),
        summary=result.get("summary", ""),
        sources=result.get("sources", []),
    )
