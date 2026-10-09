"""Compliance lookup and checklist generation for small-business queries."""

from __future__ import annotations

import re


COMPLIANCE_MAP = {
    "restaurant": [
        "Code on Wages Act, 2019",
        "Employees' State Insurance Act",
        "Employees' Provident Funds Act",
        "FSSAI",
        "Shops and Establishments Act",
        "Consumer Protection Act, 2019",
    ],
    "retail_shop": [
        "Code on Wages Act, 2019",
        "Shops and Establishments Act",
        "Consumer Protection Act, 2019",
        "Legal Metrology Act",
    ],
    "it_company": [
        "Code on Wages Act, 2019",
        "Employees' Provident Funds Act",
        "Shops and Establishments Act",
        "Sexual Harassment at Workplace Act",
    ],
    "manufacturing": [
        "Code on Wages Act, 2019",
        "Employees' State Insurance Act",
        "Employees' Provident Funds Act",
        "Factories Act",
        "Payment of Gratuity Act",
    ],
    "hospital_clinic": [
        "Code on Wages Act, 2019",
        "Employees' State Insurance Act",
        "Employees' Provident Funds Act",
        "Clinical Establishments Act",
        "Consumer Protection Act, 2019",
    ],
    "school_college": [
        "Code on Wages Act, 2019",
        "Employees' Provident Funds Act",
        "Consumer Protection Act, 2019",
        "Right to Education Act",
    ],
}

BUSINESS_ALIASES = {
    "restaurant": ["restaurant", "cafe", "hotel", "food business", "eatery", "canteen"],
    "retail_shop": ["retail shop", "shop", "store", "kirana", "showroom"],
    "it_company": ["it company", "software company", "startup", "office", "agency"],
    "manufacturing": ["factory", "manufacturing", "plant", "workshop"],
    "hospital_clinic": ["hospital", "clinic", "medical practice", "nursing home"],
    "school_college": ["school", "college", "coaching class", "institute"],
}

ACT_DOMAIN_HINTS = {
    "Code on Wages Act, 2019": "labour",
    "Employees' State Insurance Act": "labour",
    "Employees' Provident Funds Act": "labour",
    "Payment of Gratuity Act": "labour",
    "Factories Act": "labour",
    "Sexual Harassment at Workplace Act": "domestic_violence",
    "Shops and Establishments Act": "tenant",
    "Consumer Protection Act, 2019": "consumer",
    "Legal Metrology Act": "consumer",
    "FSSAI": None,
    "Clinical Establishments Act": None,
    "Right to Education Act": None,
}

INDEXED_ACTS = {
    "Code on Wages Act, 2019",
    "Shops and Establishments Act",
    "Consumer Protection Act, 2019",
}


def get_applicable_acts(business_type: str, employee_count: int) -> list[str]:
    """Return applicable compliance acts for a business type and employee count."""
    normalized_type = (business_type or "").strip().lower()
    acts = COMPLIANCE_MAP.get(normalized_type, [
        "Code on Wages Act, 2019",
        "Shops and Establishments Act",
    ]).copy()

    if employee_count >= 10:
        for act in ["Employees' State Insurance Act", "Employees' Provident Funds Act"]:
            if act not in acts:
                acts.append(act)
    if employee_count >= 20 and "Payment of Gratuity Act" not in acts:
        acts.append("Payment of Gratuity Act")

    return acts


def parse_business_input(user_text: str) -> dict:
    """Parse plain English business type and employee count."""
    text = " ".join(user_text.lower().split())
    business_type = None

    for canonical, aliases in BUSINESS_ALIASES.items():
        if any(alias in text for alias in aliases):
            business_type = canonical
            break

    employee_count = None
    employee_patterns = [
        r"\b(\d+)\s*(?:employees|employee|workers|worker|staff|people)\b",
        r"\bwith\s+(\d+)\b",
        r"\b(\d+)\b",
    ]
    for pattern in employee_patterns:
        match = re.search(pattern, text)
        if match:
            employee_count = int(match.group(1))
            break

    return {
        "business_type": business_type,
        "employee_count": employee_count,
    }


def _summarize_chunks(chunks: list[dict]) -> str:
    if not chunks:
        return ""
    text = " ".join(chunk.get("text", "").strip().replace("\n", " ") for chunk in chunks)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:260]


def generate_compliance_checklist(business_type: str, employee_count: int, retrieve_fn) -> list[dict]:
    """Generate a compliance checklist with retrieved legal context per act."""
    acts = get_applicable_acts(business_type, employee_count)
    checklist = []

    for act in acts:
        domain_filter = ACT_DOMAIN_HINTS.get(act)
        chunks = []
        if act in INDEXED_ACTS:
            try:
                chunks = retrieve_fn(
                    query=f"{act} registration wages working hours compliance requirements",
                    domain_filter=domain_filter,
                    top_k=3,
                )
            except Exception as exc:
                print(f"[WARN] Compliance retrieval failed for {act}: {exc}")

        summary_text = _summarize_chunks(chunks)
        source_titles = [chunk.get("metadata", {}).get("source") or chunk.get("title", "Unknown") for chunk in chunks]

        checklist.append({
            "act": act,
            "domain": domain_filter,
            "requirement_summary": summary_text or "No indexed section found; verify this requirement manually.",
            "status": "applicable" if summary_text else "needs_review",
            "status_symbol": "✓" if summary_text else "✗",
            "compliant": None,
            "sources": list(dict.fromkeys(source_titles)),
        })

    return checklist


def format_checklist_output(checklist: list[dict], business_type: str, employee_count: int) -> str:
    """Format the compliance checklist into readable text."""
    lines = [
        "COMPLIANCE CHECKLIST",
        f"Business: {business_type or 'unknown'} | Employees: {employee_count}",
        "-" * 44,
    ]

    for item in checklist:
        lines.append(f"{item.get('status_symbol', '[ ]')} {item['act']}")
        lines.append(f"    Requirement: {item.get('requirement_summary') or 'No summary available.'}")
        if item.get("sources"):
            lines.append(f"    Sources: {', '.join(item['sources'])}")
        lines.append("")

    return "\n".join(lines).strip()
