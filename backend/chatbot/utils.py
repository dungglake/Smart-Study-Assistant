from pypdf import PdfReader

def extract_text_from_file(path: str, file_type: str) -> str:
    file_type = (file_type or "").lower()
    if file_type == "txt":
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    if file_type == "pdf":
        reader = PdfReader(path)
        parts = []
        for page in reader.pages:
            parts.append(page.extract_text() or "")
        return "\n".join(parts)

    raise ValueError("Unsupported file type. Only pdf/txt supported.")

def chunk_text(text: str, max_chars: int = 1200):
    # chunk theo paragraph trước, rồi gom lại cho đủ max_chars
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    buff = ""

    for p in paras:
        if len(buff) + len(p) + 2 <= max_chars:
            buff = (buff + "\n\n" + p).strip()
        else:
            if buff:
                chunks.append(buff)
            buff = p

    if buff:
        chunks.append(buff)

    # fallback nếu tài liệu không có \n\n
    if not chunks and text.strip():
        for i in range(0, len(text), max_chars):
            chunks.append(text[i:i+max_chars])

    return chunks