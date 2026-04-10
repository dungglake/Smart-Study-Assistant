import re
from typing import List
from pypdf import PdfReader
from docx import Document


def extract_text_from_file(path: str, file_type: str) -> str:
    file_type = (file_type or "").lower()

    if file_type in ["txt", "md"]:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    if file_type == "pdf":
        reader = PdfReader(path)
        parts = []
        for page in reader.pages:
            parts.append(page.extract_text() or "")
        return "\n".join(parts)

    if file_type == "docx":
        doc = Document(path)
        parts = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(parts)

    raise ValueError("Unsupported file type. Only pdf/txt/docx/md supported.")


def _is_heading(paragraph: str) -> bool:
    p = paragraph.strip()
    if not p or len(p) > 120:
        return False
    if p.endswith(":"):
        return True
    if re.match(r"^(chapter|section|part)\b", p, flags=re.IGNORECASE):
        return True
    if re.match(r"^\d+(\.\d+)*\s+", p):
        return True
    words = p.split()
    if 1 <= len(words) <= 10 and p == p.title():
        return True
    return False


def _normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def chunk_text(text: str, max_chars: int = 1200, overlap_chars: int = 180) -> List[str]:
    text = _normalize_whitespace(text)
    if not text:
        return []

    paragraphs = [p.strip() for p in re.split(r"\n\n+", text) if p.strip()]
    if not paragraphs:
        return [text[:max_chars]]

    chunks: List[str] = []
    buffer = ""
    last_heading = ""

    for p in paragraphs:
        if _is_heading(p):
            last_heading = p

        candidate = p if not buffer else f"{buffer}\n\n{p}"
        if len(candidate) <= max_chars:
            buffer = candidate
            continue

        if buffer:
            chunks.append(buffer.strip())

        tail = buffer[-overlap_chars:].strip() if buffer else ""
        prefix_parts = [part for part in [last_heading, tail] if part]
        prefix = "\n\n".join(prefix_parts).strip()

        if prefix and p not in prefix:
            buffer = f"{prefix}\n\n{p}"[: max_chars + overlap_chars]
        else:
            buffer = p

        while len(buffer) > max_chars:
            piece = buffer[:max_chars].rsplit(" ", 1)[0].strip() or buffer[:max_chars]
            chunks.append(piece)
            overlap = piece[-overlap_chars:].strip()
            buffer = f"{overlap} {buffer[len(piece):].strip()}".strip()

    if buffer:
        chunks.append(buffer.strip())

    deduped: List[str] = []
    seen = set()
    for chunk in chunks:
        norm = re.sub(r"\s+", " ", chunk).strip()
        if norm and norm not in seen:
            deduped.append(chunk)
            seen.add(norm)

    return deduped
