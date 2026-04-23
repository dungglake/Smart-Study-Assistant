import re
import math
from collections import OrderedDict

from .models import MaterialChunk, ConversationMemory
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

OVERVIEW_QUERIES = {
    "summary this file", "summarize this file", "document summary", "overview",
    "main topic", "main idea", "what is this file about", "what is this document about",
    "file này nói về gì", "tài liệu này nói về gì", "chu de chinh", "chủ đề chính",
    "noi dung chinh", "nội dung chính", "ý chính", "y chinh", "key points",
    "main points", "tóm tắt", "tom tat"
}

FACTUAL_PREFIXES = (
    "how many", "what are", "which", "list", "name", "give me", "show me",
    "bao nhieu", "có bao nhiêu", "liet ke", "liệt kê", "kể tên"
)

FOLLOW_UP_REFERENCES = {
    "that", "that part", "that section", "the above", "above", "it", "this part",
    "this section", "those points", "the point above", "the previous part",
    "phần đó", "phần trên", "ý trên", "cái đó", "nội dung đó", "đoạn đó", "mục đó",
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

    if any(ref in normalized for ref in FOLLOW_UP_REFERENCES):
        return True

    tokens = set(_tokenize(normalized))
    hints = {
        "sau", "hon", "hơn", "ky", "kỹ", "chi", "tiet", "tiết",
        "ro", "rõ", "mo", "mở", "rong", "rộng", "tai", "lieu",
        "tài", "liệu", "do", "đó", "phan", "phần", "tren", "trên"
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


def detect_overview_query(user_message: str) -> bool:
    q = _normalize_text(user_message)
    if _contains_any(q, OVERVIEW_QUERIES):
        return True

    broad_patterns = [
        "this file", "this document", "the uploaded document",
        "tai lieu nay", "tài liệu này", "file nay", "file này",
    ]
    return any(p in q for p in broad_patterns) and _query_type(user_message) in {
        "summary", "explain", "keypoints"
    }


def detect_factual_query(user_message: str) -> bool:
    q = _normalize_text(user_message)
    return q.startswith(FACTUAL_PREFIXES)


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


def _heading_bonus(chunk_text: str) -> float:
    lines = [ln.strip() for ln in (chunk_text or "").splitlines() if ln.strip()]
    if not lines:
        return 0.0

    first = lines[0]
    if _looks_like_heading(first):
        return 1.5
    if len(lines) >= 2 and _looks_like_heading(lines[1]):
        return 1.0
    return 0.0


def _prepare_chunk_record(chunk, score: float, semantic_score: float = 0.0, keyword_score: float = 0.0):
    return {
        "chunk": chunk,
        "score": float(score),
        "semantic_score": float(semantic_score),
        "keyword_score": float(keyword_score),
    }
    
def _query_needs_multi_hop(user_message: str, conversation_history=None) -> bool:
    q = _normalize_text(user_message)
    qtype = _query_type(user_message)

    if detect_overview_query(user_message):
        return False
    if qtype == "compare":
        return True
    if qtype in {"summary", "explain", "keypoints"}:
        return True
    if _is_follow_up_document_query(q):
        return True

    markers = [
        "why", "how", "relationship", "impact", "cause", "effect",
        "vì sao", "tại sao", "liên hệ", "ảnh hưởng", "tác động", "so sánh"
    ]
    return any(m in q for m in markers)

def _finalize_ranked_results(query: str, candidates, top_n: int):
    if not candidates:
        return []

    unique = []
    seen_ids = set()

    for item in candidates:
        cid = item["chunk"].id
        if cid in seen_ids:
            continue
        unique.append(item)
        seen_ids.add(cid)

    reranked = rerank_chunks(query, unique, top_n=max(len(unique), top_n))
    return reranked[:top_n]

def retrieve_document_overview_chunks(material_id: int, limit: int = 6):
    chunks = MaterialChunk.objects.filter(material_id=material_id).only("id", "text", "order").order_by("order")[:limit]
    return [_prepare_chunk_record(c, score=999.0) for c in chunks]

def retrieve_balanced_overview_chunks(material_id: int, limit: int = 18):
    chunks = list(
        MaterialChunk.objects.filter(material_id=material_id)
        .only("id", "text", "order")
        .order_by("order")
    )
    if not chunks:
        return []

    if len(chunks) <= limit:
        return [_prepare_chunk_record(c, score=999.0) for c in chunks]

    selected = []
    seen_ids = set()

    def add_chunk(chunk):
        if chunk.id in seen_ids:
            return
        selected.append(_prepare_chunk_record(chunk, score=999.0))
        seen_ids.add(chunk.id)

    head_count = 4
    for c in chunks[:head_count]:
        add_chunk(c)

    tail_count = 4
    for c in chunks[-tail_count:]:
        add_chunk(c)

    remaining_slots = max(0, limit - len(selected))
    if remaining_slots > 0:
        middle = chunks[head_count: len(chunks) - tail_count if tail_count > 0 else len(chunks)]
        if middle:
            for i in range(remaining_slots):
                idx = int(i * len(middle) / max(remaining_slots, 1))
                idx = min(idx, len(middle) - 1)
                add_chunk(middle[idx])

    selected.sort(key=lambda x: getattr(x["chunk"], "order", 10**9))
    return selected[:limit]

def _extract_reference_focus(conversation_history) -> str:
    """
    Try to recover the topic of a follow-up question from recent conversation.
    Priority:
    1. previous user question
    2. previous assistant heading
    3. first assistant bullet
    """
    if not conversation_history:
        return ""

    previous_user = ""
    previous_assistant = ""

    for item in reversed(conversation_history):
        role = item.get("role")
        text = (item.get("text") or "").strip()
        if not text:
            continue
        if role == "user" and not previous_user:
            previous_user = text
        elif role == "assistant" and not previous_assistant:
            previous_assistant = text
        if previous_user and previous_assistant:
            break

    if previous_user:
        normalized_prev = _normalize_text(previous_user)
        if not _is_follow_up_document_query(normalized_prev):
            return previous_user

    if previous_assistant:
        for line in previous_assistant.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("## ") or line.startswith("### "):
                return re.sub(r"^#{2,3}\s*", "", line).strip(" :")
        for line in previous_assistant.splitlines():
            line = line.strip()
            if line.startswith("- "):
                return line[2:].strip()

    return previous_user or ""


def rewrite_user_query(user_message: str, conversation_history=None) -> str:
    """
    Deterministic query rewriting:
    - keep broad overview queries as-is
    - rewrite follow-up references using recent conversation
    - preserve direct factual queries
    """
    user_message = (user_message or "").strip()
    if not user_message:
        return ""

    normalized = _normalize_text(user_message)

    if detect_overview_query(user_message):
        return user_message

    if detect_factual_query(user_message) and not _is_follow_up_document_query(normalized):
        return user_message

    if not _is_follow_up_document_query(normalized):
        return user_message

    focus = _extract_reference_focus(conversation_history)
    if not focus:
        return user_message

    if _query_type(user_message) == "compare":
        return f"Compare this follow-up topic with the previous referenced topic: {focus}. User request: {user_message}"

    if detect_factual_query(user_message):
        return f"Answer this factual question about the previously referenced topic '{focus}': {user_message}"

    return f"About the topic '{focus}', {user_message}"


def retrieve_top_chunks(material_id: int, query: str, k: int = 4):
    if detect_overview_query(query):
        return retrieve_document_overview_chunks(material_id, limit=max(6, k))

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
        raw_text = (c.text or "")[:3000]
        cleaned = clean_chunk_text(raw_text)
        if not cleaned:
            continue

        keyword_score = _keyword_score(query, cleaned)
        semantic_score = 0.0
        if query_embedding is not None and getattr(c, "embedding", None):
            semantic_score = _cosine_similarity(query_embedding, c.embedding)

        heading_bonus = _heading_bonus(raw_text)
        density_penalty = -0.2 if len(cleaned) > 2200 else 0.0

        if query_embedding is not None:
            score = semantic_score * 10.0 + keyword_score * 0.35 + heading_bonus + density_penalty
        else:
            score = keyword_score + heading_bonus + density_penalty

        if score > 0:
            scored.append(_prepare_chunk_record(
                c,
                score=score,
                semantic_score=semantic_score,
                keyword_score=keyword_score,
            ))

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:k]


def expand_with_neighbor_chunks(material_id: int, retrieved_chunks, window: int = 1, limit: int = 8):
    if not retrieved_chunks:
        return []

    base_by_id = {item["chunk"].id: item for item in retrieved_chunks}
    expanded_orders = set()

    for item in retrieved_chunks:
        chunk = item["chunk"]
        order = getattr(chunk, "order", None)
        if order is None:
            continue
        for offset in range(-window, window + 1):
            if order + offset > 0:
                expanded_orders.add(order + offset)

    neighbors = MaterialChunk.objects.filter(
        material_id=material_id,
        order__in=expanded_orders,
    ).only("id", "text", "embedding", "order").order_by("order")

    results = []
    seen_ids = set()

    for chunk in neighbors:
        if chunk.id in seen_ids:
            continue
        if chunk.id in base_by_id:
            results.append(base_by_id[chunk.id])
        else:
            results.append(_prepare_chunk_record(chunk, score=0.75))
        seen_ids.add(chunk.id)

    results.sort(key=lambda x: (getattr(x["chunk"], "order", 10**9), -x["score"]))
    return results[:limit]

def retrieve_for_chat(material_id: int, query: str, k: int = 4, conversation_history=None):
    rewritten_query = rewrite_user_query(query, conversation_history=conversation_history)

    if detect_overview_query(rewritten_query):
        first_chunks = retrieve_document_overview_chunks(material_id, limit=4)
        last_chunks = MaterialChunk.objects.filter(material_id=material_id)\
            .order_by("-order")[:4]

        last_chunks = [
            _prepare_chunk_record(c, score=999.0)
            for c in reversed(last_chunks)
        ]

        return first_chunks + last_chunks

    recall_k = max(k * 3, 12)
    primary = retrieve_top_chunks(material_id, rewritten_query, k=recall_k)
    if not primary:
        return []

    primary = _finalize_ranked_results(rewritten_query, primary, top_n=max(6, k))

    expanded = expand_with_neighbor_chunks(
        material_id,
        primary,
        window=1,
        limit=max(8, k + 4),
    )

    final_candidates = expanded if expanded else primary
    final_ranked = _finalize_ranked_results(
        rewritten_query,
        final_candidates,
        top_n=max(6, k),
    )
    return final_ranked

def is_out_of_scope(retrieved_chunks, min_score: float = 0.6):
    if not retrieved_chunks:
        return True

    top = retrieved_chunks[0]
    rerank_score = float(top.get("rerank_score", 0.0))
    base_score = float(top.get("score", 0.0))

    if rerank_score > 0:
        return rerank_score < 1.2

    return base_score < min_score


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


def _prepare_chunks_for_llm(retrieved_chunks):
    prepared = []
    seen_ids = set()

    for item in retrieved_chunks:
        chunk = item["chunk"]
        if chunk.id in seen_ids:
            continue
        prepared.append({
            "chunk": chunk,
            "score": item.get("score", 0),
            "text": clean_chunk_text(chunk.text),
        })
        seen_ids.add(chunk.id)

    return prepared


def resolve_follow_up_for_llm(user_message: str, conversation_history=None) -> str:
    """
    Make the user question more explicit for answer generation as well.
    """
    rewritten = rewrite_user_query(user_message, conversation_history=conversation_history)
    if rewritten == user_message:
        return user_message

    return f"Original user request: {user_message}\nResolved request: {rewritten}"


def _generate_llm_chat(
    mode: str,
    user_message: str,
    retrieved_chunks,
    material_id=None,
    conversation_history=None,
):
    del mode, material_id  # reserved for future extension

    query_type = _query_type(user_message)
    llm_chunks = _prepare_chunks_for_llm(retrieved_chunks)
    effective_question = resolve_follow_up_for_llm(user_message, conversation_history=conversation_history)

    if detect_factual_query(user_message):
        return {
            "text": generate_llm_answer(
                effective_question,
                llm_chunks,
                query_type="qa",
                conversation_history=None,
            ),
            "citations": [],
        }

    if query_type == "summary":
        return {"text": generate_llm_answer(effective_question, llm_chunks, query_type="summary", conversation_history=conversation_history), "citations": []}
    if query_type == "explain":
        return {"text": generate_llm_answer(effective_question, llm_chunks, query_type="explain", conversation_history=conversation_history), "citations": []}
    if query_type == "keypoints":
        return {"text": generate_llm_answer(effective_question, llm_chunks, query_type="keypoints", conversation_history=conversation_history), "citations": []}
    if query_type == "compare":
        return {"text": generate_llm_answer(effective_question, llm_chunks, query_type="compare", conversation_history=conversation_history), "citations": []}
    if _is_follow_up_document_query(_normalize_text(user_message)):
        return {"text": generate_llm_answer(effective_question, llm_chunks, query_type="explain", conversation_history=conversation_history), "citations": []}

    return {"text": generate_llm_answer(effective_question, llm_chunks, query_type="qa", conversation_history=conversation_history), "citations": []}


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
        content["citations"] = [{"chunk_id": c.id, "order": getattr(c, "order", None)} for c in chunks]
        return content

    if mode == "FLASHCARD":
        llm_chunks = _prepare_chunks_for_llm(retrieved_chunks)

        prompt = """
    Create 4 flashcards from the document.

    Rules:
    - Each flashcard must include:
    - front: a short study question
    - back: a short answer based only on the document
    - Keep each answer concise
    - Avoid duplicate ideas
    - Use simple, study-friendly wording

    Format exactly:
    Q: ...
    A: ...

    Q: ...
    A: ...
    """.strip()

        text = generate_llm_answer(
            prompt,
            llm_chunks,
            query_type="qa",
            conversation_history=conversation_history,
        )

        items = []
        for block in text.split("Q:"):
            block = block.strip()
            if not block or "A:" not in block:
                continue
            q, a = block.split("A:", 1)
            items.append({
                "front": q.strip(),
                "back": a.strip(),
                "tags": ["auto"],
            })

        return {"items": items[:4]}

    if mode == "QUIZ":
        llm_chunks = _prepare_chunks_for_llm(retrieved_chunks)

        prompt = """
    Create 3 multiple-choice questions based only on the document.

    Rules:
    - Each question must have exactly 4 choices
    - Only 1 correct answer
    - Questions should test understanding of the document
    - Do not use outside knowledge

    Format exactly:
    Q: ...
    A. ...
    B. ...
    C. ...
    D. ...
    Answer: A
    """.strip()

        text = generate_llm_answer(
            prompt,
            llm_chunks,
            query_type="qa",
            conversation_history=conversation_history,
        )

        items = []
        blocks = text.split("Q:")
        for block in blocks:
            block = block.strip()
            if not block or "Answer:" not in block:
                continue

            lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
            if not lines:
                continue

            question = lines[0]
            choices = []
            answer_index = None

            for line in lines[1:]:
                if line.startswith(("A.", "B.", "C.", "D.")):
                    choices.append(line[2:].strip())
                elif line.startswith("Answer:"):
                    ans = line.replace("Answer:", "").strip().upper()
                    mapping = {"A": 0, "B": 1, "C": 2, "D": 3}
                    answer_index = mapping.get(ans)

            if len(choices) == 4 and answer_index is not None:
                items.append({
                    "type": "mcq",
                    "question": question,
                    "choices": choices,
                    "answer_index": answer_index,
                })

        return {"items": items[:3]}

    if mode == "MINDMAP":
        llm_chunks = _prepare_chunks_for_llm(retrieved_chunks)

        prompt = """
    Create a study mindmap from the document.

    Rules:
    - Return 1 main topic
    - Return 4 to 6 main branches
    - Each branch should have 2 short subpoints
    - Use only the document content

    Format exactly:
    Main: ...
    - Branch 1
    - Subpoint 1
    - Subpoint 2
    - Branch 2
    - Subpoint 1
    - Subpoint 2
    """.strip()

        text = generate_llm_answer(
            prompt,
            llm_chunks,
            query_type="summary",
            conversation_history=conversation_history,
        )

        root = {"title": "Mindmap", "children": []}
        current_branch = None

        for raw_line in text.splitlines():
            line = raw_line.rstrip()

            if line.startswith("Main:"):
                root["title"] = line.replace("Main:", "", 1).strip() or "Mindmap"
            elif line.startswith("- ") and not line.startswith("  - "):
                current_branch = {
                    "title": line[2:].strip(),
                    "children": [],
                }
                root["children"].append(current_branch)
            elif raw_line.startswith("  - ") and current_branch is not None:
                current_branch["children"].append({
                    "title": raw_line.strip()[2:].strip(),
                    "children": [],
                })

        return root

    return {"text": "Unsupported mode"}

def choose_dynamic_k(user_message: str, conversation_history=None) -> int:
    q = _normalize_text(user_message)
    qtype = _query_type(user_message)

    if detect_overview_query(user_message):
        return 18
    if qtype == "compare":
        return 8
    if qtype in {"summary", "explain", "keypoints"}:
        return 8
    if detect_factual_query(user_message):
        return 3
    if _is_follow_up_document_query(q):
        return 6
    return 4


def rerank_chunks(query: str, candidates, top_n: int = 6):
    q_low = _normalize_text(query)
    q_tokens = set(_tokenize(query))
    reranked = []

    for item in candidates:
        chunk = item["chunk"]
        raw_text = (chunk.text or "")[:3000]
        cleaned = clean_chunk_text(raw_text)
        low = cleaned.lower()
        tokens = set(_tokenize(cleaned))

        overlap = len(q_tokens & tokens)
        exact_boost = 4.0 if q_low and q_low in low else 0.0

        heading_boost = 0.0
        lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]
        if lines:
            first = lines[0].lower()
            if any(tok in first for tok in q_tokens):
                heading_boost += 2.0

        density_boost = min(overlap * 0.25, 3.0)

        reranked.append({
            **item,
            "rerank_score": item.get("score", 0.0) + exact_boost + heading_boost + density_boost,
        })

    reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
    return reranked[:top_n]

