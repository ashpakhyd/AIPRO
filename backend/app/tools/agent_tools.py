from typing import List, Optional, Dict, Any
from app.core.config import get_settings
from app.core.logging import logger
from app.ingestion.embeddings import embed_query
from app.ingestion.vector_store import query_chunks
from app.models.llm_provider import generate_text
from app.schemas.models import SourceChunk

settings = get_settings()


def tool_document_search(
    question: str,
    document_ids: Optional[List[str]] = None,
    top_k: int = None,
) -> Dict[str, Any]:
    top_k = top_k or settings.rag_top_k
    query_emb = embed_query(question)
    results = query_chunks(query_emb, top_k=top_k, document_ids=document_ids)

    sources = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

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

    return {"sources": sources, "count": len(sources)}


def tool_summarize_document(document_id: str, document_name: str) -> Dict[str, Any]:
    from app.ingestion.vector_store import get_collection

    collection = get_collection()
    results = collection.get(
        where={"document_id": document_id},
        include=["documents", "metadatas"],
    )

    texts = results.get("documents", [])
    if not texts:
        return {"summary": "", "key_points": [], "error": "No content found for this document."}

    combined = "\n\n".join(texts)[:3000]
    prompt = (
        f"Summarize the following document concisely.\n"
        f"Provide a 2-3 sentence overview, then 3-5 key points as a numbered list.\n\n"
        f"Document: {document_name}\n\nContent:\n{combined}\n\nSummary:"
    )

    try:
        raw = generate_text(prompt)
        lines = [ln.strip() for ln in raw.strip().splitlines() if ln.strip()]
        key_points = [
            ln.lstrip("-*0123456789. ")
            for ln in lines
            if ln.startswith(("-", "*")) or (len(ln) > 2 and ln[0].isdigit() and ln[1] in ".)")
        ]
        summary_lines = [ln for ln in lines if ln not in key_points]
        summary = " ".join(summary_lines[:3])
        return {"summary": summary or raw.strip(), "key_points": key_points[:5]}
    except Exception as e:
        return {"summary": "", "key_points": [], "error": str(e)}


def tool_compare_documents(
    document_ids: List[str],
    question: Optional[str] = None,
) -> Dict[str, Any]:
    query = question or "What are the main topics and key information in this document?"
    all_sources: List[SourceChunk] = []

    for doc_id in document_ids:
        result = tool_document_search(query, document_ids=[doc_id], top_k=3)
        all_sources.extend(result["sources"])

    if not all_sources:
        return {"similarities": [], "differences": [], "summary": "No content found.", "sources": []}

    context = "\n\n".join(
        f"[{src.document_name}{f' (Page {src.page_number})' if src.page_number else ''}]: {src.text}"
        for src in all_sources
    )
    prompt = (
        f"Compare the following document excerpts.\n"
        f"List similarities, differences, and a brief summary.\n\n"
        f"Documents:\n{context}\n\nComparison:"
    )

    try:
        raw = generate_text(prompt)
        lines = [ln.strip() for ln in raw.strip().splitlines() if ln.strip()]
        similarities, differences, summary_lines = [], [], []
        mode = "summary"
        for line in lines:
            ll = line.lower()
            if "similarit" in ll:
                mode = "sim"
            elif "differenc" in ll:
                mode = "diff"
            elif "summary" in ll or "overall" in ll:
                mode = "summary"
            elif line.startswith(("-", "*")):
                item = line.lstrip("-* ")
                if mode == "sim":
                    similarities.append(item)
                elif mode == "diff":
                    differences.append(item)
                else:
                    summary_lines.append(item)
            else:
                summary_lines.append(line)

        return {
            "similarities": similarities[:5],
            "differences": differences[:5],
            "summary": " ".join(summary_lines[:3]) or raw[:300],
            "sources": all_sources,
        }
    except Exception as e:
        return {"similarities": [], "differences": [], "summary": str(e), "sources": all_sources}


def tool_web_search(query: str) -> Dict[str, Any]:
    if not settings.web_search_enabled or not settings.serpapi_key:
        return {
            "results": [],
            "error": "Web search is not configured. Set SERPAPI_KEY and WEB_SEARCH_ENABLED=true.",
        }
    try:
        from langchain_community.utilities import SerpAPIWrapper
        search = SerpAPIWrapper(serpapi_api_key=settings.serpapi_key)
        result = search.run(query)
        return {"results": [result], "error": None}
    except Exception as e:
        return {"results": [], "error": str(e)}
