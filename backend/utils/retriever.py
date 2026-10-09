from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Callable, Iterable


RetrieveFn = Callable[..., list[dict]]

_retrieve_fn: RetrieveFn | None = None
BM25_WEIGHT = 0.4
COSINE_WEIGHT = 0.6

DOMAIN_ALIASES = {
    "criminal": ["criminal", "general"],
    "employment": ["employment", "labour"],
    "civil": ["civil", "tenant", "property"],
    "constitutional": ["constitutional", "general"],
}


@dataclass
class Chunk:
    id: str
    text: str
    source_file: str
    page_number: int | None
    domain: str
    bm25_score: float
    cosine_score: float
    combined_score: float
    title: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def configure_retriever(retrieve_fn: RetrieveFn) -> None:
    global _retrieve_fn
    _retrieve_fn = retrieve_fn


def _score_from_raw(raw: dict) -> tuple[float, float, float]:
    breakdown = raw.get("score_breakdown") or {}
    bm25 = float(breakdown.get("bm25") or raw.get("bm25") or raw.get("score") or 0.0)
    cosine = float(breakdown.get("cosine") or raw.get("cosine") or 0.0)
    combined = BM25_WEIGHT * bm25 + COSINE_WEIGHT * cosine
    if combined <= 0 and raw.get("score"):
        combined = float(raw.get("score") or 0.0)
    return bm25, cosine, combined


def _chunk_id(raw: dict, index: int) -> str:
    metadata = raw.get("metadata") or {}
    source = metadata.get("source") or "corpus"
    title = raw.get("title") or "chunk"
    return str(raw.get("id") or f"{source}:{title}:{index}")


def convert_chunk(raw: dict, index: int) -> Chunk:
    metadata = raw.get("metadata") or {}
    bm25, cosine, combined = _score_from_raw(raw)
    return Chunk(
        id=_chunk_id(raw, index),
        text=str(raw.get("text") or ""),
        source_file=str(metadata.get("source") or "Retrieved legal corpus"),
        page_number=metadata.get("page_number") or metadata.get("page"),
        domain=str(metadata.get("domain") or "general"),
        bm25_score=round(bm25, 4),
        cosine_score=round(cosine, 4),
        combined_score=round(combined, 4),
        title=str(raw.get("title") or ""),
    )


def retrieve(query: str, domain: str | None, top_k: int = 8) -> list[Chunk]:
    if _retrieve_fn is None:
        raise RuntimeError("Shared retriever is not configured.")
    domains_to_try = DOMAIN_ALIASES.get(domain or "", [domain])
    raw_chunks = []
    for candidate_domain in domains_to_try:
        raw_chunks = _retrieve_fn(query=query, domain_filter=candidate_domain, top_k=top_k)
        if raw_chunks:
            break
    if not raw_chunks and domain:
        raw_chunks = _retrieve_fn(query=query, domain_filter=None, top_k=top_k)
    return [convert_chunk(raw, index) for index, raw in enumerate(raw_chunks)]


def chunks_to_prompt(chunks: Iterable[Chunk], max_chars: int = 1200) -> str:
    parts = []
    for chunk in chunks:
        snippet = " ".join(chunk.text.split())[:max_chars]
        parts.append(
            f"[{chunk.id}] Source: {chunk.source_file}; Domain: {chunk.domain}; "
            f"Score: {chunk.combined_score}\n{snippet}"
        )
    return "\n\n".join(parts)
