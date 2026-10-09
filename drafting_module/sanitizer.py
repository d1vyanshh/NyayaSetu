"""Ollama-powered legal template sanitizer for NyayaDraft."""

from __future__ import annotations

import os
import re

import requests


OLLAMA_URL = os.getenv("OLLAMA_URL") or os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/") + "/api/generate"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3:mini")
OLLAMA_TIMEOUT = int(os.getenv("NYAYADRAFT_OLLAMA_TIMEOUT", os.getenv("OLLAMA_TIMEOUT", "120")))

SANITIZE_PROMPT = (
    "Clean this messy legal text extracted from a PDF. "
    "1. Remove page numbers, headers, and website noise. "
    "2. Identify all underscores (____), blanks, or bracketed text and replace them with "
    "descriptive placeholders in double curly braces, e.g., {{landlord_name}}. "
    "3. Return ONLY the cleaned legal document text."
)


def fallback_sanitize_legal_text(raw_text: str) -> str:
    """Deterministic cleanup used if Ollama is unavailable."""
    cleaned = raw_text.replace("\x00", "")
    cleaned = re.sub(r"\n?\s*Page\s+\d+\s*(?:of\s+\d+)?\s*\n?", "\n", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"https?://\S+|www\.\S+", "", cleaned)
    cleaned = re.sub(r"_{3,}", "{{blank_field}}", cleaned)
    cleaned = re.sub(
        r"\[([A-Za-z][A-Za-z0-9 _/-]{2,60})\]",
        lambda match: "{{" + re.sub(r"[^a-z0-9]+", "_", match.group(1).lower()).strip("_") + "}}",
        cleaned,
    )
    cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def sanitize_legal_text(raw_text: str) -> str:
    """Call local Ollama and return cleaned legal document text."""
    text = str(raw_text or "").strip()
    if not text:
        return ""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"{SANITIZE_PROMPT}\n\n{text[:9000]}",
        "stream": False,
        "options": {
            "temperature": 0,
            "num_predict": 4096,
        },
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=OLLAMA_TIMEOUT)
        response.raise_for_status()
        sanitized = str(response.json().get("response") or "").strip()
        if sanitized:
            return sanitized
    except requests.RequestException:
        pass

    return fallback_sanitize_legal_text(text)
