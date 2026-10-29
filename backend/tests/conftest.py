import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock, patch
from app.main import app
from app.database.db import engine, Base


@pytest.fixture(autouse=True)
async def setup_test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
def mock_llm():
    with patch("app.models.llm_provider.get_llm") as mock:
        llm = MagicMock()
        llm.invoke.return_value = "This is a test answer from the mocked LLM."
        mock.return_value = llm
        yield llm


@pytest.fixture
def mock_embeddings():
    with patch("app.ingestion.embeddings.get_embedding_model") as mock:
        model = MagicMock()
        import numpy as np
        model.encode.return_value = np.array([[0.1] * 384])
        mock.return_value = model
        yield model
