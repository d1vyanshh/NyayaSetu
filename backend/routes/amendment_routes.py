from __future__ import annotations

from flask import Blueprint, jsonify

from features.amendment_tracker import run


amendment_bp = Blueprint("amendment_routes", __name__)


@amendment_bp.get("/api/amendments")
def amendments():
    return jsonify(run())


@amendment_bp.get("/api/amendments/<article_number>")
def amendments_by_article(article_number: str):
    return jsonify(run(article_number))
