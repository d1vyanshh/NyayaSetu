from __future__ import annotations

import json
from dataclasses import dataclass

from utils.explainability import build_explainability
from utils.hallucination_guard import apply_confidence_penalty, verify_claims, warnings_for_unverified
from utils.llm_client import GROUNDING_RULE, generate as llm_generate, parse_json_response
from utils.retriever import Chunk, chunks_to_prompt, retrieve as shared_retrieve


@dataclass
class ArticleCompareContext:
    article_a: str
    article_b: str


def retrieve(query: str, domain: str | None = "general") -> list[Chunk]:
    return shared_retrieve(query, domain, top_k=6)


def generate(chunks: list[Chunk], context: ArticleCompareContext) -> dict:
    if not chunks:
        return {"article_a": {"number": context.article_a, "title": "", "summary": ""}, "article_b": {"number": context.article_b, "title": "", "summary": ""}, "comparison": {"similarities": [], "differences": [], "conflicts": [], "relationship": "Insufficient legal information retrieved for this query.", "landmark_cases_mentioned": []}}
    prompt = f"""
You are comparing two constitutional articles. Use ONLY the retrieved excerpts.

ARTICLE A: {context.article_a}
ARTICLE B: {context.article_b}

RETRIEVED LEGAL EXCERPTS:
{chunks_to_prompt(chunks)}

{GROUNDING_RULE}

Respond in JSON matching: {{ "article_a": {{"number": "{context.article_a}", "title": "...", "summary": "..."}}, "article_b": {{"number": "{context.article_b}", "title": "...", "summary": "..."}}, "comparison": {{"similarities": ["..."], "differences": ["..."], "conflicts": ["..."], "relationship": "...", "landmark_cases_mentioned": []}} }}
""".strip()
    parsed = parse_json_response(llm_generate(prompt, max_tokens=1400))
    if parsed:
        return parsed
    return {"article_a": {"number": context.article_a, "title": f"Article {context.article_a}", "summary": "See retrieved excerpts."}, "article_b": {"number": context.article_b, "title": f"Article {context.article_b}", "summary": "See retrieved excerpts."}, "comparison": {"similarities": ["Both articles were retrieved from the constitutional corpus."], "differences": [], "conflicts": [], "relationship": "LLM comparison unavailable; review retrieved excerpts.", "landmark_cases_mentioned": []}}


def run(article_a: str, article_b: str) -> dict:
    chunks_a = retrieve(f"Article {article_a} Constitution", "general")
    chunks_b = retrieve(f"Article {article_b} Constitution", "general")
    chunks = chunks_a + chunks_b
    data = generate(chunks, ArticleCompareContext(article_a=article_a, article_b=article_b))
    unverified = verify_claims(json.dumps(data, ensure_ascii=False), chunks)
    explainability = build_explainability(chunks, "general", ["Retrieved top-6 chunks for article A.", "Retrieved top-6 chunks for article B.", "Generated comparison from both retrieved chunk sets.", "Verified cited claims."], unverified)
    confidence = explainability["confidence"]
    confidence = apply_confidence_penalty(confidence, unverified)
    warnings = warnings_for_unverified(unverified)
    return {"status": "success" if chunks else "insufficient_data", "feature": "article_comparator", "data": data, "explainability": {**explainability, "confidence": confidence}, "warnings": warnings, "confidence": confidence}
