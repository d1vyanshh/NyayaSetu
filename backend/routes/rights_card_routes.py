from __future__ import annotations

from flask import Blueprint, jsonify, request

from features.rights_card_generator import run


rights_card_bp = Blueprint("rights_card_routes", __name__)


@rights_card_bp.post("/api/rights-card")
def rights_card():
    data = request.get_json(silent=True) or {}
    rights_type = str(data.get("rights_type") or "").strip()
    if not rights_type:
        return jsonify({"status": "error", "feature": "rights_card_generator", "data": {}, "explainability": {}, "warnings": ["Missing 'rights_type'."], "confidence": 0.0}), 400
    return jsonify(run(rights_type))
