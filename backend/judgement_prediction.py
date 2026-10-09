import json
import math
import os
import re
import urllib.error
import urllib.request
from functools import lru_cache
from pathlib import Path


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_./:-]+")
CASE_CORPUS_DIR = Path(__file__).resolve().parent.parent / "case_corpus"
VECTOR_CACHE_PATH = Path(__file__).resolve().parent / "data" / "judgement_case_vectors.json"
EMBEDDING_MODEL = "nomic-embed-text"
VERDICT_SCORE = {"ALLOWED": 1.0, "PARTIAL": 0.5, "DISMISSED": 0.0, "UNCERTAIN": 0.5}
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "being", "by", "can", "could",
    "did", "do", "does", "for", "from", "has", "have", "i", "in", "is", "it", "me",
    "my", "no", "not", "of", "on", "or", "our", "that", "the", "their", "them", "then",
    "there", "this", "to", "was", "were", "what", "when", "where", "which", "who",
    "will", "with", "within", "without", "you", "your", "after", "before",
}

TOPIC_PROFILES = {
    "consumer": {
        "issue": "Consumer warranty / deficiency in service",
        "base_probability": 72,
        "positive": ["warranty", "bill", "invoice", "ignored", "complaint", "refund", "replacement", "defect", "stopped working"],
        "negative": ["misuse", "expired", "no bill", "second hand", "tampered"],
        "actions": [
            "Preserve invoice, warranty card, service tickets, emails, and photos of the defect.",
            "Send a written complaint or legal notice demanding repair, replacement, refund, and compensation.",
            "File before the District Consumer Commission if the company ignores the written complaint.",
        ],
        "risks": [
            "Weak proof of purchase or warranty coverage can reduce success.",
            "If the defect was caused by misuse or unauthorised repair, relief may be limited.",
        ],
        "evidence": ["Invoice or order confirmation", "Warranty terms", "Service complaints", "Photos/videos of defect", "Company replies"],
        "limitation": "2 years",
    },
    "bail": {
        "issue": "Bail / anticipatory bail assessment",
        "base_probability": 52,
        "positive": ["cooperated", "false", "business dispute", "no recovery", "custodial interrogation", "no criminal antecedents", "settlement"],
        "negative": ["absconding", "recovery", "weapon", "threat", "repeat offender", "serious offence", "ndps", "commercial quantity"],
        "actions": [
            "Prepare cooperation proof, notice history, and documents showing no custodial interrogation is needed.",
            "Address antecedents, recovery, witness intimidation, and flight-risk concerns directly.",
            "Move anticipatory or regular bail with a precise factual timeline.",
        ],
        "risks": [
            "Serious allegations, recovery requirements, or witness intimidation allegations can weaken bail.",
            "NDPS/commercial quantity matters have stricter bail thresholds.",
        ],
        "evidence": ["FIR copy", "Notice under CrPC/BNSS", "Cooperation proof", "Medical or location records", "Prior case history"],
        "limitation": "Urgent",
    },
    "service": {
        "issue": "Service termination / employment dispute",
        "base_probability": 58,
        "positive": ["no enquiry", "without notice", "continuous service", "salary", "termination", "regularization", "appointment"],
        "negative": ["probation", "misconduct", "contract ended", "unauthorised absence", "disciplinary enquiry"],
        "actions": [
            "Collect appointment letter, termination order, salary records, and service history.",
            "Send a representation challenging lack of notice or enquiry.",
            "Approach the labour/service forum applicable to your employment category.",
        ],
        "risks": [
            "Contractual or probationary appointments may reduce reinstatement chances.",
            "Proven misconduct or abandonment of service can weaken the claim.",
        ],
        "evidence": ["Appointment letter", "Termination order", "Salary slips", "Attendance records", "Department communications"],
        "limitation": "Verify service rules",
    },
    "maintenance": {
        "issue": "Maintenance under Section 125 / family support",
        "base_probability": 62,
        "positive": ["wife", "child", "income", "neglect", "maintenance", "unable to maintain"],
        "negative": ["independent income", "desertion", "mutual consent", "already paid"],
        "actions": [
            "Document income, expenses, relationship proof, and neglect/refusal to maintain.",
            "Prepare monthly expense chart and proof of the opposite party's earning capacity.",
            "File or respond before the family court/magistrate with supporting documents.",
        ],
        "risks": [
            "Independent income or existing support payments can reduce quantum.",
            "Incomplete income evidence may delay interim maintenance.",
        ],
        "evidence": ["Marriage proof", "Income proof", "Expense chart", "Bank statements", "Child-related expenses"],
        "limitation": "Continuing cause",
    },
    "custody": {
        "issue": "Child custody / guardianship assessment",
        "base_probability": 56,
        "positive": [
            "custody", "child", "minor", "welfare", "school", "education", "stable",
            "care", "mother", "father", "divorced", "visitation",
        ],
        "negative": [
            "abuse", "neglect", "violence", "unstable", "criminal", "addiction",
            "no income", "unsafe", "abandoned",
        ],
        "actions": [
            "Prepare a child-welfare focused affidavit covering schooling, health, routine, safety, and emotional care.",
            "Collect proof of stable residence, school involvement, medical care, expenses, and day-to-day caregiving.",
            "Ask for custody, interim custody, or visitation terms based on the child's welfare rather than parental entitlement.",
        ],
        "risks": [
            "Courts decide custody primarily on the welfare of the child, not automatically on divorce status or gender.",
            "Allegations of neglect, violence, instability, or parental alienation can materially affect custody.",
        ],
        "evidence": [
            "Child's school records and fee receipts",
            "Medical records and vaccination details",
            "Proof of residence and caregiving routine",
            "Expense records and income proof",
            "Any prior custody/visitation orders or settlement terms",
        ],
        "limitation": "Best welfare of child; no fixed limitation",
    },
    "criminal": {
        "issue": "Criminal trial / quashing assessment",
        "base_probability": 45,
        "positive": ["compromise", "civil dispute", "delay", "no evidence", "false implication"],
        "negative": ["murder", "dowry death", "weapon", "eyewitness", "medical evidence", "serious injury"],
        "actions": [
            "Map each allegation to available evidence and contradictions.",
            "Collect FIR, charge sheet, medical reports, witness statements, and orders.",
            "Consult a criminal lawyer on bail, quashing, discharge, or trial strategy.",
        ],
        "risks": [
            "Serious offences and direct evidence reduce prediction confidence.",
            "Courts rarely decide criminal merits without full record.",
        ],
        "evidence": ["FIR", "Charge sheet", "Medical report", "Witness statements", "Prior orders"],
        "limitation": "Procedure dependent",
    },
    "civil": {
        "issue": "Civil / contractual dispute",
        "base_probability": 55,
        "positive": ["agreement", "payment", "notice", "breach", "specific performance", "possession"],
        "negative": ["delay", "no contract", "oral agreement", "limitation", "unclean hands"],
        "actions": [
            "Collect contract, payment proof, notice, and chronology of breach.",
            "Check limitation and whether damages, injunction, or specific performance is the right relief.",
            "Send a legal notice before filing civil proceedings if appropriate.",
        ],
        "risks": [
            "Delay and missing written contract can weaken civil relief.",
            "Specific performance is discretionary and fact-heavy.",
        ],
        "evidence": ["Agreement", "Payment proof", "Legal notice", "Possession documents", "Correspondence"],
        "limitation": "Usually 3 years, verify facts",
    },
}


