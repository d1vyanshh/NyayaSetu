from __future__ import annotations

import html
import json
from dataclasses import dataclass
from pathlib import Path

from utils.explainability import build_explainability, compute_confidence
from utils.hallucination_guard import apply_confidence_penalty, verify_claims, warnings_for_unverified
from utils.llm_client import GROUNDING_RULE, generate as llm_generate, parse_json_response
from utils.retriever import Chunk, chunks_to_prompt, retrieve as shared_retrieve


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


@dataclass
class RightsCardContext:
    rights_type: str
    domain: str | None
    seed_query: str


def _load_mappings() -> dict:
    path = DATA_DIR / "rights_mappings.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def retrieve(query: str, domain: str | None) -> list[Chunk]:
    return shared_retrieve(query, domain, top_k=10)


def _printable_html(card: dict) -> str:
    rights = card.get("rights") or []
    items = "".join(
        f"<li><strong>{html.escape(str(item.get('right', 'Right')))}</strong><br>"
        f"{html.escape(str(item.get('plain_explanation', '')))}<br>"
        f"<small>{html.escape(str(item.get('legal_basis', '')))}</small></li>"
        for item in rights
    )
    title = html.escape(str(card.get("title") or "Know Your Rights"))
    return f"<!doctype html><html><head><meta charset='utf-8'><title>{title}</title><style>body{{font-family:Arial,sans-serif;margin:32px;color:#111}}li{{margin:12px 0}}.contact{{margin-top:24px}}</style></head><body><h1>{title}</h1><ul>{items}</ul><p class='contact'>National Legal Services Authority: 15100</p></body></html>"


def generate(chunks: list[Chunk], context: RightsCardContext) -> dict:
    if not chunks:
        return {"card": {"title": "Know Your Rights", "rights": [], "emergency_contacts": ["National Legal Services Authority: 15100"], "printable_html": ""}}
    prompt = f"""
You are a legal educator. Using ONLY the legal excerpts below, generate a "Know Your Rights" card for: {context.rights_type}.

RETRIEVED LEGAL EXCERPTS:
{chunks_to_prompt(chunks)}

For each right, include: the right itself, its legal basis (act + section from the excerpts), a plain English explanation (1-2 sentences), and what authorities CANNOT do. Do not add any right not supported by the excerpts.

{GROUNDING_RULE}

Respond in JSON with: {{ "card": {{ "title": "...", "rights": [{{"right": "...", "legal_basis": "...", "plain_explanation": "...", "what_they_cannot_do": "...", "source_chunk_id": "..."}}], "emergency_contacts": ["National Legal Services Authority: 15100"], "printable_html": "" }} }}
""".strip()
    parsed = parse_json_response(llm_generate(prompt, max_tokens=1400))
    card = parsed.get("card") if parsed else None
    if not isinstance(card, dict):
        top = chunks[0]
        card = {
            "title": f"Know Your Rights: {context.rights_type.replace('_', ' ').title()}",
            "rights": [{
                "right": top.title or "Right identified in retrieved source",
                "legal_basis": top.source_file,
                "plain_explanation": "The retrieved legal excerpt supports this right. Review the source for exact wording.",
                "what_they_cannot_do": "Authorities or parties cannot act contrary to the retrieved legal requirement.",
                "source_chunk_id": top.id,
            }],
            "emergency_contacts": ["National Legal Services Authority: 15100"],
            "printable_html": "",
        }
    card["printable_html"] = card.get("printable_html") or _printable_html(card)
    return {"card": card}


def run(rights_type: str) -> dict:
    mappings = _load_mappings()
    mapping = mappings.get(rights_type) or {}
    domain = mapping.get("domain")
    query = mapping.get("seed_query") or f"rights of a person during {rights_type}"
    chunks = retrieve(query, domain)
    context = RightsCardContext(rights_type=rights_type, domain=domain, seed_query=query)
    data = generate(chunks, context)
    unverified = verify_claims(json.dumps(data, ensure_ascii=False), chunks)
    explainability = build_explainability(
        chunks,
        domain,
        extra_steps=["Mapped rights type to domain.", "Retrieved top-10 chunks.", "Generated card from retrieved excerpts.", "Verified cited claims."],
        unverified_claims=unverified,
    )
    confidence = explainability["confidence"]
    confidence = apply_confidence_penalty(confidence, unverified)
    warnings = warnings_for_unverified(unverified)
    return {"status": "success" if chunks else "insufficient_data", "feature": "rights_card_generator", "data": data, "explainability": {**explainability, "confidence": confidence}, "warnings": warnings, "confidence": confidence}
