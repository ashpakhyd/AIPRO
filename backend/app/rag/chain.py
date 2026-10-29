"""
RAG question-answering pipeline with citation support.
"""
from typing import List, Optional, Tuple
from app.core.config import get_settings
from app.core.logging import logger
from app.ingestion.embeddings import embed_query
from app.ingestion.vector_store import query_chunks
from app.models.llm_provider import generate_text
from app.schemas.models import SourceChunk

settings = get_settings()

SYSTEM_PROMPT = """You are a helpful knowledge assistant. Answer questions using the provided document context.

Rules:
- Primarily use the provided context to answer.
- For greetings or general questions, respond naturally and helpfully.
- Never fabricate page numbers, document names, or citations.
- Be concise and accurate.
"""


def retrieve_chunks(
    question: str,
    top_k: int = None,
    document_ids: Optional[List[str]] = None,
) -> List[SourceChunk]:
    top_k = top_k or settings.rag_top_k
    query_emb = embed_query(question)
    results = query_chunks(query_emb, top_k=top_k, document_ids=document_ids)

    sources = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for text, meta, dist in zip(docs, metas, distances):
        score = 1.0 - dist  # cosine distance -> similarity
        if score < settings.rag_similarity_threshold:
            continue
        sources.append(
            SourceChunk(
                document_id=meta.get("document_id", ""),
                document_name=meta.get("document_name", "Unknown"),
                chunk_index=meta.get("chunk_index", 0),
                page_number=meta.get("page_number"),
                text=text,
                score=round(score, 4),
            )
        )

    return sources


def build_rag_prompt(question: str, sources: List[SourceChunk]) -> str:
    context_parts = []
    for i, src in enumerate(sources, 1):
        page_info = f" (Page {src.page_number})" if src.page_number else ""
        context_parts.append(
            f"[Source {i}: {src.document_name}{page_info}]\n{src.text}"
        )

    context = "\n\n---\n\n".join(context_parts)
    return f"""{SYSTEM_PROMPT}

Context from uploaded documents:
{context}

Question: {question}

Answer:"""


def answer_question(
    question: str,
    document_ids: Optional[List[str]] = None,
) -> Tuple[str, List[SourceChunk], bool]:
    """
    Returns (answer, sources, no_answer_flag).
    """
    sources = retrieve_chunks(question, document_ids=document_ids)

    if not sources:
        return (
            "I could not find sufficient information in the uploaded documents to answer this question.",
            [],
            True,
        )

    prompt = build_rag_prompt(question, sources)
    try:
        answer = generate_text(prompt)
        answer = answer.strip()
    except Exception as e:
        logger.error(f"LLM generation error: {e}")
        return f"The language model encountered an error: {str(e)}", sources, True

    no_answer = False

    return answer, sources, no_answer
