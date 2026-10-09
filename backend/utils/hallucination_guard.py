from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from .retriever import Chunk


@dataclass
class UnsupportedClaim:
    claim: str
    confidence: float = 0.0
    warning: str = "Not found in retrieved corpus"

    def to_dict(self) -> dict:
        return asdict(self)


CLAIM_PATTERNS = [
    r"\bArticle\s+\d+[A-Z]?(?:\(\d+\))?\b",
    r"\bSection\s+\d+[A-Z]?(?:\(\d+\))?\b",
    r"\b[A-Z][A-Za-z&.,' -]{2,80}\s+Act,\s*\d{4}\b",
    r"\b[A-Z][A-Za-z&.,' -]{2,80}\s+Code,\s*\d{4}\b",
    r"\bCrPC\b|\bBNSS\b|\bIPC\b|\bBNS\b",
]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _claim_supported(claim: str, corpus_text: str) -> bool:
    claim_norm = _normalize(claim)
    if re.match(r"^(article|section)\s+\d", claim_norm):
        return claim_norm in corpus_text
    if claim_norm in corpus_text:
        return True
    if re.search(r"\b(act|code),\s*\d{4}\b", claim_norm):
        year_match = re.search(r"\b\d{4}\b", claim_norm)
        if year_match and year_match.group(0) not in corpus_text:
            return False
        distinctive = [
            token for token in re.findall(r"[a-z0-9]+", claim_norm)
            if token not in {"the", "act", "code", "of", "and"} and not token.isdigit()
        ]
        return bool(distinctive) and all(re.search(rf"\b{re.escape(token)}\b", corpus_text) for token in distinctive)
    tokens = [t for t in re.findall(r"[a-z0-9]+", claim_norm) if len(t) > 1]
    if not tokens:
        return True
    required = max(1, int(len(tokens) * 0.75))
    return sum(1 for token in tokens if re.search(rf"\b{re.escape(token)}\b", corpus_text)) >= required


def extract_claims(response_text: str) -> list[str]:
    claims: list[str] = []
    for pattern in CLAIM_PATTERNS:
        claims.extend(match.group(0).strip(" .,:;") for match in re.finditer(pattern, response_text or ""))
    return list(dict.fromkeys(claims))


def verify_claims(response_text: str, chunks: list[Chunk]) -> list[dict]:
    corpus_text = _normalize(" ".join(chunk.text for chunk in chunks))
    unsupported = []
    for claim in extract_claims(response_text):
        if not _claim_supported(claim, corpus_text):
            unsupported.append(UnsupportedClaim(claim=claim, confidence=0.0).to_dict())
    return unsupported


def apply_confidence_penalty(base_confidence: float, unverified_claims: list[dict] | list[UnsupportedClaim]) -> float:
    """
    Penalize confidence when generated legal claims are not grounded in the
    retrieved corpus. Accepts dicts or UnsupportedClaim objects for compatibility
    with API serialization.
    """
    count = len(unverified_claims or [])
    if count > 2:
        return min(base_confidence, 0.30)
    if count >= 1:
        return min(base_confidence, 0.55)
    return base_confidence


def warnings_for_unverified(unverified_claims: list[dict] | list[UnsupportedClaim]) -> list[str]:
    if not unverified_claims:
        return []
    return [
        "Some information could not be verified against the legal corpus. Please confirm with a qualified lawyer before taking action."
    ]
