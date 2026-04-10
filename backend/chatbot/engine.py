import re
import math
from collections import OrderedDict

from .models import MaterialChunk
from .local_llm import generate_llm_answer

try:
    from .embedding import get_embedding
except Exception:
    get_embedding = None


OUT_OF_SCOPE_MESSAGE = (
    "This question is outside the scope of the available documentation. "
    "I can only help based on the documents you have uploaded."
)

SUMMARY_QUERIES = {
    "tom tat", "tóm tắt", "tom tat tai lieu", "tóm tắt tài liệu",
    "tai lieu noi gi", "tài liệu nói gì", "tai lieu do noi gi", "tài liệu đó nói gì",
    "noi dung chinh", "nội dung chính", "summary", "summarize", "overview",
    "introduce", "introduction", "document summary"
}

EXPLAIN_QUERIES = {
    "giai thich", "giải thích", "giai thich tai lieu", "giải thích tài liệu",
    "explain", "tai lieu dang noi gi", "tài liệu đang nói gì",
    "mo ta tai lieu", "mô tả tài liệu", "describe document"
}

FOLLOW_UP_EXPLAIN_QUERIES = {
    "noi sau hon", "nói sâu hơn", "giai thich ky hon", "giải thích kỹ hơn",
    "chi tiet hon", "chi tiết hơn", "noi ro hon", "nói rõ hơn",
    "mo rong hon", "mở rộng hơn", "phan do la gi", "phần đó là gì",
    "tai lieu do", "tài liệu đó", "ve tai lieu do", "về tài liệu đó"
}

KEYPOINT_QUERIES = {
    "liet ke y chinh", "liệt kê ý chính", "key points", "main points",
    "bullet points", "important points"
}

COMPARE_QUERIES = {
    "compare", "so sanh", "so sánh", "difference", "khac nhau", "khác nhau"
}

GENERIC_STOP_LINES = [
    "page ", "trang ", "copyright", "all rights reserved"
]

GENERIC_STOP_CONTAINS = [
    "@gmail.com", "@outlook.com", "@yahoo.com", "http://", "https://", "www."
]

TOPIC_HINTS = OrderedDict([
    ("topic", ["responsible use", "ethical", "legal", "big data", "data analytics"]),
    ("issues", ["bias", "fairness", "privacy", "security", "risk", "harm", "transparency"]),
    ("case_study", ["case study", "case 1", "case 2", "case 3", "case 4", "context"]),
    ("actions", ["task", "tasks", "identify", "track", "maintain", "audit", "explore"]),
    ("conclusion", ["conclusion", "takeaway", "recommendation", "future work"]),
])

DOMAIN_HINTS = OrderedDict([
    ("supervised", ["supervised learning", "classification", "regression", "ensemble", "random forest", "gradient boosting"]),
    ("unsupervised", ["unsupervised learning", "clustering", "dbscan", "hdbscan", "gmm", "gaussian mixture"]),
    ("dimensionality", ["dimensionality reduction", "pca", "t-sne", "tsne", "umap", "autoencoder"]),
    ("features", ["feature engineering", "feature selection", "feature importance"]),
    ("scale", ["scalability", "distributed", "parallel", "big data", "machine learning at scale"]),
])


def _normalize_text(s: str) -> str:
    s = (s or "").lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _tokenize(s: str):
    return re.findall(r"[a-zA-Z0-9À-ỹ]+", (s or "").lower())


def _contains_any(normalized: str, phrases: set[str]) -> bool:
    return normalized in phrases or any(p in normalized for p in phrases)


def _is_follow_up_document_query(normalized: str) -> bool:
    if _contains_any(normalized, FOLLOW_UP_EXPLAIN_QUERIES):
        return True

    tokens = set(_tokenize(normalized))
    hints = {
        "sau", "hon", "hơn", "ky", "kỹ", "chi", "tiet", "tiết",
        "ro", "rõ", "mo", "mở", "rong", "rộng", "tai", "lieu",
        "tài", "liệu", "do", "đó", "phan", "phần"
    }
    return len(tokens & hints) >= 2


