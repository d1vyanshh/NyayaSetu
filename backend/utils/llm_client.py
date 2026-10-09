from __future__ import annotations

import json
import re
import socket
from typing import Callable


GenerateFn = Callable[[str], str]

_generate_fn: GenerateFn | None = None

GROUNDING_RULE = """
STRICT GROUNDING RULE: You may ONLY cite acts, articles, sections, and legal principles that appear verbatim or semantically in the retrieved excerpts above. If the retrieved excerpts do not contain sufficient information, respond with: "Insufficient legal information retrieved for this query." Do NOT recall legal provisions from training memory.
""".strip()


def configure_llm(generate_fn: GenerateFn | None) -> None:
    global _generate_fn
    _generate_fn = generate_fn


def generate(prompt: str, max_tokens: int = 1024) -> str:
    if _generate_fn is None:
        return "Insufficient legal information retrieved for this query."
    try:
        return (_generate_fn(prompt) or "").strip()
    except (TimeoutError, socket.timeout):
        return "Insufficient legal information retrieved for this query."
    except Exception as exc:
        return f"Insufficient legal information retrieved for this query. LLM error: {exc}"


def parse_json_response(raw: str) -> dict:
    cleaned = (raw or "").strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        for idx, ch in enumerate(cleaned):
            if ch != "{":
                continue
            try:
                parsed, _ = decoder.raw_decode(cleaned[idx:])
                return parsed if isinstance(parsed, dict) else {}
            except json.JSONDecodeError:
                continue
    return {}
