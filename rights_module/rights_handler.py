"""High-level handler for rights module modes."""

from __future__ import annotations

from rights_module.situation_classifier import situation_classifier
from rights_module.compliance_checker import (
    parse_business_input,
    generate_compliance_checklist,
    format_checklist_output,
)


def _build_answer_from_chunks(query: str, chunks: list[dict]) -> tuple[str, list[str]]:
    """Build a grounded prompt-style answer and source list from retrieved chunks."""
    if not chunks:
        return "No relevant legal information found", []

    context = "\n\n".join(c.get("text", "").strip() for c in chunks)
    answer_text = (
        "You are a legal assistant.\n"
        "Answer ONLY using the provided legal context.\n"
        "Do NOT give general advice.\n"
        "If the answer is not present, say: No relevant legal information found.\n\n"
        "LEGAL CONTEXT:\n"
        f"{context}\n\n"
        "QUESTION:\n"
        f"{query}"
    )
    source_titles = [
        chunk.get("metadata", {}).get("source") or chunk.get("title", "Unknown")
        for chunk in chunks
    ]
    return answer_text, list(dict.fromkeys(source_titles))


def handle_rights_query(user_input: str, retrieve_fn, mode: str = "auto") -> dict:
    """Handle a rights query in auto, situation, compliance, or direct mode."""
    classification = situation_classifier(user_input)
    business_info = parse_business_input(user_input)
    business_type = business_info.get("business_type")
    employee_count = business_info.get("employee_count")

    mode_used = mode
    domain_detected = classification.get("domain")
    confidence = classification.get("confidence")
    matched_keywords = classification.get("matched_keywords", [])
    print(f"Detected domain: {domain_detected} (confidence: {confidence}) - matched: {matched_keywords}")

    checklist = None
    answer = ""
    sources_used = []

    if mode == "auto":
        if business_type and employee_count is not None:
            mode_used = "compliance"
        elif domain_detected:
            mode_used = "situation"
        else:
            mode_used = "direct"

    if mode_used in ("situation", "direct"):
        domain_filter_to_use = domain_detected if (mode_used == "situation" and domain_detected) else None
        chunks = retrieve_fn(query=user_input, domain_filter=domain_filter_to_use, top_k=5)
        answer, sources_used = _build_answer_from_chunks(user_input, chunks)

    elif mode_used == "compliance":
        if business_type and employee_count is not None:
            checklist = generate_compliance_checklist(business_type, employee_count, retrieve_fn)
            answer = format_checklist_output(checklist, business_type, employee_count)
            sources_used = list(dict.fromkeys(
                source for item in checklist for source in item.get("sources", [])
            ))
        else:
            checklist = []
            answer = (
                "Could not determine business type and employee count from the input. "
                "Please provide a sentence like 'I run a restaurant with 15 employees'."
            )

    else:
        chunks = retrieve_fn(query=user_input, domain_filter=None, top_k=5)
        answer, sources_used = _build_answer_from_chunks(user_input, chunks)
        mode_used = "direct"

    return {
        "mode_used": mode_used,
        "domain_detected": domain_detected,
        "confidence": confidence,
        "matched_keywords": matched_keywords,
        "answer": answer,
        "checklist": checklist,
        "sources_used": sources_used,
    }
