from __future__ import annotations

from dataclasses import asdict
from typing import Iterable

from .retriever import Chunk


def compute_confidence(chunks: Iterable[Chunk]) -> float:
    chunk_list = list(chunks)
    if not chunk_list:
        return 0.0
    scores = [max(0.0, c.combined_score) for c in chunk_list]
    mean_score = sum(scores) / len(scores)
    return round(min(1.0, mean_score / 10.0), 2)


def build_explainability(
    chunks: list[Chunk],
    domain: str | None,
    extra_steps: list[str] | None = None,
    unverified_claims: list[dict] | None = None,
) -> dict:
    return {
        "retrieved_chunks": [asdict(chunk) for chunk in chunks],
        "retrieval_scores": [
            {
                "chunk_id": chunk.id,
                "bm25_score": chunk.bm25_score,
                "cosine_score": chunk.cosine_score,
                "combined_score": chunk.combined_score,
            }
            for chunk in chunks
        ],
        "domain_filter_applied": domain or "all",
        "confidence": compute_confidence(chunks),
        "sources": list(dict.fromkeys(
            f"{chunk.source_file}{f' p.{chunk.page_number}' if chunk.page_number else ''}"
            for chunk in chunks
        )),
        "reasoning_steps": extra_steps or [],
        "unverified_claims": unverified_claims or [],
    }