def tokenize(text: str) -> list[str]:
    tokens = [token.lower() for token in TOKEN_PATTERN.findall(text)]
    return [token for token in tokens if token not in STOP_WORDS and len(token) > 1]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


@lru_cache(maxsize=1)
def load_case_index() -> list[dict]:
    cases = []
    for path in sorted(CASE_CORPUS_DIR.glob("*.txt")):
        text = read_text(path)
        if not text.strip():
            continue
        head = text[:5000]
        tail = text[-3500:]
        tokens = tokenize(f"{path.stem} {head} {tail}")
        cases.append(
            {
                "source_file": path.name,
                "path": path,
                "title": extract_case_title(text, path.name),
                "topic": path.stem.rsplit("_", 1)[0].replace("_", " ").title(),
                "preview": normalize_space(head[:700]),
                "verdict_tail": tail,
                "embedding_text": normalize_space(f"{path.stem}\n{text[:2600]}\nFINAL VERDICT:\n{tail[-1400:]}"),
                "tokens": tokens,
                "token_set": set(tokens),
            }
        )
    return cases


@lru_cache(maxsize=1)
def inverse_document_frequency() -> dict[str, float]:
    cases = load_case_index()
    total = max(1, len(cases))
    document_frequency = {}
    for case in cases:
        for token in case["token_set"]:
            document_frequency[token] = document_frequency.get(token, 0) + 1
    return {
        token: math.log((total + 1) / (count + 0.5)) + 1
        for token, count in document_frequency.items()
    }


