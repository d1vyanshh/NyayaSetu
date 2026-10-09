from __future__ import annotations

from flask import Blueprint, jsonify, request

from features.legal_translator import run


translator_bp = Blueprint("translator_routes", __name__)


@translator_bp.post("/api/translate")
def translate():
    data = request.get_json(silent=True) or {}
    text = str(data.get("text") or "").strip()
    direction = str(data.get("direction") or "").strip()
    if not text or direction not in {"to_legal", "to_plain"}:
        return jsonify({"status": "error", "feature": "legal_translator", "data": {}, "explainability": {}, "warnings": ["Expected 'text' and direction 'to_legal' or 'to_plain'."], "confidence": 0.0}), 400
    return jsonify(run(text, direction))
