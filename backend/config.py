"""Configuration loader for backend runtime settings."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG: dict[str, Any] = {
    "llm_provider": "gemini",
    "gemini_model": "gemini-1.5-flash",
    "ollama_model": "phi3:mini",
    "ollama_host": "http://localhost:11434",
    "ollama_timeout": 20,
    "ollama_num_predict": 220,
}

ENV_OVERRIDES = {
    "LLM_PROVIDER": "llm_provider",
    "GEMINI_MODEL": "gemini_model",
    "OLLAMA_MODEL": "ollama_model",
    "OLLAMA_HOST": "ollama_host",
    "OLLAMA_TIMEOUT": "ollama_timeout",
    "OLLAMA_NUM_PREDICT": "ollama_num_predict",
}


def load_config() -> dict[str, Any]:
    """Load config.yaml from repo root and apply environment overrides."""
    config = DEFAULT_CONFIG.copy()
    config_path = Path(__file__).resolve().parents[1] / "config.yaml"
    if config_path.exists():
        try:
            data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            if isinstance(data, dict):
                for key, value in data.items():
                    if value is not None:
                        config[key] = value
        except Exception as exc:
            print(f"[WARN] Failed to load config.yaml: {exc}")

    for env_key, cfg_key in ENV_OVERRIDES.items():
        val = os.getenv(env_key)
        if val:
            config[cfg_key] = val

    config["llm_provider"] = str(config.get("llm_provider", "gemini")).lower()
    return config
