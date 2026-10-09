"""Concise comparison answers for generic ChatGPT vs grounded legal RAG."""

from __future__ import annotations

import re


COMPARISON_PATTERNS = [
    r"\bwhy\s+not\s+(?:use\s+)?chatgpt\b",
    r"\bwhy\s+(?:shouldn'?t|should\s+i\s+not)\s+(?:i\s+)?(?:use\s+)?chatgpt\b",
    r"\bwhy\s+(?:use\s+)?(?:this|rag|nyayasetu).*\bchatgpt\b",
    r"\bchatgpt\b.*\b(?:legal|law|lawyer|advice|rag|grounded|better|different)\b",
    r"\b(?:better|different).*\bchatgpt\b",
    r"\bwhy\s+not\s+(?:use\s+)?(?:a\s+)?general\s+(?:ai|llm|chatbot)\b",
]


def is_comparison_query(query: str) -> bool:
    """Return True when the user is asking why not use ChatGPT/general LLMs."""
    normalized = " ".join(query.lower().split())
    normalized = normalized.replace("chat gpt", "chatgpt")
    return any(re.search(pattern, normalized) for pattern in COMPARISON_PATTERNS)


def build_comparison_response(query: str) -> dict:
    """Build a frontend-compatible structured response without invoking RAG/LLM."""
    points = [
        {
            "issue": "Hallucination risk",
            "chatgpt_limitation": "A general model may produce plausible-sounding legal statements that are not present in the source law.",
            "rag_solution": "RAG retrieves relevant legal chunks first and answers from those documents.",
        },
        {
            "issue": "Lack of grounding",
            "chatgpt_limitation": "A general response may not show which article, act, or document supports the answer.",
            "rag_solution": "RAG can attach retrieved sections, citations, and source text to the response.",
        },
        {
            "issue": "Knowledge cutoff",
            "chatgpt_limitation": "A standalone model may not include newer laws, amendments, or local corpus updates.",
            "rag_solution": "RAG uses the documents currently loaded into the system, so updating the corpus updates retrieval.",
        },
        {
            "issue": "Jurisdiction mismatch",
            "chatgpt_limitation": "A general model may mix rules from different countries or legal systems.",
            "rag_solution": "RAG narrows answers to the configured Indian legal corpus and retrieved jurisdiction-specific materials.",
        },
    ]

    summary = "General chatbots are useful, but legal answers need source grounding, current documents, and jurisdiction control."
    analysis = (
        "NyayaSetu uses RAG to retrieve relevant legal documents before answering. "
        "This reduces unsupported claims, makes citations inspectable, keeps answers tied to the loaded corpus, "
        "and helps avoid mixing Indian law with rules from other jurisdictions."
    )

    return {
        "query": query,
        "ai_powered": False,
        "urgency": {
            "level": "STANDARD",
            "color": "#10b981",
            "message": "Informational comparison",
        },
        "case_type": "RAG Comparison",
        "summary": summary,
        "analysis": analysis,
        "key_points": [
            "General LLMs can hallucinate when not tied to source documents.",
            "RAG grounds answers in retrieved legal text.",
            "Corpus updates can reduce knowledge-cutoff issues.",
            "Jurisdiction-specific retrieval reduces legal mismatch.",
        ],
        "is_follow_up": False,
        "legal_topics": ["RAG grounding", "Legal AI reliability"],
        "articles_cited": [],
        "your_rights": [],
        "next_steps": [
            "Use retrieved source sections to verify legal claims.",
            "Check whether the cited act or article matches your jurisdiction.",
            "Consult a qualified lawyer for advice on a specific dispute.",
        ],
        "retrieved_sections": [],
        "structured": {
            "meta": {
                "domain": "explanation",
                "case_type": "RAG Comparison",
                "confidence": 100,
                "in_scope": True,
                "ai_powered": False,
                "llm_provider": "none",
            },
            "summary": {
                "one_line": summary,
                "signal": "Use grounded legal sources",
            },
            "plain_words": {
                "short_explanation": analysis,
            },
            "comparison": points,
            "applicable_laws": [],
            "rights_vs_limits": {
                "rights": [],
                "limits": [
                    "RAG quality depends on the quality and completeness of the loaded documents.",
                    "Grounded information is not a substitute for legal advice from a qualified lawyer.",
                ],
            },
            "steps": [],
            "sources": {
                "corpus_used": "No retrieval needed for this comparison answer",
                "chunks_retrieved": 0,
            },
            "followups": [
                "How does RAG retrieval work?",
                "What sources are used here?",
            ],
            "disclaimer": "This is an informational product comparison, not legal advice.",
        },
        "explainability": {
            "detected_domain": "comparison",
            "confidence": "high",
            "matched_keywords": ["chatgpt", "rag"],
            "number_of_chunks_used": 0,
            "source_documents": [],
            "short_explanation": "The query asks why a grounded RAG assistant is preferable to a general chatbot for legal information.",
            "retrieval_details": [],
        },
        "disclaimer": "This is an informational product comparison, not legal advice.",
    }
