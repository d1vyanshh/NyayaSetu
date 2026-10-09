from __future__ import annotations

import json
import re
from dataclasses import dataclass

from rights_module.situation_classifier import situation_classifier

from utils.explainability import build_explainability, compute_confidence
from utils.hallucination_guard import apply_confidence_penalty, verify_claims, warnings_for_unverified
from utils.llm_client import GROUNDING_RULE, generate as llm_generate, parse_json_response
from utils.retriever import Chunk, chunks_to_prompt, retrieve as shared_retrieve


VIOLATION_KEYWORDS = {
    "unpaid_wages": ["unpaid", "salary", "wages", "overtime", "minimum wage"],
    "wrongful_termination": ["fired", "terminated", "dismissed", "notice period"],
    "unlawful_detention": ["arrest", "detention", "custody", "locked"],
    "consumer_defect": ["defective", "refund", "warranty", "damaged"],
    "domestic_violence": ["violence", "abuse", "harassment", "dowry"],
}


@dataclass
class FairnessContext:
    situation: str
    domain: str | None
    violation_keywords: list[str]


def extract_violation_keywords(text: str) -> list[str]:
    lowered = text.lower()
    found = []
    for label, keywords in VIOLATION_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            found.append(label)
    return found


def retrieve(query: str, domain: str | None) -> list[Chunk]:
    return shared_retrieve(query, domain, top_k=8)


def generate(chunks: list[Chunk], context: FairnessContext) -> dict:
    if not chunks:
        return {"possible_violations": [], "suggested_next_steps": ["Insufficient legal information retrieved for this query."]}

    prompt = f"""
You are a legal rights advisor. Based ONLY on the retrieved legal excerpts below,
identify any rights violations in this situation. Do NOT cite any act, section, or
article that does not appear in the excerpts. If evidence is insufficient, say so.

SITUATION: {context.situation}

RETRIEVED LEGAL EXCERPTS:
{chunks_to_prompt(chunks)}

{GROUNDING_RULE}

Respond ONLY in JSON:
{{
  "possible_violations": [
    {{ "right": "...", "act": "...", "why_applicable": "...", "confidence": 0.0 }}
  ],
  "suggested_next_steps": ["..."]
}}
""".strip()
    parsed = parse_json_response(llm_generate(prompt, max_tokens=1200))
    if parsed:
        return parsed

    top = chunks[0]
    right = top.title or "Potential legal right identified from retrieved source"
    act = top.source_file
    return {
        "possible_violations": [
            {
                "right": right,
                "act": act,
                "why_applicable": "The retrieved legal excerpt matched the facts and should be reviewed for exact applicability.",
                "confidence": compute_confidence(chunks),
                "source_chunk_ids": [top.id],
            }
        ],
        "suggested_next_steps": ["Preserve documents and contact the authority named in the retrieved law, if any.", "Consult a qualified lawyer with the source excerpts."],
    }


def run(situation: str) -> dict:
    classification = situation_classifier(situation)
    domain = classification.get("domain")
    keywords = extract_violation_keywords(situation)
    chunks = retrieve(situation, domain)
    context = FairnessContext(situation=situation, domain=domain, violation_keywords=keywords)
    data = generate(chunks, context)
    response_text = json.dumps(data, ensure_ascii=False)
    unverified = verify_claims(response_text, chunks)
    explainability = build_explainability(
        chunks,
        domain,
        extra_steps=[
            "Classified legal domain using the existing situation classifier.",
            "Extracted visible violation keywords from the user's situation.",
            "Retrieved top-8 domain-filtered legal chunks before generation.",
            "Generated only from retrieved excerpts and ran hallucination guard.",
        ],
        unverified_claims=unverified,
    )
    confidence = explainability["confidence"]
    confidence = apply_confidence_penalty(confidence, unverified)
    warnings = warnings_for_unverified(unverified)
    return {
        "status": "success" if chunks else "insufficient_data",
        "feature": "fairness_check",
        "data": data,
        "explainability": {**explainability, "confidence": confidence},
        "warnings": warnings,
        "confidence": confidence,
    }