def _query_type(user_message: str) -> str:
    q = _normalize_text(user_message)
    if _contains_any(q, SUMMARY_QUERIES):
        return "summary"
    if _contains_any(q, EXPLAIN_QUERIES):
        return "explain"
    if _contains_any(q, FOLLOW_UP_EXPLAIN_QUERIES):
        return "explain"
    if _contains_any(q, KEYPOINT_QUERIES):
        return "keypoints"
    if _contains_any(q, COMPARE_QUERIES):
        return "compare"
    return "qa"


def _looks_like_heading(line: str) -> bool:
    raw = line.strip()
    low = raw.lower()

    if len(raw) < 4 or len(raw) > 90:
        return False
    if raw.endswith(":"):
        return True
    if re.match(r"^(chapter|section|part)\b", low):
        return True
    if re.match(r"^\d+(\.\d+)*\s+", raw):
        return True

    words = raw.split()
    if len(words) <= 8 and not raw.endswith("."):
        alpha_ratio = sum(ch.isalpha() for ch in raw) / max(len(raw), 1)
        if alpha_ratio > 0.6:
            return True

    return False


def _compress_line(line: str) -> str:
    line = re.sub(r"\s+", " ", line).strip()
    line = line.replace(" .", ".").replace(" ,", ",").replace(" :", ":").replace(" ;", ";")
    line = line.replace(" ?", "?").replace(" !", "!")
    return line.strip(" -•")


def _normalize_inline_separators(line: str) -> str:
    line = _compress_line(line)
    line = line.replace("•", "\n- ")
    line = line.replace("·", "\n- ")
    line = re.sub(r"(?<=[\?\!\.:;,])(?=[A-Za-zÀ-ỹ])", " ", line)
    line = re.sub(r"(?<=[a-zà-ỹ])(?=[A-ZÀ-Ỹ])", " ", line)
    line = re.sub(r"\n\s*-\s*", "\n- ", line)
    line = re.sub(r"\n{3,}", "\n\n", line)
    line = re.sub(r"[ \t]+", " ", line)
    return line.strip()


def clean_chunk_text(text: str) -> str:
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    cleaned = []
    seen = set()

    for raw_line in lines:
        low = raw_line.lower().strip()

        if low in {"1", "2", "3", "4", "5"}:
            continue
        if any(low.startswith(prefix) for prefix in GENERIC_STOP_LINES):
            continue
        if any(bad in low for bad in GENERIC_STOP_CONTAINS):
            continue

        line = re.sub(r"\s+", " ", raw_line).strip()
        line = line.strip("•- ").strip()
        if len(line) < 8:
            continue

        normalized = _normalize_inline_separators(line)
        for part in normalized.splitlines():
            part = _compress_line(part).strip()
            part = re.sub(r"^\-\s*", "", part).strip()
            if len(part) < 8:
                continue
            if part not in seen:
                cleaned.append(part)
                seen.add(part)

    return "\n".join(cleaned)


