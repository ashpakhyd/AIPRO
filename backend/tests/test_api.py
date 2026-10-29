import pytest
from unittest.mock import patch


@pytest.mark.asyncio
async def test_health_endpoint(client):
    with patch("app.ingestion.vector_store.get_total_chunk_count", return_value=0):
        response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "llm_provider" in data


@pytest.mark.asyncio
async def test_list_documents_empty(client):
    response = await client.get("/api/documents")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["documents"] == []


@pytest.mark.asyncio
async def test_upload_invalid_file_type(client):
    response = await client.post(
        "/api/documents/upload",
        files={"file": ("malware.exe", b"binary content", "application/octet-stream")},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_upload_oversized_file(client):
    big_content = b"x" * (60 * 1024 * 1024)  # 60MB > 50MB limit
    response = await client.post(
        "/api/documents/upload",
        files={"file": ("big.txt", big_content, "text/plain")},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_nonexistent_document(client):
    response = await client.get("/api/documents/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_document(client):
    response = await client.delete("/api/documents/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_upload_txt_document(client, mock_embeddings):
    import numpy as np
    mock_embeddings.encode.return_value = np.array([[0.1] * 384] * 5)

    with patch("app.ingestion.vector_store.add_chunks"):
        content = b"This is a test document. " * 50
        response = await client.post(
            "/api/documents/upload",
            files={"file": ("test.txt", content, "text/plain")},
        )
    assert response.status_code == 200
    data = response.json()
    assert "document_id" in data
    assert data["status"] in ("indexed", "failed")


@pytest.mark.asyncio
async def test_agent_tools_endpoint(client):
    response = await client.get("/api/agent/tools")
    assert response.status_code == 200
    tools = response.json()
    assert isinstance(tools, list)
    tool_names = [t["name"] for t in tools]
    assert "document_search" in tool_names
    assert "document_summarizer" in tool_names


@pytest.mark.asyncio
async def test_chat_no_documents(client, mock_embeddings):
    import numpy as np
    mock_embeddings.encode.return_value = np.array([[0.1] * 384])

    empty_results = {"documents": [[]], "metadatas": [[]], "distances": [[]]}
    with patch("app.tools.agent_tools.query_chunks", return_value=empty_results):
        response = await client.post(
            "/api/chat",
            json={"question": "What is the meaning of life?", "use_agent": True},
        )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert data["no_answer"] is True
