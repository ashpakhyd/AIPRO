import pytest
from unittest.mock import patch, MagicMock
import numpy as np


def test_embed_texts_returns_list(mock_embeddings):
    mock_embeddings.encode.return_value = np.array([[0.1] * 384, [0.2] * 384])
    from app.ingestion.embeddings import embed_texts
    result = embed_texts(["hello", "world"])
    assert isinstance(result, list)
    assert len(result) == 2
    assert len(result[0]) == 384


def test_embed_query_returns_single(mock_embeddings):
    mock_embeddings.encode.return_value = np.array([[0.5] * 384])
    from app.ingestion.embeddings import embed_query
    result = embed_query("test question")
    assert isinstance(result, list)
    assert len(result) == 384


def test_rag_answer_with_sources(mock_llm, mock_embeddings):
    mock_embeddings.encode.return_value = np.array([[0.1] * 384])

    mock_results = {
        "documents": [["Relevant document content about AI."]],
        "metadatas": [[{"document_id": "doc1", "document_name": "test.pdf", "chunk_index": 0, "page_number": 1}]],
        "distances": [[0.1]],
    }

    with patch("app.rag.chain.query_chunks", return_value=mock_results):
        with patch("app.rag.chain.generate_text", return_value="AI is a field of computer science."):
            from app.rag.chain import answer_question
            answer, sources, no_answer = answer_question("What is AI?")
            assert isinstance(answer, str)
            assert len(answer) > 0
            assert len(sources) > 0
            assert not no_answer


def test_rag_no_answer_when_no_sources(mock_embeddings):
    mock_embeddings.encode.return_value = np.array([[0.1] * 384])
    empty_results = {"documents": [[]], "metadatas": [[]], "distances": [[]]}

    with patch("app.rag.chain.query_chunks", return_value=empty_results):
        from app.rag.chain import answer_question
        answer, sources, no_answer = answer_question("Unknown question")
        assert no_answer
        assert sources == []


def test_rag_no_answer_below_threshold(mock_embeddings):
    mock_embeddings.encode.return_value = np.array([[0.1] * 384])
    # Distance of 0.95 means similarity of 0.05, below threshold
    low_score_results = {
        "documents": [["Some text"]],
        "metadatas": [[{"document_id": "d1", "document_name": "f.txt", "chunk_index": 0, "page_number": 1}]],
        "distances": [[0.95]],
    }

    with patch("app.rag.chain.query_chunks", return_value=low_score_results):
        from app.rag.chain import answer_question
        answer, sources, no_answer = answer_question("test")
        assert no_answer
        assert sources == []
