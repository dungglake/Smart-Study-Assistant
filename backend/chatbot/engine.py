import re
from .models import MaterialChunk

def _tokenize(s: str):
    s = s.lower()
    return set(re.findall(r"[a-zA-Z0-9À-ỹ]+", s))

def retrieve_top_chunks(material_id: int, query: str, k: int = 4):
    q_tokens = _tokenize(query)
    chunks = MaterialChunk.objects.filter(material_id=material_id).only("id", "text")

    scored = []
    for c in chunks:
        t_tokens = _tokenize(c.text[:2000])
        score = len(q_tokens & t_tokens)
        if score > 0:
            scored.append((score, c))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [c for _, c in scored[:k]]
    return top

def generate_response(mode: str, user_message: str, chunks):
    # MVP chưa gọi AI thật: trả “template” dựa trên chunks
    # Sau này bạn chỉ thay phần này bằng LLM/local model.
    context = "\n\n".join([f"[chunk {c.id}] {c.text[:500]}" for c in chunks])

    if mode == "CHAT":
        text = (
            "Mình dựa trên tài liệu bạn upload và thấy các đoạn liên quan như sau.\n\n"
            f"{context}\n\n"
            "Bạn muốn mình giải thích sâu hơn phần nào?"
        )
        return {"text": text, "citations": [{"chunk_id": c.id} for c in chunks]}

    if mode == "FLASHCARD":
        # tạo flashcards mock dựa trên heading/ý chính (MVP)
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
        return {"items": [{"type": "mcq", "question": "MVP quiz placeholder", "choices": ["A","B","C","D"], "answer_index": 0}]}

    if mode == "MINDMAP":
        return {"title": "Mindmap (MVP)", "children": [{"title": f"Chunk {c.id}", "children": []} for c in chunks]}

    return {"text": "Unsupported mode"}