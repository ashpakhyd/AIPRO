"""
Controlled agent orchestrator with bounded execution.
"""
from typing import List, Optional, Tuple
from app.core.config import get_settings
from app.core.logging import logger
from app.tools.agent_tools import (
    tool_document_search,
    tool_summarize_document,
    tool_compare_documents,
    tool_web_search,
)
from app.models.llm_provider import generate_text
from app.schemas.models import AgentStep, SourceChunk

settings = get_settings()


def _classify_intent(question: str, document_ids: Optional[List[str]]) -> str:
    """Simple keyword-based intent classification."""
    q = question.lower()
    if any(w in q for w in ["summarize", "summary", "overview", "brief", "outline"]):
        return "summarize"
    if any(w in q for w in ["compare", "difference", "similar", "contrast", "versus", "vs"]):
        return "compare"
    if any(w in q for w in ["search web", "latest", "current", "news", "internet", "online"]):
        return "web_search"
    return "document_search"


def run_agent(
    question: str,
    document_ids: Optional[List[str]] = None,
    doc_id_for_summary: Optional[str] = None,
    doc_name_for_summary: Optional[str] = None,
) -> Tuple[str, List[SourceChunk], List[AgentStep]]:
    """
    Run the controlled agent. Returns (answer, sources, steps).
    Max iterations enforced.
    """
    steps: List[AgentStep] = []
    all_sources: List[SourceChunk] = []
    iterations = 0
    max_iter = settings.agent_max_iterations

    intent = _classify_intent(question, document_ids)

    # --- Tool execution ---
    while iterations < max_iter:
        iterations += 1

        if intent == "summarize" and doc_id_for_summary:
            step_result = tool_summarize_document(doc_id_for_summary, doc_name_for_summary or "Document")
            error = step_result.get("error")
            steps.append(AgentStep(
                tool="document_summarizer",
                reason="User requested a document summary.",
                result_summary=step_result.get("summary", "")[:200] or error or "No summary generated.",
                sources_count=0,
                success=not bool(error),
            ))
            if error:
                return f"Summarization failed: {error}", [], steps
            summary = step_result.get("summary", "")
            key_points = step_result.get("key_points", [])
            answer = summary
            if key_points:
                answer += "\n\nKey Points:\n" + "\n".join(f"- {p}" for p in key_points)
            return answer, [], steps

        elif intent == "compare" and document_ids and len(document_ids) >= 2:
            step_result = tool_compare_documents(document_ids, question)
            sources = step_result.get("sources", [])
            all_sources.extend(sources)
            steps.append(AgentStep(
                tool="document_comparison",
                reason="User requested a comparison across documents.",
                result_summary=step_result.get("summary", "")[:200],
                sources_count=len(sources),
                success=True,
            ))
            sims = step_result.get("similarities", [])
            diffs = step_result.get("differences", [])
            summary = step_result.get("summary", "")
            answer = summary
            if sims:
                answer += "\n\nSimilarities:\n" + "\n".join(f"- {s}" for s in sims)
            if diffs:
                answer += "\n\nDifferences:\n" + "\n".join(f"- {d}" for d in diffs)
            return answer or "Could not generate comparison.", all_sources, steps

        elif intent == "web_search":
            step_result = tool_web_search(question)
            error = step_result.get("error")
            results = step_result.get("results", [])
            steps.append(AgentStep(
                tool="web_search",
                reason="Question appears to require external/current information.",
                result_summary=(results[0][:200] if results else error or "No results."),
                sources_count=len(results),
                success=not bool(error) and bool(results),
            ))
            if error or not results:
                # Fall back to document search
                intent = "document_search"
                continue

            context = "\n".join(results[:3])
            prompt = f"Answer the following question using the web search results below.\n\nResults:\n{context}\n\nQuestion: {question}\n\nAnswer:"
            try:
                answer = generate_text(prompt).strip()
            except Exception as e:
                answer = f"Web search succeeded but answer generation failed: {e}"
            return answer, [], steps

        else:  # document_search (default)
            step_result = tool_document_search(question, document_ids=document_ids)
            sources = step_result.get("sources", [])
            all_sources.extend(sources)
            steps.append(AgentStep(
                tool="document_search",
                reason="Searching indexed documents for relevant information.",
                result_summary=f"Found {len(sources)} relevant chunks.",
                sources_count=len(sources),
                success=True,
            ))

            if not sources:
                return (
                    "I could not find sufficient information in the uploaded documents to answer this question.",
                    [],
                    steps,
                )

            # Build answer from retrieved context
            from app.rag.chain import build_rag_prompt
            prompt = build_rag_prompt(question, sources)
            try:
                answer = generate_text(prompt).strip()
            except Exception as e:
                return f"Answer generation failed: {e}", sources, steps

            return answer, all_sources, steps

    return "Agent reached maximum iterations without a complete answer.", all_sources, steps