def _cosine_similarity(a, b) -> float:
    if not a or not b:
        return 0.0
    if len(a) != len(b):
        return 0.0

    dot = sum(float(x) * float(y) for x, y in zip(a, b))
    norm_a = math.sqrt(sum(float(x) * float(x) for x in a))
    norm_b = math.sqrt(sum(float(y) * float(y) for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def _keyword_score(query: str, cleaned_text: str) -> float:
    q_tokens = set(_tokenize(query))
    if not q_tokens:
        return 0.0

    t_tokens = set(_tokenize(cleaned_text))
    overlap = q_tokens & t_tokens
    score = float(len(overlap))
    q_low = _normalize_text(query)
    low = cleaned_text.lower()

    if q_low and q_low in low:
        score += 4.0

    for keywords in DOMAIN_HINTS.values():
        for kw in keywords:
            if kw in q_low and kw in low:
                score += 3.0

    for keywords in TOPIC_HINTS.values():
        for kw in keywords:
            if kw in q_low and kw in low:
                score += 2.0

    return score


def retrieve_top_chunks(material_id: int, query: str, k: int = 4):
    chunks = MaterialChunk.objects.filter(material_id=material_id).only("id", "text", "embedding", "order")
    if not query.strip():
        return []

    query_embedding = None
    if get_embedding is not None:
        try:
            query_embedding = get_embedding(query[:800])
        except Exception:
            query_embedding = None

    scored = []
    for c in chunks:
        cleaned = clean_chunk_text((c.text or "")[:3000])
        if not cleaned:
            continue

        keyword_score = _keyword_score(query, cleaned)
        semantic_score = 0.0
        if query_embedding is not None and getattr(c, "embedding", None):
            semantic_score = _cosine_similarity(query_embedding, c.embedding)

        if query_embedding is not None:
            score = semantic_score * 10.0 + keyword_score * 0.35
        else:
            score = keyword_score

        if score > 0:
            scored.append({
                "chunk": c,
                "score": score,
                "semantic_score": semantic_score,
                "keyword_score": keyword_score,
            })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:k]


def is_out_of_scope(retrieved_chunks, min_score: float = 0.6):
    if not retrieved_chunks:
        return True
    return float(retrieved_chunks[0].get("score", 0)) < min_score


def suggest_title_and_summary(material):
    chunks = MaterialChunk.objects.filter(material_id=material.id).order_by("order")[:8]
    lines = []

    for chunk in chunks:
        cleaned = clean_chunk_text(chunk.text)
        for line in cleaned.splitlines():
            line = line.strip()
            if len(line) >= 10 and line not in lines:
                lines.append(line)

    if not lines:
        return material.title, ""

    title = material.title
    for line in lines:
        low = line.lower()
        if _looks_like_heading(line) or "machine learning" in low or "big data" in low:
            title = line[:255]
            break

    summary = "\n".join(lines[:4]).strip()
    return title[:255], summary[:900]


def _format_history(conversation_history) -> str:
    if not conversation_history:
        return ""
    parts = []
    for item in conversation_history[-6:]:
        role = item.get("role", "user")
        text = (item.get("text") or "").strip()
        if text:
            parts.append(f"{role}: {text}")
    return "\n".join(parts)


def _prepare_chunks_for_llm(retrieved_chunks):
    prepared = []
    for item in retrieved_chunks:
        chunk = item["chunk"]
        prepared.append({
            "chunk": chunk,
            "score": item.get("score", 0),
            "text": clean_chunk_text(chunk.text),
        })
    return prepared


def _generate_llm_chat(
    mode: str,
    user_message: str,
    retrieved_chunks,
    material_id=None,
    conversation_history=None,
):
    del mode, material_id  # reserved for future extension

    query_type = _query_type(user_message)
    normalized = _normalize_text(user_message)
    llm_chunks = _prepare_chunks_for_llm(retrieved_chunks)

    # Tạm thời giữ history để đồng bộ API; có thể ghép sâu hơn vào local_llm sau.
    _ = _format_history(conversation_history)

    if query_type == "summary":
        return {"text": generate_llm_answer(user_message, llm_chunks, query_type="summary"), "citations": []}
    if query_type == "explain":
        return {"text": generate_llm_answer(user_message, llm_chunks, query_type="explain"), "citations": []}
    if query_type == "keypoints":
        return {"text": generate_llm_answer(user_message, llm_chunks, query_type="keypoints"), "citations": []}
    if query_type == "compare":
        return {"text": generate_llm_answer(user_message, llm_chunks, query_type="compare"), "citations": []}
    if _is_follow_up_document_query(normalized):
        return {"text": generate_llm_answer(user_message, llm_chunks, query_type="explain"), "citations": []}

    return {"text": generate_llm_answer(user_message, llm_chunks, query_type="qa"), "citations": []}


def generate_response(
    mode: str,
    user_message: str,
    retrieved_chunks,
    material_id=None,
    conversation_history=None,
):
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
        content = _generate_llm_chat(
            mode,
            user_message,
            retrieved_chunks,
            material_id=material_id,
            conversation_history=conversation_history,
        )
        content["citations"] = [{"chunk_id": c.id} for c in chunks]
        return content

    if mode == "FLASHCARD":
        items = []
        for c in chunks[:3]:
            cleaned = clean_chunk_text(c.text)
            items.append({
                "front": "Ý chính của phần này là gì?",
                "back": cleaned[:220].strip(),
                "tags": ["mvp"],
                "chunk_id": c.id,
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
                        "Thông tin ngoài tài liệu",
                    ],
                    "answer_index": 0,
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
                "children": [],
            })

        return {
            "title": "Mindmap (MVP)",
            "children": cleaned_titles,
        }

    return {"text": "Unsupported mode"}
