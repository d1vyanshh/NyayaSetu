from __future__ import annotations

from flask import Blueprint, jsonify, request

from features.scenario_simulator import run


scenario_bp = Blueprint("scenario_routes", __name__)


@scenario_bp.post("/api/simulate-scenario")
def simulate_scenario():
    data = request.get_json(silent=True) or {}
    scenario = str(data.get("scenario") or "").strip()
    if not scenario:
        return jsonify({"status": "error", "feature": "scenario_simulator", "data": {}, "explainability": {}, "warnings": ["Missing 'scenario'."], "confidence": 0.0}), 400
    return jsonify(run(scenario))