def retrieve_cases(facts: str, top_k: int = 5) -> list[dict]:
    query_tokens = tokenize(facts)
    if not query_tokens:
        return []

    query_counts = {}
    for token in query_tokens:
        query_counts[token] = query_counts.get(token, 0) + 1

    idf = inverse_document_frequency()
    scored = []
    for case in load_case_index():
        overlap = case["token_set"].intersection(query_counts)
        if not overlap:
            continue
        score = 0.0
        for token in overlap:
            score += query_counts[token] * idf.get(token, 1.0)
        score += topic_boost(facts, case["source_file"])
        scored.append((score, case))

    ranked = sorted(scored, key=lambda item: item[0], reverse=True)[:top_k]
    max_score = ranked[0][0] if ranked else 1.0
    return [
        {
            "source_file": case["source_file"],
            "title": case["title"],
            "topic": case["topic"],
            "similarity": round(min(0.98, score / max_score), 3),
            "preview": case["preview"],
            "verdict_tail": case["verdict_tail"],
        }
        for score, case in ranked
    ]


def retrieve_cases_vector(
    facts: str,
    ollama_host: str,
    top_k: int = 5,
    embedding_model: str = EMBEDDING_MODEL,
    timeout: int = 45,
) -> list[dict]:
    """Retrieve top cases using Ollama embeddings and cosine similarity."""
    query_embedding = call_ollama_embedding(ollama_host, facts, embedding_model, timeout)
    if not query_embedding:
        return retrieve_cases(facts, top_k=top_k)

    preferred_topic = infer_topic_key(facts, [])
    vector_index = load_or_build_vector_index(ollama_host, embedding_model, timeout, preferred_topic)
    if not vector_index:
        return retrieve_cases(facts, top_k=top_k)

    scored = []
    case_by_file = {case["source_file"]: case for case in load_case_index()}
    for item in vector_index:
        case = case_by_file.get(item["source_file"])
        if not case:
            continue
        vector_score = cosine_similarity(query_embedding, item.get("embedding", []))
        if topic_matches_file(preferred_topic, case["source_file"]):
            vector_score += 0.18
        scored.append((vector_score, case))

    ranked = sorted(scored, key=lambda entry: entry[0], reverse=True)[:top_k]
    max_score = ranked[0][0] if ranked else 1.0
    return [
        {
            "source_file": case["source_file"],
            "title": case["title"],
            "topic": case["topic"],
            "similarity": round(max(0.01, min(0.99, score / max_score)), 3),
            "preview": case["preview"],
            "verdict_tail": case["verdict_tail"],
            "case_verdict": infer_case_verdict(case["verdict_tail"]),
            "retrieval_method": "ollama_vector",
        }
        for score, case in ranked
    ]


@lru_cache(maxsize=16)
def load_or_build_vector_index(
    ollama_host: str,
    embedding_model: str = EMBEDDING_MODEL,
    timeout: int = 45,
    topic_key: str | None = None,
) -> list[dict]:
    all_cases = load_case_index()
    topic_cases = [case for case in all_cases if topic_matches_file(topic_key or "", case["source_file"])]
    cases = topic_cases if len(topic_cases) >= 5 else all_cases
    cached = read_vector_cache(embedding_model)
    cached_by_file = {item.get("source_file"): item for item in cached}
    index: list[dict] = []
    changed = False

    for case in cases:
        cached_item = cached_by_file.get(case["source_file"])
        if cached_item and cached_item.get("embedding"):
            index.append(cached_item)
            continue

        embedding = call_ollama_embedding(
            ollama_host=ollama_host,
            text=case["embedding_text"][:4200],
            model=embedding_model,
            timeout=timeout,
        )
        if embedding:
            index.append(
                {
                    "source_file": case["source_file"],
                    "topic": case["topic"],
                    "title": case["title"],
                    "embedding": embedding,
                }
            )
            changed = True

    if changed:
        merged = merge_vector_cache(cached, index)
        write_vector_cache(merged, embedding_model)
    return index


