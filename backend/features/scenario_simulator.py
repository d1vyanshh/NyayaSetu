from __future__ import annotations

import json
from dataclasses import dataclass

from rights_module.situation_classifier import situation_classifier

from utils.explainability import build_explainability
from utils.hallucination_guard import apply_confidence_penalty, verify_claims, warnings_for_unverified
from utils.llm_client import GROUNDING_RULE, generate as llm_generate, parse_json_response
from utils.retriever import Chunk, chunks_to_prompt, retrieve as shared_retrieve


@dataclass
class ScenarioContext:
    scenario: str
    domain: str | None


def retrieve(query: str, domain: str | None) -> list[Chunk]:
    return shared_retrieve(query, domain, top_k=10)


def generate(chunks: list[Chunk], context: ScenarioContext) -> dict:
    if not chunks:
        return {"simulation": {"summary": "Insufficient legal information retrieved for this query.", "legal_walkthrough": [], "rights_involved": [], "what_employer_cannot_do": [], "evidence_to_preserve": [], "possible_remedies": [], "timeline_estimate": "Unknown"}}
    prompt = f"""
You are a legal scenario simulator. Simulate a full legal walkthrough using ONLY the retrieved excerpts.

SCENARIO: {context.scenario}

RETRIEVED LEGAL EXCERPTS:
{chunks_to_prompt(chunks)}

{GROUNDING_RULE}

Respond in JSON with: {{ "simulation": {{ "summary": "...", "legal_walkthrough": [{{"step": 1, "title": "...", "detail": "...", "source_chunk_id": "..."}}], "rights_involved": ["..."], "what_employer_cannot_do": ["..."], "evidence_to_preserve": ["..."], "possible_remedies": ["..."], "timeline_estimate": "..." }} }}
""".strip()
    parsed = parse_json_response(llm_generate(prompt, max_tokens=1600))
    if parsed:
        return parsed
    top = chunks[0]
    return {"simulation": {"summary": "The scenario matches retrieved legal material and needs fact-specific review.", "legal_walkthrough": [{"step": 1, "title": top.title or "Review retrieved law", "detail": "The first retrieved source is the strongest available grounding for this scenario.", "source_chunk_id": top.id}], "rights_involved": [top.title or top.source_file], "what_employer_cannot_do": [], "evidence_to_preserve": ["Documents, notices, messages, salary slips, receipts, and dates."], "possible_remedies": ["Contact the relevant authority or court named in the source material."], "timeline_estimate": "Insufficient retrieved information for a reliable timeline."}}


def run(scenario: str) -> dict:
    domain = situation_classifier(scenario).get("domain")
    chunks = retrieve(scenario, domain)
    data = generate(chunks, ScenarioContext(scenario=scenario, domain=domain))
    unverified = verify_claims(json.dumps(data, ensure_ascii=False), chunks)
    explainability = build_explainability(chunks, domain, ["Classified domain.", "Retrieved top-10 chunks.", "Generated walkthrough.", "Verified legal claims."], unverified)
    confidence = explainability["confidence"]
    confidence = apply_confidence_penalty(confidence, unverified)
    warnings = warnings_for_unverified(unverified)
    return {"status": "success" if chunks else "insufficient_data", "feature": "scenario_simulator", "data": data, "explainability": {**explainability, "confidence": confidence}, "warnings": warnings, "confidence": confidence}
