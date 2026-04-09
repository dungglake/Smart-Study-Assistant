import re
from collections import Counter
from .models import MaterialChunk

OUT_OF_SCOPE_MESSAGE = (
    "This question is outside the scope of the available documentation. "
    "I can only help based on the documents you have uploaded."
)

STOPWORDS = {
    "và", "là", "của", "cho", "trong", "một", "những", "các", "với", "được",
    "the", "and", "for", "that", "this", "from", "into", "how", "what", "when",
    "pdf", "docx", "txt", "md"
}

DOCUMENT_SUMMARY_QUERIES = {
    "tom tat", "tóm tắt", "tom tat tai lieu", "tóm tắt tài liệu",
    "tai lieu noi gi", "tài liệu nói gì", "noi dung chinh", "nội dung chính",
    "summary", "summarize", "summarize document", "document summary",
    "overview", "introduce", "introduction"
}


def _normalize_text(s: str):
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _tokenize(s: str):
    s = s.lower()
    return re.findall(r"[a-zA-Z0-9À-ỹ]+", s)


def is_document_summary_query(user_message: str) -> bool:
    normalized = _normalize_text(user_message)
    if normalized in DOCUMENT_SUMMARY_QUERIES:
        return True

    tokens = set(_tokenize(normalized))
    summary_hints = {
        "tom", "tat", "tóm", "tắt", "tai", "lieu", "tài", "liệu",
        "noi", "dung", "nội", "summary", "summarize", "overview",
        "introduce", "introduction"
    }
    return len(tokens & summary_hints) >= 1


def clean_chunk_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    filtered = []
    seen = set()

    for line in lines:
        lower = line.lower()

        if lower in {"1", "2", "3", "4", "5"}:
            continue

        if "international university" in lower and len(lower) < 80:
            continue
        if "assoc. prof." in lower and len(lower) < 80:
            continue
        if "vnu-hcmc" in lower and len(lower) < 80:
            continue
        if "school of computer science and engineering" in lower:
            continue

        if line not in seen:
            filtered.append(line)
            seen.add(line)

    return "\n".join(filtered)


def suggest_title_and_summary(material):
    chunks = MaterialChunk.objects.filter(material=material).order_by("order")[:6]
    cleaned_parts = [clean_chunk_text(c.text) for c in chunks]
    full_text = "\n".join([p for p in cleaned_parts if p]).strip()

    if not full_text:
        return material.title, ""

    words = [w for w in _tokenize(full_text) if len(w) > 2 and w not in STOPWORDS]
    common = [w for w, _ in Counter(words).most_common(6)]

    title = " ".join(common[:5]).title() if common else material.title

    summary_lines = []
    for part in cleaned_parts:
        for line in part.splitlines():
            if len(line) > 20 and line not in summary_lines:
                summary_lines.append(line)
            if len(summary_lines) >= 6:
                break
        if len(summary_lines) >= 6:
            break

    summary = "\n".join(summary_lines[:6]).strip()
    return title[:255], summary[:900]


def retrieve_top_chunks(material_id: int, query: str, k: int = 4):
    q_tokens = set(_tokenize(query))
    chunks = MaterialChunk.objects.filter(material_id=material_id).only("id", "text")

    if not q_tokens:
        return []

    scored = []
    for c in chunks:
        t_tokens = set(_tokenize(c.text[:2000]))
        overlap = q_tokens & t_tokens
        score = len(overlap)
        if score > 0:
            scored.append({
                "chunk": c,
                "score": score,
                "overlap_tokens": list(overlap)
            })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:k]


def is_out_of_scope(retrieved_chunks, min_score: int = 1):
    if not retrieved_chunks:
        return True
    top_score = retrieved_chunks[0]["score"]
    return top_score < min_score


def build_summary_answer(material_id: int) -> str:
    chunks = MaterialChunk.objects.filter(material_id=material_id).order_by("order")[:8]
    cleaned_parts = [clean_chunk_text(c.text) for c in chunks]

    collected = []
    for part in cleaned_parts:
        for line in part.splitlines():
            if len(line) > 25 and line not in collected:
                collected.append(line)
            if len(collected) >= 6:
                break
        if len(collected) >= 6:
            break

    if not collected:
        return "Tài liệu này chủ yếu trình bày nội dung tổng quan của bài giảng."

    return "Tài liệu này chủ yếu nói về:\n\n- " + "\n- ".join(collected[:6])


def build_grounded_chat_answer(retrieved_chunks) -> str:
    chunks = [item["chunk"] for item in retrieved_chunks]
    cleaned = [clean_chunk_text(c.text) for c in chunks]
    merged_lines = []

    for part in cleaned:
        for line in part.splitlines():
            if len(line) > 20 and line not in merged_lines:
                merged_lines.append(line)
            if len(merged_lines) >= 8:
                break
        if len(merged_lines) >= 8:
            break

    if not merged_lines:
        return (
            "Mình có tìm thấy phần liên quan trong tài liệu, "
            "nhưng nội dung trích xuất chưa đủ rõ để tóm tắt tốt hơn."
        )

    return (
        "Mình tìm được nội dung liên quan trong tài liệu:\n\n- "
        + "\n- ".join(merged_lines[:8])
        + "\n\nBạn muốn mình giải thích ngắn gọn hơn, dịch sang tiếng Việt, "
          "hay tóm tắt theo bullet?"
    )


def generate_response(mode: str, user_message: str, retrieved_chunks, material_id=None):
    if mode == "CHAT" and material_id and is_document_summary_query(user_message):
        summary_text = build_summary_answer(material_id)
        return {
            "text": summary_text,
            "citations": []
        }

    if is_out_of_scope(retrieved_chunks):
        if mode == "FLASHCARD":
            return {"items": [], "message": OUT_OF_SCOPE_MESSAGE}

        if mode == "QUIZ":
            return {"items": [], "message": OUT_OF_SCOPE_MESSAGE}

        if mode == "MINDMAP":
            return {"title": "Mindmap", "children": [], "message": OUT_OF_SCOPE_MESSAGE}

        return {"text": OUT_OF_SCOPE_MESSAGE, "citations": []}

    chunks = [item["chunk"] for item in retrieved_chunks]

    if mode == "CHAT":
        return {
            "text": build_grounded_chat_answer(retrieved_chunks),
            "citations": [{"chunk_id": c.id} for c in chunks]
        }

    if mode == "FLASHCARD":
        items = []
        for c in chunks[:3]:
            cleaned = clean_chunk_text(c.text)
            items.append({
                "front": "Ý chính của phần này là gì?",
                "back": cleaned[:220].strip(),
                "tags": ["mvp"],
                "chunk_id": c.id
            })
        return {"items": items}

    if mode == "QUIZ":
        return {
            "items": [
                {
                    "type": "mcq",
                    "question": "Nội dung chính của phần liên quan trong tài liệu là gì?",
                    "choices": [
                        "Khái niệm và mục tiêu chính",
                        "Mã nguồn hệ thống",
                        "Hướng dẫn cài đặt IDE",
                        "Thông tin ngoài tài liệu"
                    ],
                    "answer_index": 0
                }
            ]
        }

    if mode == "MINDMAP":
        cleaned_titles = []
        for c in chunks:
            cleaned = clean_chunk_text(c.text)
            first_line = cleaned.splitlines()[0] if cleaned else f"Chunk {c.id}"
            cleaned_titles.append({
                "title": first_line[:80],
                "children": []
            })

        return {
            "title": "Mindmap (MVP)",
            "children": cleaned_titles
        }

    return {"text": "Unsupported mode"}