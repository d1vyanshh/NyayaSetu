from __future__ import annotations

from flask import Blueprint, jsonify, request

from features.fairness_checker import run


fairness_bp = Blueprint("fairness_routes", __name__)


@fairness_bp.post("/api/fairness-check")
def fairness_check():
    data = request.get_json(silent=True) or {}
    situation = str(data.get("situation") or "").strip()
    if not situation:
        return jsonify({"status": "error", "feature": "fairness_checker", "data": {}, "explainability": {}, "warnings": ["Missing 'situation'."], "confidence": 0.0}), 400
    return jsonify(run(situation))
