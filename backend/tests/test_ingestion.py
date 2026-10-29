import pytest
import tempfile
import os
from app.ingestion.extractor import extract_text_from_txt, extract_text
from app.ingestion.chunker import chunk_pages
from app.core.errors import ValidationError
from app.ingestion.pipeline import validate_file


def test_extract_txt():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("Hello world. " * 100)
        path = f.name
    try:
        pages = extract_text_from_txt(path)
        assert len(pages) > 0
        assert all(isinstance(text, str) and isinstance(num, int) for text, num in pages)
    finally:
        os.unlink(path)


def test_extract_unsupported_type():
    with pytest.raises(ValueError, match="Unsupported"):
        extract_text("/fake/path.xyz", "xyz")


def test_chunk_pages_basic():
    pages = [("This is a test document with some content. " * 20, 1)]
    chunks = chunk_pages(pages, "doc123", "test.txt", chunk_size=100, chunk_overlap=20)
    assert len(chunks) > 1
    for chunk in chunks:
        assert "id" in chunk
        assert "text" in chunk
        assert chunk["metadata"]["document_id"] == "doc123"
        assert chunk["metadata"]["document_name"] == "test.txt"
        assert chunk["metadata"]["page_number"] == 1


def test_chunk_preserves_metadata():
    pages = [("Page one content.", 1), ("Page two content.", 2)]
    chunks = chunk_pages(pages, "docX", "file.txt")
    page_nums = {c["metadata"]["page_number"] for c in chunks}
    assert 1 in page_nums
    assert 2 in page_nums


def test_chunk_ids_unique():
    pages = [("Content " * 50, 1)]
    chunks = chunk_pages(pages, "doc1", "test.txt", chunk_size=50, chunk_overlap=10)
    ids = [c["id"] for c in chunks]
    assert len(ids) == len(set(ids))


def test_validate_file_valid():
    ext = validate_file("document.pdf", 1024)
    assert ext == "pdf"


def test_validate_file_invalid_type():
    with pytest.raises(ValidationError):
        validate_file("script.exe", 1024)


def test_validate_file_too_large():
    with pytest.raises(ValidationError, match="too large"):
        validate_file("big.pdf", 999 * 1024 * 1024)
