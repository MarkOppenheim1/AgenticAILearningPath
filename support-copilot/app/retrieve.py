# app/retrieve.py
from pathlib import Path

DOCS_DIR = Path("data/docs")

def simple_retrieve(query: str, k: int = 3) -> list[str]:
    query_terms = set(query.lower().split())
    scored = []

    for path in DOCS_DIR.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        score = sum(1 for term in query_terms if term in text.lower())
        scored.append((score, path.name, text))

    scored.sort(reverse=True, key=lambda x: x[0])
    return [f"[SOURCE: {name}]\n{text[:2000]}" for score, name, text in scored[:k] if score > 0]