def merge_vector_cache(existing: list[dict], updated: list[dict]) -> list[dict]:
    merged = {item.get("source_file"): item for item in existing if item.get("source_file")}
    for item in updated:
        if item.get("source_file"):
            merged[item["source_file"]] = item
    return list(merged.values())


def read_vector_cache(embedding_model: str) -> list[dict]:
    if not VECTOR_CACHE_PATH.exists():
        return []
    try:
        payload = json.loads(VECTOR_CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if payload.get("embedding_model") != embedding_model:
        return []
    return payload.get("cases", []) if isinstance(payload.get("cases"), list) else []


def write_vector_cache(index: list[dict], embedding_model: str) -> None:
    try:
        VECTOR_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        VECTOR_CACHE_PATH.write_text(
            json.dumps({"embedding_model": embedding_model, "cases": index}),
            encoding="utf-8",
        )
    except OSError as exc:
        print(f"[WARN] Could not write judgement vector cache: {exc}")


def call_ollama_embedding(
    ollama_host: str,
    text: str,
    model: str = EMBEDDING_MODEL,
    timeout: int = 45,
) -> list[float] | None:
    url = ollama_host.rstrip("/") + "/api/embeddings"
    payload = {"model": model, "prompt": text}
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        embedding = data.get("embedding")
        return embedding if isinstance(embedding, list) else None
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        print(f"[WARN] Ollama embedding failed: {exc}")
        return None


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def topic_matches_file(topic_key: str, filename: str) -> bool:
    filename = filename.lower()
    signals = {
        "consumer": ["consumer_protection"],
        "bail": ["anticipatory_bail", "ndps_bail"],
        "service": ["termination_of_service", "regularization_of_service", "pensionary_benefits", "compassionate_appointment"],
        "maintenance": ["maintenance_section_125"],
        "custody": ["custody_of_minor_child"],
        "criminal": ["murder_section_302", "dowry_death", "quashing_of_fir", "quashing_of_criminal_proceedings"],
        "civil": ["specific_performance", "land_acquisition", "arbitration_and_conciliation"],
    }
    return any(signal in filename for signal in signals.get(topic_key, []))


def topic_boost(facts: str, filename: str) -> float:
    haystack = f"{facts} {filename}".lower()
    preferred = infer_topic_key(facts, [])
    filename_lower = filename.lower()
    preferred_file_signals = {
        "consumer": ["consumer_protection"],
        "bail": ["anticipatory_bail", "ndps_bail"],
        "service": ["termination_of_service", "regularization_of_service", "pensionary_benefits", "compassionate_appointment"],
        "maintenance": ["maintenance_section_125"],
        "custody": ["custody_of_minor_child"],
        "criminal": ["murder_section_302", "dowry_death", "quashing_of_fir", "quashing_of_criminal_proceedings"],
        "civil": ["specific_performance", "land_acquisition", "arbitration_and_conciliation"],
    }
    score = 0.0
    if any(signal in filename_lower for signal in preferred_file_signals.get(preferred, [])):
        score += 35.0
    boosts = {
        "consumer": ["consumer", "defect", "refund", "warranty", "seller", "service", "company", "refrigerator", "dishwasher", "washing machine", "replacement"],
        "bail": ["bail", "arrest", "custody", "ndps", "anticipatory"],
        "custody": ["custody", "minor child", "child", "divorce", "guardian", "visitation"],
        "maintenance": ["maintenance", "wife", "husband", "section 125"],
        "murder": ["murder", "302", "homicide"],
        "dowry": ["dowry", "304b", "cruelty"],
        "service": ["employment", "salary", "termination", "regularization", "pension"],
        "property": ["land", "acquisition", "compensation", "specific performance"],
    }
    for topic, words in boosts.items():
        if topic in filename.lower() and any(word in haystack for word in words):
            score += 8.0
    return score


def predict_judgement(
    facts: str,
    ollama_host: str,
    model: str,
    timeout: int = 180,
    top_k: int = 5,
) -> dict:
    top_k = max(5, min(20, int(top_k or 5)))
    similar_cases = retrieve_cases_vector(
        facts=facts,
        ollama_host=ollama_host,
        top_k=top_k,
        embedding_model=EMBEDDING_MODEL,
        timeout=min(timeout, 45),
    )
    if not similar_cases:
        return fallback_prediction(facts, [])
    return verdict_prediction_from_cases(facts, similar_cases)


def call_ollama_json(ollama_host: str, model: str, prompt: str, timeout: int) -> dict | None:
    url = ollama_host.rstrip("/") + "/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "format": "json",
        "stream": False,
        "keep_alive": "10m",
        "options": {"temperature": 0.1, "num_predict": 220},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=min(timeout, 20)) as response:
            data = json.loads(response.read().decode("utf-8"))
        raw = data.get("response", "{}")
        return json.loads(raw)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        print(f"[WARN] Judgement prediction Ollama call failed: {exc}")
        return None


