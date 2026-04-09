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
        "noi", "dung", "nội", "summary", "summarize", "overview", "introduce"
    }
    return len(tokens & summary_hints) >= 1

def suggest_title_and_summary(material):
    chunks = MaterialChunk.objects.filter(material=material).order_by("order")[:5]
    full_text = "\n".join([c.text for c in chunks]).strip()

    if not full_text:
        return material.title, ""

    words = [w for w in _tokenize(full_text) if len(w) > 2 and w not in STOPWORDS]
    common = [w for w, _ in Counter(words).most_common(6)]

    if common:
        title = " ".join(common[:5]).title()
    else:
        title = material.title

    summary = full_text[:900].strip()
    return title[:255], summary

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

def generate_response(mode: str, user_message: str, retrieved_chunks):
    if is_document_summary_query(user_message):
        chunks = MaterialChunk.objects.all()[:4]
        text = "\n\n".join([c.text[:400] for c in chunks])
        if mode == "CHAT":
            return {
                "text": f"Tài liệu này nói về:\n\n{text}",
                "citations": [{"chunk_id": c.id} for c in chunks]
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
    context = "\n\n".join([f"[chunk {c.id}] {c.text[:500]}" for c in chunks])

    if mode == "CHAT":
        return {
            "text": (
                "Mình dựa trên tài liệu bạn upload và thấy các đoạn liên quan như sau.\n\n"
                f"{context}\n\n"
                "Bạn muốn mình giải thích sâu hơn phần nào?"
            ),
            "citations": [{"chunk_id": c.id} for c in chunks]
        }

    if mode == "FLASHCARD":
        items = []
        for c in chunks[:3]:
            items.append({
                "front": f"Tóm tắt ý chính của chunk {c.id} là gì?",
                "back": c.text[:220].strip(),
                "tags": ["mvp"],
                "chunk_id": c.id
            })
        return {"items": items}

    if mode == "QUIZ":
        return {
            "items": [
                {
                    "type": "mcq",
                    "question": "Nội dung chính của tài liệu trong phần liên quan là gì?",
                    "choices": ["Ý A", "Ý B", "Ý C", "Ý D"],
                    "answer_index": 0
                }
            ]
        }

    if mode == "MINDMAP":
        return {
            "title": "Mindmap (MVP)",
            "children": [{"title": f"Chunk {c.id}", "children": []} for c in chunks]
        }

    return {"text": "Unsupported mode"}