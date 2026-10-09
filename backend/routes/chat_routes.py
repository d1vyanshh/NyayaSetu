from __future__ import annotations

import json
import re
from dataclasses import dataclass

from flask import Blueprint, jsonify, request

from rights_module.situation_classifier import situation_classifier
from utils.explainability import build_explainability
from utils.hallucination_guard import apply_confidence_penalty, verify_claims, warnings_for_unverified
from utils.llm_client import GROUNDING_RULE, generate as llm_generate, parse_json_response
from utils.retriever import Chunk, chunks_to_prompt, retrieve as shared_retrieve


chat_bp = Blueprint("chat_routes", __name__)


@dataclass
class ChatContext:
    query: str
    domain: str | None
    messages: list[dict]


def _feature_hint(query: str) -> tuple[str | None, str]:
    text = query.lower()
    if any(word in text for word in ["translate", "plain english", "legal jargon", "what does this mean"]):
        return "translator", "This looks like text I can translate or explain in plain English. Want me to?"
    if re.search(r"\barticle\s*\d+.*\barticle\s*\d+", text) or "compare" in text:
        return "article_comparator", "This looks like an article comparison. Want me to compare the articles side by side?"
    if any(word in text for word in ["rights card", "know my rights", "arrest rights", "consumer rights", "tenant rights", "employment rights"]):
        return "rights_card", "This looks like a rights-card request. Want a printable rights card?"
    if any(word in text for word in ["fired", "evicted", "detained", "arrested", "landlord", "employer", "scenario", "what happens if"]):
        return "scenario_simulator", "This looks like a scenario I can simulate in detail. Want me to?"
    if any(word in text for word in ["unfair", "violation", "treated fairly", "discriminated"]):
        return "fairness_check", "This may involve a rights violation. Want me to run a fairness check?"
    return None, ""


def _quick_actions(query: str, hint: str | None) -> list[dict]:
    if hint == "scenario_simulator":
        return [
            {"label": "Simulate this scenario", "action": "simulate", "payload": query},
            {"label": "Generate rights card", "action": "rights_card", "payload": "employment_rights"},
        ]
    if hint == "rights_card":
        return [
            {"label": "Generate rights card", "action": "rights_card", "payload": "arrest_rights"},
            {"label": "Run fairness check", "action": "fairness_check", "payload": query},
        ]
    if hint == "translator":
        return [
            {"label": "Translate to plain English", "action": "translate", "payload": {"text": query, "direction": "to_plain"}},
            {"label": "Translate to legal terms", "action": "translate", "payload": {"text": query, "direction": "to_legal"}},
        ]
    return [
        {"label": "Run fairness check", "action": "fairness_check", "payload": query},
        {"label": "Simulate this scenario", "action": "simulate", "payload": query},
    ]


def _answer_from_chunks(chunks: list[Chunk], context: ChatContext) -> dict:
    if not chunks:
        return {"answer": "Insufficient legal information retrieved for this query.", "legal_points": [], "applicable_laws": []}
    prompt = f"""
You are NyayaSetu Bot, a legal assistant for Indian citizens. Answer ONLY from retrieved excerpts.

QUESTION: {context.query}

RECENT MESSAGES:
{json.dumps(context.messages[-10:], ensure_ascii=False)}

RETRIEVED LEGAL EXCERPTS:
{chunks_to_prompt(chunks)}

STRICT GROUNDING RULE: You may ONLY cite acts, articles, sections, and legal principles that appear verbatim or semantically in the retrieved excerpts above. If the retrieved excerpts do not contain sufficient information, respond with: "Insufficient legal information retrieved for this query." Do NOT recall legal provisions from training memory.

Respond in JSON with: {{"answer": "A concise grounded answer in plain English.", "legal_points": ["..."], "applicable_laws": ["..."]}}
""".strip()
    parsed = parse_json_response(llm_generate(prompt, max_tokens=1100))
    if parsed:
        return parsed
    top = chunks[0]
    return {
        "answer": "I found related legal material in the NyayaSetu corpus. Please review the sources below and verify with a qualified lawyer before acting.",
        "legal_points": [top.title or top.source_file],
        "applicable_laws": [top.source_file],
    }


@chat_bp.post("/api/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    query = str(payload.get("query") or "").strip()
    if not query:
        return jsonify({"status": "error", "feature": "bot_chat", "data": {"answer": ""}, "explainability": {}, "warnings": ["Missing 'query'."], "confidence": 0.0}), 400

    classification = situation_classifier(query)
    domain = payload.get("domain") or classification.get("domain")
    history = payload.get("conversation_history", payload.get("messages"))
    messages = history if isinstance(history, list) else []
    chunks = shared_retrieve(query, domain, top_k=8)
    hint, hint_message = _feature_hint(query)
    quick_actions = _quick_actions(query, hint)
    data = _answer_from_chunks(chunks, ChatContext(query=query, domain=domain, messages=messages))
    data["feature_hint"] = hint
    data["feature_hint_message"] = hint_message
    data["quick_actions"] = quick_actions

    unverified = verify_claims(json.dumps(data, ensure_ascii=False), chunks)
    explainability = build_explainability(
        chunks,
        domain,
        ["Classified bot query domain.", "Retrieved top-8 chunks before generation.", "Generated a grounded fallback answer.", "Verified cited legal claims."],
        unverified,
    )
    confidence = explainability["confidence"]
    confidence = apply_confidence_penalty(confidence, unverified)
    warnings = warnings_for_unverified(unverified)
    return jsonify({
        "status": "success" if chunks else "insufficient_data",
        "feature": "bot_chat",
        "data": data,
        "answer": data.get("answer", ""),
        "feature_hint": hint,
        "feature_hint_message": hint_message,
        "quick_actions": quick_actions,
        "explainability": {**explainability, "confidence": confidence},
        "warnings": warnings,
        "confidence": confidence,
    })