def fallback_prediction(facts: str, similar_cases: list[dict]) -> dict:
    topic_key = infer_topic_key(facts, similar_cases)
    profile = TOPIC_PROFILES[topic_key]
    positive_hits = matched_signals(facts, profile["positive"])
    negative_hits = matched_signals(facts, profile["negative"])
    avg_similarity = average_similarity(similar_cases)
    corpus_confidence = confidence_from_cases(similar_cases, positive_hits, negative_hits)
    probability = profile["base_probability"] + (len(positive_hits) * 4) - (len(negative_hits) * 7)
    probability += int((avg_similarity - 0.65) * 18)
    probability = max(18, min(88, probability))
    outcome = outcome_from_probability(probability, negative_hits)
    top_case = similar_cases[0] if similar_cases else {}
    ratio_items = build_ratio_analysis(similar_cases, outcome, positive_hits, negative_hits)
    top_case_suffix = f", led by {top_case.get('source_file')}" if top_case else ""

    return normalize_prediction(
        {
            "predicted_outcome": outcome,
            "success_probability": probability,
            "confidence": corpus_confidence,
            "issue_identified": profile["issue"],
            "plain_english": (
                f"Your facts were matched primarily with {profile['issue'].lower()} precedents"
                f"{top_case_suffix}. "
                f"The corpus-based estimate is {probability}% because the facts contain "
                f"{', '.join(positive_hits[:4]) if positive_hits else 'some matching legal signals'}"
                f"{' but also risk signals such as ' + ', '.join(negative_hits[:3]) if negative_hits else ''}."
            ),
            "ratio_analysis": ratio_items,
            "recommended_actions": profile["actions"],
            "risk_factors": profile["risks"] + signal_risks(negative_hits),
            "evidence_needed": profile["evidence"],
            "do_this": profile["actions"],
            "avoid_this": profile["risks"],
            "similar_cases": [
                {
                    "source_file": case.get("source_file"),
                    "title": case.get("title"),
                    "topic": case.get("topic"),
                    "similarity": case.get("similarity"),
                    "why_similar": case.get("preview"),
                }
                for case in similar_cases
            ],
            "corpus_stats": {
                "cases_loaded": len(load_case_index()),
                "cases_retrieved": len(similar_cases),
                "source": "case_corpus",
            },
            "limitation_period": profile["limitation"],
        }
    )


