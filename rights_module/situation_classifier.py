"""Keyword-based situation-to-law mapper for domain-aware retrieval."""

from __future__ import annotations

import re


KEYWORD_GROUPS = {
    "labour": [
        "fired", "termination", "terminated", "salary", "wages", "overtime",
        "employer", "employee", "layoff", "pf", "esi", "provident fund",
        "notice period", "resign", "employment", "job", "worker", "bonus",
        "minimum wage", "unpaid", "dismissed", "workplace", "shift",
    ],
    "tenant": [
        "landlord", "tenant", "deposit", "security deposit", "eviction",
        "rent", "lease", "property", "flat", "house", "accommodation",
        "notice to vacate", "shop", "establishment", "commercial premises",
        "licence", "license", "working hours", "weekly holiday",
    ],
    "consumer": [
        "product", "defective", "refund", "consumer", "fraud", "service",
        "complaint", "warranty", "seller", "ecommerce", "e-commerce",
        "online purchase", "replacement", "deficiency", "unfair trade",
        "invoice", "bill", "damaged item", "fake product", "company",
        "manufacturer", "repair", "appliance", "refrigerator", "dishwasher",
        "washing machine", "ac", "phone", "laptop", "ignored", "not working",
        "stopped working",
    ],
    "domestic_violence": [
        "husband", "wife", "domestic", "violence", "abuse", "dowry",
        "harassment", "matrimonial", "cruelty", "shelter", "protection order",
        "residence order", "shared household", "in-laws", "physical abuse",
        "emotional abuse", "economic abuse",
    ],
}


def _keyword_matches(text: str, keyword: str) -> bool:
    if " " in keyword or "-" in keyword:
        return keyword in text
    return re.search(rf"\b{re.escape(keyword)}\b", text) is not None


def situation_classifier(text: str) -> dict:
    """
    Classify a situation into the best legal domain using keyword matching.

    Returns the selected domain, confidence, matched keywords, and per-domain
    scores. A single strong keyword is enough to auto-select a domain for demo
    retrieval, while confidence still shows how much evidence was found.
    """
    lowered = " ".join(text.lower().split())
    all_scores = {domain: 0 for domain in KEYWORD_GROUPS}
    matches_by_domain = {domain: [] for domain in KEYWORD_GROUPS}

    for domain, keywords in KEYWORD_GROUPS.items():
        for keyword in keywords:
            if _keyword_matches(lowered, keyword):
                all_scores[domain] += 1
                matches_by_domain[domain].append(keyword)

    best_domain = None
    best_count = 0
    for domain, count in all_scores.items():
        if count > best_count:
            best_domain = domain
            best_count = count

    if best_count >= 3:
        confidence = "high"
    elif best_count == 2:
        confidence = "medium"
    elif best_count == 1:
        confidence = "low"
    else:
        confidence = "none"
        best_domain = None

    matched_keywords = matches_by_domain.get(best_domain, []) if best_domain else []

    return {
        "domain": best_domain,
        "confidence": confidence,
        "matched_keywords": matched_keywords,
        "all_scores": all_scores,
        "matches_by_domain": matches_by_domain,
    }


if __name__ == "__main__":
    samples = {
        "labour": "I was fired without notice and my employer is not paying overtime wages.",
        "tenant": "My landlord wants me to vacate the flat and will not return my deposit.",
        "consumer": "The product I bought online was defective and I want a refund from the seller.",
        "domestic_violence": "My husband is abusing me and I need help with domestic violence protection.",
    }

    for expected_domain, sentence in samples.items():
        result = situation_classifier(sentence)
        print(f"Sample domain={expected_domain}: {result}")
