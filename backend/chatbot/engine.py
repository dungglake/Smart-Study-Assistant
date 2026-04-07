import re
from .models import MaterialChunk

OUT_OF_SCOPE_MESSAGE = (
    "Câu hỏi này nằm ngoài nội dung tài liệu hiện có. "
    "Mình chỉ hỗ trợ dựa trên tài liệu bạn đã tải lên."
)

def _tokenize(s: str):
    s = s.lower()
    return set(re.findall(r"[a-zA-Z0-9À-ỹ]+", s))

def retrieve_top_chunks(material_id: int, query: str, k: int = 4):
    q_tokens = _tokenize(query)
    chunks = MaterialChunk.objects.filter(material_id=material_id).only("id", "text")

    scored = []
    for c in chunks:
        t_tokens = _tokenize(c.text[:2000])
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

def is_out_of_scope(retrieved_chunks, min_score: int = 2):
    """
    Rule MVP:
    - không có chunk nào match -> ngoài phạm vi
    - score cao nhất < min_score -> ngoài phạm vi
    """
    if not retrieved_chunks:
        return True

    top_score = retrieved_chunks[0]["score"]
    return top_score < min_score

def generate_response(mode: str, user_message: str, retrieved_chunks):
    if is_out_of_scope(retrieved_chunks):
        if mode == "FLASHCARD":
            return {
                "items": [],
                "message": OUT_OF_SCOPE_MESSAGE
            }

        if mode == "QUIZ":
            return {
                "items": [],
                "message": OUT_OF_SCOPE_MESSAGE
            }

        if mode == "MINDMAP":
            return {
                "title": "Mindmap",
                "children": [],
                "message": OUT_OF_SCOPE_MESSAGE
            }

        return {
            "text": OUT_OF_SCOPE_MESSAGE,
            "citations": []
        }

    chunks = [item["chunk"] for item in retrieved_chunks]
    context = "\n\n".join([f"[chunk {c.id}] {c.text[:500]}" for c in chunks])

    if mode == "CHAT":
        text = (
            "Mình dựa trên tài liệu bạn upload và thấy các đoạn liên quan như sau.\n\n"
            f"{context}\n\n"
            "Bạn muốn mình giải thích sâu hơn phần nào?"
        )
        return {
            "text": text,
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