def verdict_prediction_from_cases(facts: str, similar_cases: list[dict]) -> dict:
    topic_key = infer_topic_key(facts, similar_cases)
    profile = TOPIC_PROFILES[topic_key]
    positive_hits = matched_signals(facts, profile["positive"])
    negative_hits = matched_signals(facts, profile["negative"])
    weighted_score = 0.0
    weight_total = 0.0
    verdict_counts = {"ALLOWED": 0, "PARTIAL": 0, "DISMISSED": 0, "UNCERTAIN": 0}

    for index, case in enumerate(similar_cases):
        verdict = case.get("case_verdict") or infer_case_verdict(case.get("verdict_tail", ""))
        case["case_verdict"] = verdict
        rank_weight = max(0.2, 1.0 - index * 0.08)
        weight = max(0.08, float(case.get("similarity") or 0.1)) * rank_weight
        weighted_score += VERDICT_SCORE.get(verdict, 0.5) * weight
        weight_total += weight
        verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1

    base_probability = int(round((weighted_score / weight_total) * 100)) if weight_total else profile["base_probability"]
    probability = base_probability + min(10, len(positive_hits) * 2) - min(16, len(negative_hits) * 4)
    probability = max(15, min(90, probability))
    outcome = outcome_from_probability(probability, negative_hits)
    confidence = confidence_from_verdicts(similar_cases, verdict_counts, positive_hits, negative_hits)

    return normalize_prediction(
        {
            "predicted_outcome": outcome,
            "success_probability": probability,
            "confidence": confidence,
            "issue_identified": profile["issue"],
            "plain_english": (
                f"NyayaSetu compared your facts with {len(similar_cases)} similar past court decisions. "
                f"Based on how those matters ended, the estimated result is {outcome} at {probability}%."
            ),
            "ratio_analysis": build_ratio_analysis(similar_cases, outcome, positive_hits, negative_hits),
            "recommended_actions": profile["actions"],
            "risk_factors": profile["risks"] + signal_risks(negative_hits),
            "evidence_needed": profile["evidence"],
            "do_this": profile["actions"],
            "avoid_this": profile["risks"],
            "similar_cases": [
                {
                    "source_file": case.get("source_file"),
                    "title": case.get("title"),
                    "topic": case.get("topic"),
                    "similarity": case.get("similarity"),
                    "why_similar": case.get("preview"),
                    "case_verdict": case.get("case_verdict"),
                    "retrieval_method": case.get("retrieval_method", "keyword"),
                }
                for case in similar_cases
            ],
            "corpus_stats": {
                "cases_loaded": len(load_case_index()),
                "cases_retrieved": len(similar_cases),
                "source": "case_corpus",
                "retrieval": "ollama_embeddings_vector_search",
                "embedding_model": EMBEDDING_MODEL,
            },
            "limitation_period": profile["limitation"],
        }
    )


def infer_case_verdict(verdict_tail: str) -> str:
    """Infer the final order of a retrieved case from its verdict tail."""
    text = normalize_space(verdict_tail).lower()
    allowed_patterns = [
        r"\bappeal(?:s)? (?:is|are) allowed\b",
        r"\bpetition(?:s)? (?:is|are) allowed\b",
        r"\bapplication(?:s)? (?:is|are) allowed\b",
        r"\ballowed accordingly\b",
        r"\bset aside\b",
        r"\bgrant(?:ed)?\b",
        r"\brelief(?:s)? (?:is|are) granted\b",
    ]
    dismissed_patterns = [
        r"\bappeal(?:s)? (?:is|are) dismissed\b",
        r"\bpetition(?:s)? (?:is|are) dismissed\b",
        r"\bapplication(?:s)? (?:is|are) dismissed\b",
        r"\bdismissed accordingly\b",
        r"\bstands dismissed\b",
        r"\brejected\b",
        r"\bno merit\b",
    ]
    partial_patterns = [
        r"\bpartly allowed\b",
        r"\bpartially allowed\b",
        r"\ballowed in part\b",
        r"\bmodified\b",
        r"\bdisposed of\b",
        r"\bremanded\b",
    ]

    allowed = count_patterns(text, allowed_patterns)
    dismissed = count_patterns(text, dismissed_patterns)
    partial = count_patterns(text, partial_patterns)
    if partial and partial >= max(allowed, dismissed):
        return "PARTIAL"
    if allowed > dismissed:
        return "ALLOWED"
    if dismissed > allowed:
        return "DISMISSED"
    if partial:
        return "PARTIAL"
    return "UNCERTAIN"


def count_patterns(text: str, patterns: list[str]) -> int:
    return sum(len(re.findall(pattern, text, flags=re.IGNORECASE)) for pattern in patterns)


