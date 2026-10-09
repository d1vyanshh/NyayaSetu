from __future__ import annotations

from flask import Blueprint, jsonify, request


advanced_stub_bp = Blueprint("advanced_stub_routes", __name__)


def _stub(feature: str, message: str):
    return jsonify({
        "status": "insufficient_data",
        "feature": feature,
        "data": {"message": message},
        "explainability": {
            "retrieved_chunks": [],
            "retrieval_scores": [],
            "domain_filter_applied": "not_implemented",
            "confidence": 0.0,
            "sources": [],
            "reasoning_steps": ["TODO: implement retrieve -> generate flow before enabling this endpoint."],
            "unverified_claims": [],
        },
        "warnings": ["Endpoint stub only; no LLM generation was performed."],
        "confidence": 0.0,
    }), 501


@advanced_stub_bp.post("/api/document-analyzer")
def document_analyzer():
    # TODO: upload legal notice/contract, retrieve law, then extract obligations, rights, and red flags.
    return _stub("document_analyzer", "Document analyzer is planned but not implemented.")


@advanced_stub_bp.post("/api/petition-draft")
def petition_draft():
    # TODO: classify situation, retrieve law, then draft a grounded petition or complaint letter.
    return _stub("petition_draft", "Petition drafting is planned but not implemented.")


@advanced_stub_bp.get("/api/landmark-cases")
def landmark_cases():
    # TODO: retrieve case-law chunks for request.args['topic'] and return grounded case summaries.
    topic = request.args.get("topic", "")
    return _stub("landmark_cases", f"Landmark case search is planned but not implemented. Topic: {topic}")


@advanced_stub_bp.post("/api/bail-eligibility")
def bail_eligibility():
    # TODO: classify offence facts, retrieve CrPC/BNSS chunks, then assess bail eligibility.
    return _stub("bail_eligibility", "Bail eligibility assessment is planned but not implemented.")


@advanced_stub_bp.post("/api/legal-timeline")
def legal_timeline():
    # TODO: retrieve limitation, notice-period, and procedural deadline chunks for the scenario.
    return _stub("legal_timeline", "Legal deadline timeline is planned but not implemented.")
