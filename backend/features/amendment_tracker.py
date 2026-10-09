from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from utils.explainability import build_explainability
from utils.retriever import Chunk, retrieve as shared_retrieve


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "amendments.json"


@dataclass
class AmendmentQuery:
    article_number: str | None = None


def _load() -> list[dict]:
    if not DATA_PATH.exists():
        return []
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return data.get("amendments", [])


def retrieve(query: str, domain: str | None = "general") -> list[Chunk]:
    return shared_retrieve(query, domain, top_k=8)


def generate(chunks: list[Chunk], context: AmendmentQuery) -> dict:
    amendments = sorted(_load(), key=lambda item: (item.get("year", 0), item.get("amendment_number", 0)))
    if context.article_number:
        article = str(context.article_number)
        selected = [item for item in amendments if article in [str(a) for a in item.get("articles_affected", [])]]
        article_title = chunks[0].title if chunks else f"Article {article}"
        current_text = chunks[0].text[:1500] if chunks else ""
        return {
            "article": article,
            "article_title": article_title,
            "total_amendments_affecting": len(selected),
            "timeline": [
                {
                    "year": item.get("year"),
                    "amendment_number": item.get("amendment_number"),
                    "change_summary": item.get("summary"),
                    "reversed_by": "44th Amendment (1978)" if item.get("amendment_number") == 42 and article in {"19", "20", "21", "22"} else None,
                    "key_changes": item.get("key_changes", []),
                    "source_act": item.get("source_act"),
                    "source_chunks": [chunk.to_dict() for chunk in chunks[:3]],
                }
                for item in selected
            ],
            "current_text": current_text,
        }
    grouped: dict[str, list[dict]] = {}
    for item in amendments:
        decade = f"{int(item.get('year', 0)) // 10 * 10}s"
        grouped.setdefault(decade, []).append(item)
    return {
        "article": None,
        "total_amendments": len(amendments),
        "grouped_by_decade": grouped,
        "timeline": [
            {
                "year": item.get("year"),
                "amendment_number": item.get("amendment_number"),
                "change_summary": item.get("summary"),
                "key_changes": item.get("key_changes", []),
                "source_act": item.get("source_act"),
                "source_chunks": [chunk.id for chunk in chunks[:2]],
            }
            for item in amendments
        ],
    }


def run(article_number: str | None = None) -> dict:
    query = f"Article {article_number} Constitution amendment" if article_number else "Constitutional amendments India articles"
    chunks = retrieve(query, "general")
    data = generate(chunks, AmendmentQuery(article_number=article_number))
    explainability = build_explainability(chunks, "general", ["Loaded structured amendment reference data.", "Retrieved constitutional chunks for grounding context.", "Attached retrieved source chunk IDs to timeline rows."], [])
    return {"status": "success", "feature": "amendment_tracker", "data": data, "explainability": explainability, "warnings": [], "confidence": explainability["confidence"]}