def confidence_from_verdicts(
    similar_cases: list[dict],
    verdict_counts: dict[str, int],
    positive_hits: list[str],
    negative_hits: list[str],
) -> int:
    if not similar_cases:
        return 25
    avg_similarity = average_similarity(similar_cases[:5])
    known_verdicts = sum(count for verdict, count in verdict_counts.items() if verdict != "UNCERTAIN")
    dominant = max(verdict_counts.values() or [0])
    agreement = dominant / max(1, len(similar_cases[:5]))
    confidence = 28 + int(avg_similarity * 28) + int(agreement * 24) + known_verdicts * 4
    confidence += min(10, len(positive_hits) * 2)
    confidence -= min(12, len(negative_hits) * 3)
    return max(28, min(90, confidence))


def verdict_summary(verdict_counts: dict[str, int]) -> str:
    parts = [
        f"{count} {verdict.lower()}"
        for verdict, count in verdict_counts.items()
        if count
    ]
    return ", ".join(parts) if parts else "unclear"


def infer_topic_key(facts: str, similar_cases: list[dict]) -> str:
    text = f"{facts} " + " ".join(str(case.get("topic", "")) for case in similar_cases)
    text = text.lower()
    if any(word in text for word in ["child custody", "custody of minor", "minor child", "custody", "visitation", "guardian", "guardianship"]) and any(word in text for word in ["child", "minor", "son", "daughter", "divorce", "divorced", "wife", "husband"]):
        return "custody"
    if any(word in text for word in ["consumer", "warranty", "refund", "replacement", "defect", "refrigerator", "dishwasher", "washing machine"]):
        return "consumer"
    if any(word in text for word in ["bail", "arrest", "anticipatory", "ndps", "police custody", "judicial custody"]):
        return "bail"
    if any(word in text for word in ["termination", "service", "salary", "regularization", "pension", "appointment", "employee"]):
        return "service"
    if any(word in text for word in ["maintenance", "section 125", "wife", "husband", "child"]):
        return "maintenance"
    if any(word in text for word in ["murder", "302", "dowry death", "304b", "fir", "quashing", "criminal"]):
        return "criminal"
    return "civil"


def matched_signals(facts: str, signals: list[str]) -> list[str]:
    lowered = facts.lower()
    return [signal for signal in signals if signal in lowered]


def average_similarity(similar_cases: list[dict]) -> float:
    if not similar_cases:
        return 0.0
    return sum(float(case.get("similarity") or 0) for case in similar_cases) / len(similar_cases)


def confidence_from_cases(similar_cases: list[dict], positive_hits: list[str], negative_hits: list[str]) -> int:
    if not similar_cases:
        return 22
    avg_similarity = average_similarity(similar_cases)
    topic_count = len(set(str(case.get("topic", "")) for case in similar_cases if case.get("topic")))
    confidence = 34 + int(avg_similarity * 32) + min(18, len(positive_hits) * 4) - min(12, len(negative_hits) * 4)
    if topic_count == 1:
        confidence += 8
    elif topic_count >= 3:
        confidence -= 6
    return max(28, min(86, confidence))


def outcome_from_probability(probability: int, negative_hits: list[str]) -> str:
    if probability >= 68 and len(negative_hits) <= 1:
        return "ALLOWED"
    if probability <= 38 or len(negative_hits) >= 3:
        return "DISMISSED"
    return "PARTIAL"


def build_ratio_analysis(similar_cases: list[dict], outcome: str, positive_hits: list[str], negative_hits: list[str]) -> list[dict]:
    ratio = []
    for case in similar_cases[:3]:
        case_verdict = case.get("case_verdict") or infer_case_verdict(case.get("verdict_tail", ""))
        ratio.append(
            {
                "source_file": case.get("source_file"),
                "principle": ratio_principle(case),
                "comparison": (
                    f"This retrieved case ended as {case_verdict}. "
                    f"Matched signals: {', '.join(positive_hits[:4]) or 'general factual overlap'}. "
                    f"Risk signals: {', '.join(negative_hits[:3]) or 'none obvious from the provided facts'}."
                ),
                "leans": case_verdict if case_verdict in {"ALLOWED", "DISMISSED", "PARTIAL"} else outcome,
            }
        )
    return ratio