def extract_followup_search_clues(retrieved_chunks, max_clues: int = 3):
    clues = []
    seen = set()

    for item in retrieved_chunks:
        chunk = item["chunk"]
        cleaned = clean_chunk_text(chunk.text)

        for line in cleaned.splitlines():
            line = line.strip()
            if len(line) < 12:
                continue

            lowered = line.lower()
            if lowered in seen:
                continue

            if _looks_like_heading(line) or len(clues) < max_clues:
                clues.append(line[:120])
                seen.add(lowered)

            if len(clues) >= max_clues:
                return clues

    return clues

def retrieve_multi_hop(material_id: int, query: str, k: int = 4, conversation_history=None):
    rewritten_query = rewrite_user_query(query, conversation_history=conversation_history)

    recall_k = max(k * 3, 12)
    hop1 = retrieve_top_chunks(material_id, rewritten_query, k=recall_k)
    if not hop1:
        return []

    hop1 = _finalize_ranked_results(rewritten_query, hop1, top_n=max(6, k))
    clues = extract_followup_search_clues(hop1, max_clues=2)

    hop2_all = []
    for clue in clues:
        second_query = f"{rewritten_query} {clue}"
        hop2_hits = retrieve_top_chunks(material_id, second_query, k=8)
        hop2_all.extend(hop2_hits)

    merged = []
    seen_ids = set()
    for item in hop1 + hop2_all:
        cid = item["chunk"].id
        if cid in seen_ids:
            continue
        merged.append(item)
        seen_ids.add(cid)

    merged = _finalize_ranked_results(rewritten_query, merged, top_n=max(8, k + 2))

    expanded = expand_with_neighbor_chunks(
        material_id,
        merged,
        window=1,
        limit=max(10, k + 4),
    )

    final_candidates = expanded if expanded else merged
    final_ranked = _finalize_ranked_results(
        rewritten_query,
        final_candidates,
        top_n=max(6, k),
    )
    return final_ranked

