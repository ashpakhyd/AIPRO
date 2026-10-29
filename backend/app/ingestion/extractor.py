from pathlib import Path
from typing import List, Tuple
import re


def extract_text_from_pdf(file_path: str) -> List[Tuple[str, int]]:
    """Returns list of (text, page_number) tuples."""
    from pypdf import PdfReader

    reader = PdfReader(file_path)
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = text.strip()
        if text:
            pages.append((text, i))
    return pages


def extract_text_from_docx(file_path: str) -> List[Tuple[str, int]]:
    """Returns list of (text, section_number) tuples (paragraphs grouped)."""
    from docx import Document

    doc = Document(file_path)
    sections = []
    current_section = []
    section_num = 1

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        current_section.append(text)
        # Group ~10 paragraphs per section
        if len(current_section) >= 10:
            sections.append(("\n".join(current_section), section_num))
            current_section = []
            section_num += 1

    if current_section:
        sections.append(("\n".join(current_section), section_num))

    return sections


def extract_text_from_txt(file_path: str) -> List[Tuple[str, int]]:
    """Returns list of (text, section_number) tuples."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # Split into ~500-char sections
    lines = content.splitlines()
    sections = []
    current = []
    section_num = 1
    char_count = 0

    for line in lines:
        current.append(line)
        char_count += len(line)
        if char_count >= 500:
            sections.append(("\n".join(current), section_num))
            current = []
            section_num += 1
            char_count = 0

    if current:
        sections.append(("\n".join(current), section_num))

    return sections


def extract_text(file_path: str, file_type: str) -> List[Tuple[str, int]]:
    """Dispatch to the correct extractor. Returns (text, page/section) pairs."""
    ext = file_type.lower().lstrip(".")
    if ext == "pdf":
        return extract_text_from_pdf(file_path)
    elif ext in ("docx", "doc"):
        return extract_text_from_docx(file_path)
    elif ext == "txt":
        return extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