def ratio_principle(case: dict) -> str:
    topic = str(case.get("topic", "")).lower()
    if "consumer" in topic:
        return "Consumer relief turns on proof of defect, deficiency in service, warranty coverage, and company response."
    if "bail" in topic:
        return "Bail turns on accusation severity, custody need, antecedents, cooperation, and risk of absconding or tampering."
    if "termination" in topic or "regularization" in topic or "pension" in topic:
        return "Service relief turns on appointment status, procedural fairness, notice, enquiry, and applicable service rules."
    if "maintenance" in topic:
        return "Maintenance depends on relationship proof, need, neglect, and earning capacity of the parties."
    if "custody" in topic or "minor child" in topic:
        return "Child custody is governed by the welfare of the child, including stability, care, schooling, safety, and emotional needs."
    if "murder" in topic or "dowry" in topic or "criminal" in topic or "fir" in topic:
        return "Criminal relief depends on offence gravity, prima facie evidence, procedural stage, and contradictions in the record."
    return "Civil relief depends on enforceable rights, limitation, documentary proof, conduct of parties, and appropriate forum."


def signal_risks(negative_hits: list[str]) -> list[str]:
    if not negative_hits:
        return []
    return [f"Your facts mention '{signal}', which may reduce the predicted success unless explained with evidence." for signal in negative_hits[:2]]


def normalize_prediction(prediction: dict) -> dict:
    outcome = str(prediction.get("predicted_outcome", "UNCERTAIN")).upper()
    if outcome not in {"ALLOWED", "DISMISSED", "PARTIAL", "UNCERTAIN"}:
        outcome = "UNCERTAIN"
    prediction["predicted_outcome"] = outcome
    prediction["success_probability"] = clamp_number(prediction.get("success_probability"), 0, 100, 50)
    prediction["confidence"] = clamp_number(prediction.get("confidence"), 0, 100, 40)
    prediction.setdefault("ratio_analysis", [])
    prediction.setdefault("recommended_actions", [])
    prediction.setdefault("risk_factors", [])
    prediction.setdefault("evidence_needed", [])
    prediction.setdefault("similar_cases", [])
    if not prediction.get("do_this"):
        prediction["do_this"] = prediction.get("recommended_actions", [])[:4]
    if not prediction.get("avoid_this"):
        prediction["avoid_this"] = prediction.get("risk_factors", [])[:4]
    if not prediction.get("misconceptions"):
        prediction["misconceptions"] = default_misconceptions(prediction)
    if not prediction.get("limitation_period"):
        prediction["limitation_period"] = infer_limitation_period(prediction)
    return prediction


def default_misconceptions(prediction: dict) -> list[dict]:
    topic_text = " ".join(
        str(case.get("topic", "")) for case in prediction.get("similar_cases", [])
    ).lower()
    if "consumer" in topic_text:
        return [
            {"statement": "I need a lawyer to file a consumer complaint", "verdict": "False"},
            {"statement": "Warranty cards are only for reference", "verdict": "False"},
            {"statement": "If the company offers any repair, I must accept it", "verdict": "False"},
            {"statement": "Consumer cases always take years to resolve", "verdict": "Partially true"},
        ]
    return [
        {"statement": "A prediction is the same as legal advice", "verdict": "False"},
        {"statement": "Similar cases guarantee the same result", "verdict": "False"},
        {"statement": "Missing documents can be fixed later without risk", "verdict": "Partially true"},
    ]


def infer_limitation_period(prediction: dict) -> str:
    topic_text = " ".join(
        str(case.get("topic", "")) for case in prediction.get("similar_cases", [])
    ).lower()
    if "consumer" in topic_text:
        return "2 years"
    if "section 138" in topic_text or "negotiable" in topic_text:
        return "30 days notice timeline"
    if "bail" in topic_text:
        return "Urgent"
    return "Verify from statute"


def clamp_number(value, minimum: int, maximum: int, fallback: int) -> int:
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        number = fallback
    return max(minimum, min(maximum, number))


def extract_case_title(text: str, filename: str) -> str:
    lines = [normalize_space(line) for line in text.splitlines() if normalize_space(line)]
    for line in lines[:18]:
        if " vs " in line.lower() or " v. " in line.lower():
            return line[:140]
    return filename.replace("_", " ").replace(".txt", "").title()


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()
