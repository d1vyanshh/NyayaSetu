from __future__ import annotations

from flask import Blueprint, jsonify, request

from features.article_comparator import run


comparator_bp = Blueprint("comparator_routes", __name__)


@comparator_bp.post("/api/compare-articles")
def compare_articles():
    data = request.get_json(silent=True) or {}
    article_a = str(data.get("article_a") or "").strip()
    article_b = str(data.get("article_b") or "").strip()
    if not article_a or not article_b:
        return jsonify({"status": "error", "feature": "article_comparator", "data": {}, "explainability": {}, "warnings": ["Expected 'article_a' and 'article_b'."], "confidence": 0.0}), 400
    return jsonify(run(article_a, article_b))
