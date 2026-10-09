from __future__ import annotations

import json
from dataclasses import dataclass

from rights_module.situation_classifier import situation_classifier

from utils.explainability import build_explainability
from utils.hallucination_guard import apply_confidence_penalty, verify_claims, warnings_for_unverified
from utils.llm_client import GROUNDING_RULE, generate as llm_generate, parse_json_response
from utils.retriever import Chunk, chunks_to_prompt, retrieve as shared_retrieve


@dataclass
class TranslationContext:
    text: str
    direction: str
    domain: str | None


def retrieve(query: str, domain: str | None) -> list[Chunk]:
    return shared_retrieve(query, domain, top_k=8)


def generate(chunks: list[Chunk], context: TranslationContext) -> dict:
    if not chunks:
        return {"original": context.text, "translated": "Insufficient legal information retrieved for this query.", "direction": context.direction, "legal_terms_used": [], "ambiguities": ["No retrieved legal context was available."]}
    prompt = f"""
You are a legal translator. Translate without changing legal meaning.

TEXT: {context.text}
DIRECTION: {context.direction}

RETRIEVED LEGAL EXCERPTS:
{chunks_to_prompt(chunks)}

For to_legal, translate plain English into precise legal terminology and cite only retrieved provisions. For to_plain, explain legal jargon in plain English while preserving meaning. Flag ambiguities explicitly.

{GROUNDING_RULE}

Respond in JSON with: {{ "original": "...", "translated": "...", "direction": "{context.direction}", "legal_terms_used": [{{"term": "...", "definition": "...", "source_chunk_id": "..."}}], "ambiguities": [] }}
""".strip()
    parsed = parse_json_response(llm_generate(prompt, max_tokens=1100))
    if parsed:
        return parsed
    top = chunks[0]
    return {"original": context.text, "translated": context.text, "direction": context.direction, "legal_terms_used": [{"term": top.title or "Retrieved legal term", "definition": top.source_file, "source_chunk_id": top.id}], "ambiguities": ["LLM translation unavailable; returned grounded source term only."]}


def run(text: str, direction: str) -> dict:
    domain = situation_classifier(text).get("domain")
    chunks = retrieve(text, domain)
    data = generate(chunks, TranslationContext(text=text, direction=direction, domain=domain))
    unverified = verify_claims(json.dumps(data, ensure_ascii=False), chunks)
    explainability = build_explainability(chunks, domain, ["Classified domain.", "Retrieved legal definition context.", "Generated translation.", "Verified legal claims."], unverified)
    confidence = explainability["confidence"]
    confidence = apply_confidence_penalty(confidence, unverified)
    warnings = warnings_for_unverified(unverified)
    return {"status": "success" if chunks else "insufficient_data", "feature": "legal_translator", "data": data, "explainability": {**explainability, "confidence": confidence}, "warnings": warnings, "confidence": confidence}