def retrieve_for_level2_chat(material_id: int, query: str, k: int = 4, conversation_history=None):
    if detect_overview_query(query):
        return retrieve_for_chat(
            material_id,
            query,
            k=max(8, k),
            conversation_history=conversation_history,
        )

    if _query_needs_multi_hop(query, conversation_history=conversation_history):
        return retrieve_multi_hop(
            material_id,
            query,
            k=k,
            conversation_history=conversation_history,
        )

    return retrieve_for_chat(
        material_id,
        query,
        k=k,
        conversation_history=conversation_history,
    )

def retrieve_memory_for_chat(conversation_id: int, query: str, top_k: int = 4):
    memories = ConversationMemory.objects.filter(conversation_id=conversation_id).only(
        "id", "text", "embedding", "importance", "memory_type"
    )

    if not query.strip():
        return []

    query_embedding = None
    if get_embedding is not None:
        try:
            query_embedding = get_embedding(query[:800])
        except Exception:
            query_embedding = None

    scored = []
    for mem in memories:
        text = (mem.text or "").strip()
        if not text:
            continue

        keyword_score = _keyword_score(query, text)
        semantic_score = 0.0
        if query_embedding is not None and getattr(mem, "embedding", None):
            semantic_score = _cosine_similarity(query_embedding, mem.embedding)

        score = semantic_score * 10.0 + keyword_score * 0.35 + float(mem.importance or 1.0)

        if score > 0:
            scored.append({
                "memory": mem,
                "score": score,
                "semantic_score": semantic_score,
                "keyword_score": keyword_score,
            })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]

def build_memory_context(memory_hits):
    lines = []
    for item in memory_hits:
        mem = item["memory"]
        if mem.text:
            lines.append(f"- {mem.text.strip()}")
    return "\n".join(lines).strip()
