from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import PyPDF2
import re
import os
import sys
import json
import socket
import urllib.request
import urllib.error
from pathlib import Path
from dotenv import load_dotenv
from config import load_config
from comparison_explainer import build_comparison_response, is_comparison_query
import tempfile
from document_intelligence import (
    DocumentCorpusStore,
    analyze_contract,
    decode_court_notice,
    extract_text,
)
from legal_doc_intel import build_legal_document_report
from judgement_prediction import predict_judgement
from rag_engine import (
    HybridRAGIndex,
    extract_legal_keywords,
    get_rights_and_steps,
    assess_urgency,
    tokenize,
)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from rights_module.situation_classifier import situation_classifier
from rights_module.rights_handler import handle_rights_query
from rights_module.corpus_loader import load_legal_corpus
from rights_module.compliance_checker import (
    parse_business_input,
    generate_compliance_checklist,
    format_checklist_output,
)

load_dotenv()
APP_CONFIG = load_config()

app = Flask(__name__)
CORS(app)

# ── LLM config ──────────────────────────────────────────────
LLM_PROVIDER = APP_CONFIG.get("llm_provider", "gemini")
GEMINI_MODEL = APP_CONFIG.get("gemini_model", "gemini-1.5-flash")
OLLAMA_MODEL = APP_CONFIG.get("ollama_model", "phi3:mini")
OLLAMA_HOST = APP_CONFIG.get("ollama_host", "http://localhost:11434")
try:
    OLLAMA_TIMEOUT = max(8, int(APP_CONFIG.get("ollama_timeout", 20)))
except (TypeError, ValueError):
    OLLAMA_TIMEOUT = 20
try:
    OLLAMA_NUM_PREDICT = int(APP_CONFIG.get("ollama_num_predict", 220))
except (TypeError, ValueError):
    OLLAMA_NUM_PREDICT = 220

# ── Gemini setup ─────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
gemini_available = False
model = None
if GEMINI_API_KEY and LLM_PROVIDER == "gemini":
    try:
        import google.generativeai as genai

        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)
        gemini_available = True
        print("[INFO] Gemini model initialized successfully.")
    except Exception as e:
        print(f"[WARN] Gemini init failed: {e}")

# ── Paths ────────────────────────────────────────────────────
CONSTITUTION_TEXT_PATH = "constitution.txt"
INDEX_BUILD_LOCK = False

# ── PDF Extraction ───────────────────────────────────────────
def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    return text

def save_constitution_text():
    pdf_path = "static/constitution.pdf"
    constitution_text = extract_text_from_pdf(pdf_path)
    with open(CONSTITUTION_TEXT_PATH, "w", encoding="utf-8") as f:
        f.write(constitution_text)
    print("[INFO] Constitution text extracted from PDF.")

# ── Build Hybrid RAG Index ───────────────────────────────────
rag_index = HybridRAGIndex()
doc_store = DocumentCorpusStore()

def build_index():
    global INDEX_BUILD_LOCK
    if INDEX_BUILD_LOCK:
        return
    INDEX_BUILD_LOCK = True
    constitution_pdf_path = "static/constitution.pdf"
    if os.path.exists(constitution_pdf_path):
        if not os.path.exists(CONSTITUTION_TEXT_PATH):
            save_constitution_text()
        with open(CONSTITUTION_TEXT_PATH, "r", encoding="utf-8") as f:
            text = f.read()
        extra_corpus = doc_store.combined_text()
        if extra_corpus.strip():
            text = f"{text}\n\n{extra_corpus}"
        if text.strip():
            rag_index.build(text, chunk_size=2000, overlap=400, domain="general")
    else:
        print("[WARN] Constitution PDF not found at static/constitution.pdf, skipping constitution loading.")


def _topic_from_case_filename(path: Path) -> str:
    stem = re.sub(r"_\d+$", "", path.stem)
    return stem.replace("_", " ").strip().title() or path.stem


def load_case_corpus(case_dir: str | Path, max_files: int | None = None) -> list[dict]:
    """
    Add local judgment text files to the same RAG index as generic case-law
    context. This lets retrieval learn from whatever topics are present in
    case_corpus without hardcoding a new legal domain for each issue.
    """
    case_path = Path(case_dir)
    if not case_path.is_absolute():
        case_path = (Path(__file__).resolve().parents[1] / case_path).resolve()

    report = []
    if not case_path.exists() or not case_path.is_dir():
        print(f"[WARN] case_corpus not found at {case_path}, skipping case-law indexing.")
        return report

    files = sorted(path for path in case_path.glob("*.txt") if path.is_file())
    if max_files is not None and max_files > 0:
        files = files[:max_files]

    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:
            report.append({"file": path.name, "indexed": False, "message": str(exc)})
            continue

        text = re.sub(r"\s+", " ", text).strip()
        if len(text) < 200:
            report.append({"file": path.name, "indexed": False, "message": "too little text"})
            continue

        topic = _topic_from_case_filename(path)
        tagged_text = f"Case topic: {topic}\nSource file: {path.name}\n\n{text}"
        rag_index.build(
            tagged_text,
            chunk_size=2200,
            overlap=350,
            domain="case_law",
            source=topic,
            append=True,
        )
        report.append({"file": path.name, "indexed": True, "topic": topic, "characters": len(text)})

    print(f"[RAG] Case corpus indexed: {sum(1 for item in report if item.get('indexed'))} files from {case_path}")
    return report

try:
    build_index()
    load_legal_corpus(os.path.join(os.path.dirname(__file__), "..", "corpus"), rag_index.build)
    max_case_files = APP_CONFIG.get("case_corpus_max_files", 0)
    try:
        max_case_files = int(max_case_files)
    except (TypeError, ValueError):
        max_case_files = 0
    load_case_corpus(Path(__file__).resolve().parents[1] / "case_corpus", max_files=max_case_files)
except Exception as e:
    print(f"[ERROR] Index build failed: {e}")


# ── Gemini-powered analysis ──────────────────────────────────
def build_prompt(query: str, context_chunks: list, chat_history_text: str, provider: str = "generic", domain: str = "unknown") -> str:
    # Strict RAG grounding: always require context_chunks, enforce template
    if not context_chunks:
        print(f"[DEBUG] build_prompt called with no retrieved chunks | chunks_retrieved=0 | top_chunk_text='' | domain_used={domain}")
        return "No relevant legal information found"

    compact_chunks = context_chunks[:3]
    print(f"[DEBUG] build_prompt | chunks_retrieved={len(compact_chunks)} | top_chunk_text={compact_chunks[0].get('text', '').replace(chr(10), ' ')[:220]!r} | domain_used={domain}")

    context = "\n\n".join(c.get('text', '').strip()[:650] for c in compact_chunks)
    return (
        "You are a legal assistant.\n"
        "Answer ONLY using the provided legal context. Be concise.\n"
        "Do NOT give general advice.\n"
        "If the answer is not present, say: No relevant legal information found.\n\n"
        "LEGAL CONTEXT:\n"
        f"{context}\n\n"
        "QUESTION:\n"
        f"{query}"
    )


def parse_llm_json(raw: str) -> dict | None:
    cleaned = (raw or "").strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.replace("\ufeff", "")

    decoder = json.JSONDecoder()

    def try_load(text: str) -> dict | None:
        if not text:
            return None
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None

    parsed = try_load(cleaned)
    if parsed is not None:
        return parsed

    # If the model wraps JSON with extra text, decode from the first object start.
    for idx, ch in enumerate(cleaned):
        if ch != "{":
            continue
        try:
            candidate, _ = decoder.raw_decode(cleaned[idx:])
            if isinstance(candidate, dict):
                return candidate
        except json.JSONDecodeError:
            continue

    return None


def gemini_analysis(query: str, context_chunks: list, chat_history_text: str, domain: str) -> dict | None:
    """Call Gemini and ask for a structured JSON response."""
    if not gemini_available or model is None:
        return None

    prompt = build_prompt(query, context_chunks, chat_history_text, provider="gemini", domain=domain)

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=2048,
            ),
        )
        raw = response.text.strip()
        parsed = parse_llm_json(raw)
        if parsed is None:
            print(f"[WARN] Gemini JSON parse error. Raw: {raw[:300]}")
        return parsed
    except Exception as e:
        print(f"[WARN] Gemini API error: {e}")
        return None


def ollama_analysis(query: str, context_chunks: list, chat_history_text: str, domain: str) -> dict | None:
    """Call Ollama and ask for a structured JSON response."""
    url = OLLAMA_HOST.rstrip("/") + "/api/generate"

    def run_ollama(prompt: str, num_predict: int, timeout: int) -> dict | None:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "keep_alive": "10m",
        }
        if num_predict > 0:
            payload["options"] = {"num_predict": min(num_predict, 220), "temperature": 0.1}
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        raw = (data.get("response") or "").strip()
        parsed = parse_llm_json(raw)
        if parsed is None:
            print(f"[WARN] Ollama JSON parse error. Raw: {raw[:300]}")
        return parsed

    prompt = build_prompt(query, context_chunks[:3], chat_history_text[-500:], provider="ollama", domain=domain)
    try:
        return run_ollama(prompt, min(OLLAMA_NUM_PREDICT, 220), min(OLLAMA_TIMEOUT, 20))
    except (TimeoutError, socket.timeout):
        print("[WARN] Ollama timed out; using retrieval fallback.")
        return None
    except urllib.error.URLError as e:
        print(f"[WARN] Ollama connection error: {e}")
        return None
    except Exception as e:
        print(f"[WARN] Ollama error: {e}")
        return None


def generate_answer(query: str, chunks: list, chat_history_text: str, domain: str = "unknown") -> dict | str | None:
    """Route LLM generation based on config."""
    # Strict RAG grounding: never call LLM if no chunks
    if not chunks:
        return "No relevant legal information found"

    # Debug logging for RAG pipeline
    print("[RAG DEBUG] Detected domain:", domain)
    print("[RAG DEBUG] Number of chunks retrieved:", len(chunks))
    if chunks:
        print("[RAG DEBUG] Top chunk (first 300 chars):", chunks[0].get('text', '')[:300].replace('\n', ' '))

    # Build prompt and print it before LLM call
    if LLM_PROVIDER == "ollama":
        return ollama_analysis(query, chunks, chat_history_text, domain)
    if LLM_PROVIDER == "gemini":
        return gemini_analysis(query, chunks, chat_history_text, domain)
    print(f"[WARN] Unknown llm_provider: {LLM_PROVIDER}")
    return None


def infer_domain(query: str, legal_topics: list[str]) -> str:
    q = query.lower()
    if "consumer" in q or "warranty" in q or "refund" in q or "defect" in q:
        return "consumer"
    if any(k in q for k in ["landlord", "tenant", "property", "eviction"]):
        return "property"
    if any(k in q for k in ["divorce", "marriage", "custody", "dowry"]):
        return "family"
    if any(k in q for k in ["wages", "salary", "employee", "labour", "worker"]):
        return "labour"
    if any(t in legal_topics for t in ["right to equality", "right to freedom", "right to education", "police brutality / unlawful arrest"]):
        return "constitutional"
    return "other"


DOMAIN_ALIASES = {
    "property": "tenant",
    "family": "domestic_violence",
}


DOMAIN_PROFILES = {
    "consumer": {
        "case_type": "Consumer Warranty / Deficiency in Service",
        "forum": "District Consumer Disputes Redressal Commission",
        "opposite_party": "Seller, manufacturer, service centre, or platform",
        "signal": "Send written complaint and preserve proof",
        "limits": [
            "Claims usually need bills, warranty terms, service requests, and proof of defect.",
            "Limitation is generally 2 years from cause of action, subject to condonation rules.",
            "Relief depends on product value, defect proof, and company response history.",
        ],
        "evidence": [
            "Invoice or order confirmation",
            "Warranty card or warranty terms",
            "Photos/videos showing the defect",
            "Emails, complaint tickets, call logs, and service centre reports",
            "Refund/replacement denial or non-response proof",
        ],
        "do": [
            "Send a written complaint or legal notice with dates and invoice details.",
            "Preserve the defective product and all service records.",
            "File online or before the District Consumer Commission if the company ignores you.",
        ],
        "avoid": [
            "Do not rely only on phone calls; follow up in writing.",
            "Do not discard the defective product before inspection.",
            "Do not accept a partial settlement without written terms.",
        ],
        "followups": ["Draft a consumer notice", "What evidence should I attach?", "Where do I file my complaint?"],
    },
    "labour": {
        "case_type": "Employment / Wage Dispute",
        "forum": "Labour Commissioner, Labour Court, or Industrial Tribunal",
        "opposite_party": "Employer, contractor, HR department, or establishment",
        "signal": "Document employment and unpaid dues",
        "limits": [
            "Employee status, appointment terms, and state labour rules can change the remedy.",
            "Limitation and forum can vary by type of claim and whether the worker is covered by industrial law.",
            "Verbal promises are weaker unless supported by messages, salary slips, or attendance records.",
        ],
        "evidence": [
            "Appointment letter, contract, ID card, or joining proof",
            "Salary slips, bank statements, attendance records",
            "Termination notice, emails, HR messages, or warning letters",
            "Proof of unpaid wages, overtime, PF, ESI, or bonus",
        ],
        "do": [
            "Calculate exact unpaid amount with dates and supporting records.",
            "Send a written demand to the employer before escalating.",
            "Approach the Labour Commissioner or appropriate labour forum.",
        ],
        "avoid": [
            "Do not resign or sign settlement papers without reading them.",
            "Do not delete workplace chats or attendance proof.",
            "Do not delay if termination or wages are time-sensitive.",
        ],
        "followups": ["Draft salary demand notice", "Which labour office should I approach?", "What proof is needed?"],
    },
    "tenant": {
        "case_type": "Tenant / Landlord Dispute",
        "forum": "Rent authority, civil court, or local tenancy forum",
        "opposite_party": "Landlord, tenant, broker, society, or property manager",
        "signal": "Check agreement, notice, and possession proof",
        "limits": [
            "Rent control protection depends on state law, premises type, and agreement terms.",
            "Commercial premises and residential premises can follow different rules.",
            "Illegal eviction claims need possession proof and notice history.",
        ],
        "evidence": [
            "Rent agreement or lease deed",
            "Rent receipts, bank transfers, and deposit proof",
            "Eviction notice or landlord messages",
            "Photos, utility bills, police complaint, and possession proof",
        ],
        "do": [
            "Keep paying rent through traceable mode if legally advisable.",
            "Reply to notices in writing and preserve possession proof.",
            "Seek injunction or authority intervention if forceful eviction is threatened.",
        ],
        "avoid": [
            "Do not vacate without documenting deposit and handover terms.",
            "Do not rely only on oral promises about deposit return.",
            "Do not change locks or escalate physically.",
        ],
        "followups": ["Draft reply to eviction notice", "Can landlord keep my deposit?", "How do I stop forceful eviction?"],
    },
    "domestic_violence": {
        "case_type": "Domestic Violence / Family Protection",
        "forum": "Protection Officer, Magistrate Court, police, or DLSA",
        "opposite_party": "Husband, in-laws, partner, or household member",
        "signal": "Prioritize immediate safety",
        "limits": [
            "Emergency safety and shelter should be handled before long-term legal strategy.",
            "Relief depends on relationship, shared household, incident proof, and urgency.",
            "Criminal complaints and civil protection remedies can move in parallel.",
        ],
        "evidence": [
            "Medical records, injury photos, and incident diary",
            "Messages, call recordings where lawful, witness details",
            "Marriage/residence proof and shared household documents",
            "Police complaints or prior protection requests",
        ],
        "do": [
            "Contact police or emergency support if there is immediate danger.",
            "Approach a Protection Officer or Magistrate for protection/residence orders.",
            "Keep copies of medical and communication evidence safely.",
        ],
        "avoid": [
            "Do not confront the abuser alone if safety is at risk.",
            "Do not share your location or legal plan with unsafe people.",
            "Do not delay medical documentation after violence.",
        ],
        "followups": ["How do I get a protection order?", "Draft a safety plan", "What evidence helps domestic violence cases?"],
    },
    "constitutional": {
        "case_type": "Constitutional Rights Issue",
        "forum": "High Court, Supreme Court, Human Rights Commission, or relevant authority",
        "opposite_party": "State authority, public body, police, school, or institution",
        "signal": "Identify violated fundamental right",
        "limits": [
            "Writ remedies need state action or public-law element in many situations.",
            "Private disputes may require a statutory forum instead of writ court.",
            "Urgent liberty matters need immediate legal representation.",
        ],
        "evidence": [
            "Order, notice, FIR, school/authority communication",
            "Identity documents and timeline of events",
            "Witness details, photos/videos, and complaint acknowledgements",
        ],
        "do": [
            "Identify the authority involved and preserve the written order or communication.",
            "Send a representation or complaint where appropriate.",
            "Approach DLSA or a lawyer for writ/complaint strategy if rights are violated.",
        ],
        "avoid": [
            "Do not miss short deadlines for bail, appeal, or representation.",
            "Do not rely on social media posts as a substitute for formal complaint.",
        ],
        "followups": ["Which fundamental right applies?", "Draft a representation", "Can I file a writ petition?"],
    },
}


def canonical_domain(domain: str | None) -> str | None:
    if not domain:
        return domain
    return DOMAIN_ALIASES.get(domain, domain)


def _chunk_key(chunk: dict) -> tuple:
    meta = chunk.get("metadata", {})
    return (
        meta.get("source", ""),
        chunk.get("title", ""),
        chunk.get("text", "")[:120],
    )


def retrieve_context(query: str, domain_filter: str | None, manual_domain: bool = False, top_k: int = 5) -> list[dict]:
    """
    Retrieve from the whole learned corpus, using domain filtering only as a
    boost/hint. This prevents the small statutory classifier from hiding better
    matches in case_corpus or uploaded documents.
    """
    candidates = []

    if domain_filter:
        try:
            candidates.extend(rag_index.retrieve(query, top_k=top_k, domain_filter=domain_filter))
        except Exception as exc:
            print(f"[WARN] Domain retrieval failed for {domain_filter}: {exc}")

    if not manual_domain:
        try:
            candidates.extend(rag_index.retrieve(query, top_k=top_k, domain_filter=None))
        except Exception as exc:
            print(f"[WARN] Global retrieval failed: {exc}")

    unique = {}
    for chunk in candidates:
        key = _chunk_key(chunk)
        previous = unique.get(key)
        if previous is None or chunk.get("score", 0) > previous.get("score", 0):
            unique[key] = chunk

    ranked = sorted(unique.values(), key=lambda c: c.get("score", 0), reverse=True)
    return ranked[:top_k]


def retrieval_is_reliable(chunks: list[dict]) -> bool:
    if not chunks:
        return False
    top = chunks[0]
    matched = top.get("score_breakdown", {}).get("matched_terms", [])
    return float(top.get("score") or 0) >= 2.5 and len(matched) >= 2


def confidence_from_retrieval(domain: str, chunks: list[dict], classification: dict, legal_topics: list[str]) -> int:
    if not chunks:
        if classification.get("domain") and DOMAIN_PROFILES.get(canonical_domain(classification.get("domain"))):
            return {"high": 72, "medium": 62, "low": 52, "manual": 70}.get(str(classification.get("confidence")), 55)
        return 18
    top_score = float(chunks[0].get("score") or 0)
    matched_terms = []
    for chunk in chunks:
        matched_terms.extend(chunk.get("score_breakdown", {}).get("matched_terms", []))
    unique_terms = len(set(matched_terms))
    source_count = len(set(c.get("metadata", {}).get("source", "") for c in chunks))

    score_points = min(35, int(top_score * 3))
    term_points = min(20, unique_terms * 4)
    source_points = min(10, source_count * 5)
    domain_points = 0
    if classification.get("domain"):
        domain_points = {"high": 20, "medium": 14, "low": 8}.get(str(classification.get("confidence")), 10)
    elif domain not in ("other", None):
        domain_points = 8
    topic_points = min(10, len(legal_topics) * 3)
    confidence = 20 + score_points + term_points + source_points + domain_points + topic_points
    return max(22, min(92, confidence))


def query_excerpt(query: str, limit: int = 110) -> str:
    clean = " ".join(query.split())
    return clean if len(clean) <= limit else clean[: limit - 3].rstrip() + "..."


def extract_statute_mentions(chunks: list[dict], query: str = "") -> list[dict]:
    """
    Pull statute names and nearby section references from retrieved text. This is
    intentionally generic: when the corpus mentions a law, the UI can cite that
    law instead of treating the enclosing case topic as the applicable statute.
    """
    aliases = {
        "mv act": "Motor Vehicles Act, 1988",
        "motor vehicles act": "Motor Vehicles Act, 1988",
        "consumer protection act": "Consumer Protection Act",
        "code of civil procedure": "Code of Civil Procedure",
        "criminal procedure code": "Code of Criminal Procedure",
        "indian penal code": "Indian Penal Code",
    }
    law_pattern = re.compile(
        r"\b(MV Act|Motor Vehicles [Aa]ct(?:,\s*\d{4})?|Consumer Protection [Aa]ct(?:,\s*\d{4})?|Code of Civil Procedure|Criminal Procedure Code|Indian Penal Code|[A-Z][A-Za-z&().-]*(?:\s+[A-Z][A-Za-z&().-]*){0,8}\s+[Aa]ct(?:,\s*\d{4})?)\b"
    )
    section_pattern = re.compile(r"\b(?:Section|Sec\.?|S\.)\s*(\d+[A-Z]?(?:\(\d+\))?)", flags=re.IGNORECASE)

    found = {}
    query_terms = set(tokenize(query))
    for chunk in chunks:
        text = chunk.get("text", "")
        source = chunk.get("metadata", {}).get("source", "Retrieved corpus")
        for match in law_pattern.finditer(text):
            raw = re.sub(r"\s+", " ", match.group(1)).strip(" .,;:")
            key = raw.lower()
            name = aliases.get(key, raw)
            if name.lower().startswith("of the "):
                name = name[7:]
            if name.lower() in {"an act", "the act", "this act", "that act", "act"}:
                continue
            if len(name) < 6:
                continue
            window = text[max(0, match.start() - 500): match.end() + 500]
            citations = [f"Section {n}" for n in section_pattern.findall(window)]
            name_terms = set(tokenize(name))
            if not citations and query_terms and not (name_terms & query_terms):
                continue
            item = found.setdefault(name, {
                "name": name,
                "type": "retrieved",
                "why_it_applies": f"Mentioned in retrieved legal context from {source}.",
                "citations": [],
                "_score": 0,
            })
            item["_score"] += len(query_terms & (set(tokenize(window)) | name_terms)) + (2 if citations else 0)
            for citation in citations[:4]:
                if citation not in item["citations"]:
                    item["citations"].append(citation)

    ranked = sorted(found.values(), key=lambda item: item.get("_score", 0), reverse=True)
    for item in ranked:
        item.pop("_score", None)
    return ranked[:5]


def build_structured_fallback(query: str, legal_topics: list[str], rights: list[str], next_steps: list[str],
                              chunks: list[dict], meta: dict, disclaimer: str) -> dict:
    article_nums = []
    for c in chunks:
        article_nums.extend(c.get("article_numbers", []))
    article_nums = list(dict.fromkeys(article_nums))[:6]
    sources = list(dict.fromkeys(
        c.get("metadata", {}).get("source", "Retrieved legal corpus") for c in chunks
    ))
    corpus_used = ", ".join(sources) if sources else "No close indexed source"

    domain = canonical_domain(meta.get("domain")) or "other"
    profile = DOMAIN_PROFILES.get(domain, {})
    topic_case_type = f"{legal_topics[0].title()} Query" if legal_topics else None
    case_type = profile.get("case_type") or meta.get("case_type") or topic_case_type or "Legal Query"

    laws = []
    statute_mentions = extract_statute_mentions(chunks, query)
    if statute_mentions:
        laws.extend(statute_mentions)
    elif article_nums and meta.get("domain") == "constitutional":
        laws.append({
            "name": "Constitution of India",
            "type": "primary",
            "why_it_applies": "Retrieved from constitutional context based on your query.",
            "citations": [f"Article {n}" for n in article_nums],
        })
    elif sources:
        laws.append({
            "name": sources[0],
            "type": "primary",
            "why_it_applies": f"Retrieved because your facts match {domain.replace('_', ' ')} signals and source language.",
            "citations": sources[:3],
        })
    elif profile.get("laws"):
        laws.extend(profile["laws"])

    matched_terms = []
    for chunk in chunks:
        matched_terms.extend(chunk.get("score_breakdown", {}).get("matched_terms", []))
    matched_terms = list(dict.fromkeys(matched_terms))[:8]
    term_text = ", ".join(matched_terms) if matched_terms else "your facts"

    if chunks:
        short_explanation = (
            f"Your query appears to be a {case_type.lower()} because it mentions {term_text}. "
            f"The strongest available corpus match is {corpus_used}. "
            "The steps below are tailored to that issue and the retrieved legal source."
        )
    else:
        short_explanation = (
            f"Your query appears to be a {case_type.lower()} based on the facts you described. "
            "The current indexed corpus does not contain a close source match for this domain, "
            "so the brief uses the built-in legal workflow for this issue instead of citing an unrelated act."
        )

    return {
        "meta": {**meta, "domain": domain, "case_type": case_type},
        "summary": {
            "one_line": f"{case_type}: {query_excerpt(query)}",
            "signal": profile.get("signal") or ("Act promptly" if meta.get("confidence", 0) >= 70 else "Verify facts and forum"),
        },
        "plain_words": {"short_explanation": short_explanation},
        "parties": {
            "complainant": "You (the user)",
            "opposite_party": profile.get("opposite_party", "Relevant authority or opposite party"),
            "subject": query[:120],
            "forum": profile.get("forum", "Relevant authority, commission, or court"),
        },
        "applicable_laws": laws,
        "rights_vs_limits": {
            "rights": rights[:6],
            "limits": profile.get("limits", [
                "This is informational guidance only.",
                "Specific legal advice requires a qualified lawyer.",
            ]),
        },
        "steps": [
            {
                "step_no": i + 1,
                "timeframe": f"Day {i + 1}-{i + 2}",
                "action": s,
                "why": f"This step fits a {case_type.lower()} and helps preserve proof or move the matter to the right forum.",
                "urgency_tag": "Action",
            }
            for i, s in enumerate(next_steps[:5])
        ],
        "forum_comparison": {"forums": [], "rows": []},
        "relief_spectrum": [],
        "case_strength": [
            {
                "label": "Domain fit",
                "score": meta.get("confidence", 0) if not chunks else min(100, int((chunks[0].get("score", 0) if chunks else 0) * 8)),
                "note": f"Top source: {sources[0] if sources else 'No close indexed source; using domain workflow'}",
            },
            {
                "label": "Fact specificity",
                "score": min(100, 35 + len(query.split()) * 2),
                "note": "More dates, documents, amounts, and opposite-party details improve reliability.",
            },
            {
                "label": "Evidence readiness",
                "score": 65 if any(k in query.lower() for k in ["bill", "invoice", "notice", "email", "proof", "receipt", "salary", "agreement", "fir"]) else 42,
                "note": "The score improves if you already have written proof.",
            },
        ],
        "cost_benefit": {"invest": [], "recover": []},
        "clause_risks": [],
        "evidence_checklist": profile.get("evidence", ["Relevant documents", "Receipts, notices, or records"]),
        "do_and_avoid": {
            "do": profile.get("do", ["Keep written records", "Document key dates"]),
            "avoid": profile.get("avoid", ["Relying only on verbal communication"]),
        },
        "misconceptions": [],
        "similar_cases": [],
        "sources": {
            "corpus_used": corpus_used,
            "chunks_retrieved": len(chunks),
        },
        "followups": profile.get("followups", ["Draft a formal notice", "Prepare a complaint summary"]),
        "disclaimer": disclaimer,
    }


def deep_merge(base: dict, update: dict) -> dict:
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = deep_merge(base[key], value)
        elif value not in (None, "", [], {}):
            base[key] = value
    return base


def build_compliance_response(query: str, business_type: str, employee_count: int, checklist: list[dict]) -> dict:
    """Build a frontend-compatible response for compliance monitor mode."""
    answer = format_checklist_output(checklist, business_type, employee_count)
    sources = list(dict.fromkeys(source for item in checklist for source in item.get("sources", [])))
    complete_count = sum(1 for item in checklist if item.get("status") == "applicable")
    total_count = len(checklist)

    steps = [
        {
            "step_no": idx + 1,
            "timeframe": "Review",
            "action": f"{item.get('status_symbol', '-')} {item['act']}",
            "why": item.get("requirement_summary", ""),
            "urgency_tag": item.get("status", "needs_review"),
        }
        for idx, item in enumerate(checklist)
    ]

    summary = (
        f"Compliance checklist prepared for {business_type.replace('_', ' ')} "
        f"with {employee_count} employees."
    )

    return {
        "query": query,
        "ai_powered": False,
        "urgency": {
            "level": "STANDARD",
            "color": "#10b981",
            "message": "Compliance review checklist",
        },
        "case_type": "Compliance Monitor",
        "summary": summary,
        "analysis": answer,
        "key_points": [
            f"{total_count} applicable acts identified.",
            f"{complete_count} acts have matching indexed source context.",
            "Items marked with x need manual verification or additional corpus coverage.",
        ],
        "is_follow_up": False,
        "legal_topics": ["business compliance", business_type.replace("_", " ")],
        "articles_cited": [],
        "your_rights": [],
        "next_steps": [f"{item.get('status_symbol', '-')} {item['act']}: {item['requirement_summary']}" for item in checklist],
        "retrieved_sections": [],
        "structured": {
            "meta": {
                "domain": "compliance",
                "case_type": "Compliance Monitor",
                "confidence": 85,
                "in_scope": True,
                "ai_powered": False,
                "llm_provider": LLM_PROVIDER,
            },
            "summary": {
                "one_line": summary,
                "signal": "Verify checklist items",
            },
            "plain_words": {
                "short_explanation": "The compliance monitor maps the business type and employee count to likely applicable acts, then retrieves matching indexed sections where available.",
            },
            "parties": {
                "complainant": "Business owner",
                "opposite_party": "Regulators / authorities",
                "subject": query,
                "forum": "Relevant labour, municipal, food safety, and consumer authorities",
            },
            "applicable_laws": [
                {
                    "name": item["act"],
                    "type": "compliance",
                    "why_it_applies": item.get("requirement_summary", ""),
                    "citations": item.get("sources", []),
                }
                for item in checklist
            ],
            "rights_vs_limits": {
                "rights": [],
                "limits": [
                    "This checklist identifies likely requirements; final applicability can depend on state rules, registrations, and exact business facts.",
                ],
            },
            "steps": steps,
            "evidence_checklist": [
                "Employee count records",
                "Wage register and salary slips",
                "Business registration/license documents",
                "Food safety registration if food is served",
            ],
            "do_and_avoid": {
                "do": ["Verify each applicable act with current state rules", "Keep wage and attendance records updated"],
                "avoid": ["Treating this checklist as a final legal audit"],
            },
            "sources": {
                "corpus_used": ", ".join(sources) if sources else "No matching indexed source found",
                "chunks_retrieved": complete_count,
            },
            "compliance_checklist": checklist,
            "followups": ["Show labour compliance only", "Explain Shops Act requirements"],
            "disclaimer": "This is an informational compliance checklist, not legal advice.",
        },
        "explainability": {
            "detected_domain": "compliance",
            "confidence": "high",
            "matched_keywords": [business_type, str(employee_count)],
            "number_of_chunks_used": complete_count,
            "source_documents": sources,
            "short_explanation": "Business type and employee count triggered compliance monitor mode.",
            "retrieval_details": [
                {
                    "act": item["act"],
                    "domain": item.get("domain"),
                    "status": item.get("status"),
                    "sources": item.get("sources", []),
                }
                for item in checklist
            ],
        },
        "disclaimer": "This is an informational compliance checklist, not legal advice.",
    }


# ── Fallback analysis (no Gemini) ────────────────────────────
def fallback_analysis(query: str, chunks: list) -> dict:
    """Produce a structured response purely from RAG-retrieved chunks."""
    corpus_used = "Retrieved legal corpus"
    if chunks:
        sources = [
            c.get("metadata", {}).get("source")
            for c in chunks
            if c.get("metadata", {}).get("source")
        ]
        if sources:
            corpus_used = ", ".join(list(dict.fromkeys(sources))[:3])

    article_nums = []
    for c in chunks:
        article_nums.extend(c.get("article_numbers", []))
    article_nums = list(dict.fromkeys(article_nums))[:6]

    applicable_articles = []
    for c in chunks:
        for num in c.get("article_numbers", [])[:2]:
            # Try to extract article title from the chunk
            title_match = re.search(
                rf'Article\s+{re.escape(num)}\s*[-–—.]?\s*([^\n]{{0,80}})', c["text"]
            )
            title = title_match.group(1).strip() if title_match else c["title"]
            applicable_articles.append({
                "number": f"Article {num}",
                "title": title[:80],
                "relevance": "Retrieved as relevant to your query from the Constitution of India."
            })

    if not applicable_articles and chunks:
        applicable_articles = [{"number": "N/A", "title": chunks[0]["title"], "relevance": "Most relevant section found."}]

    # Extract key sentences from chunks
    key_points = []
    for chunk in chunks[:3]:
        sentences = re.split(r'(?<=[.!?])\s+', chunk["text"])
        for sent in sentences[:2]:
            sent = sent.strip()
            if len(sent) > 40:
                key_points.append(sent[:200])

    return {
        "summary": f"Based on your query about \"{query[:100]}\", relevant sections from {corpus_used} have been retrieved. AI-powered analysis is temporarily unavailable, but grounded source text is shown below.",
        "analysis": f"The following retrieved legal sections from {corpus_used} are relevant to your situation. Please review the source text and consult a qualified legal professional for advice on your facts.",
        "key_points": key_points[:5] if key_points else ["Please review the retrieved constitutional articles below."],
        "applicable_articles": applicable_articles[:5],
        "case_type": "Legal Corpus Query",
        "is_follow_up": False,
        "fallback": True,
    }


# ── Main endpoint ────────────────────────────────────────────
@app.route('/legal-help', methods=['POST'])
def legal_help():
    data = request.json
    if not data or "query" not in data:
        return jsonify({"error": "Missing 'query' in request body"}), 400

    query: str = data["query"].strip()
    if not query:
        return jsonify({"error": "Query cannot be empty"}), 400

    if is_comparison_query(query):
        return jsonify(build_comparison_response(query))

    business_info = parse_business_input(query)
    if business_info.get("business_type") and business_info.get("employee_count") is not None:
        checklist = generate_compliance_checklist(
            business_info["business_type"],
            business_info["employee_count"],
            rag_index.retrieve,
        )
        return jsonify(build_compliance_response(
            query,
            business_info["business_type"],
            business_info["employee_count"],
            checklist,
        ))

    chat_history_list = data.get("chat_history", [])
    chat_history_text = ""
    if chat_history_list:
        for msg in chat_history_list[-6:]:  # last 3 exchanges
            role = "User" if msg.get("role") == "user" else "Assistant"
            chat_history_text += f"{role}: {msg.get('text', '')[:500]}\n\n"

    # 1. Domain-aware retrieval
    domain_override = data.get("domain")
    manual_domain = bool(domain_override and domain_override != "auto")
    if domain_override and domain_override != "auto":
        domain_filter = canonical_domain(domain_override)
        classification = {
            "domain": domain_filter,
            "confidence": "manual",
            "matched_keywords": ["manual override"]
        }
        print(f"Manual domain override: {domain_filter}")
    else:
        classification = situation_classifier(query)
        domain_filter = canonical_domain(classification["domain"])
        classification["domain"] = domain_filter
        if classification.get("confidence") not in ("medium", "high"):
            domain_filter = None
        if domain_filter is not None:
            print(f"Detected domain: {domain_filter} (confidence: {classification['confidence']}) — matched: {classification['matched_keywords']}")
        else:
            print("No specific domain detected — searching all documents")

    try:
        chunks = retrieve_context(query, domain_filter=domain_filter, manual_domain=manual_domain, top_k=5)
    except Exception as e:
        print(f"[ERROR] Retrieval failed: {e}")
        chunks = []

    retrieval_ok = retrieval_is_reliable(chunks)
    if not retrieval_ok:
        print("[RAG] Weak retrieval match; suppressing chunks to avoid unrelated legal sources.")
        chunks = []

    # 2. Extract supporting metadata. Keep query-intent topics first so broad
    # retrieved chunks cannot relabel the user's issue.
    query_topics = extract_legal_keywords(query, [])
    retrieved_topics = extract_legal_keywords(query, chunks)
    legal_keywords = list(dict.fromkeys(query_topics + retrieved_topics))
    rights, next_steps = get_rights_and_steps(query)
    urgency = assess_urgency(query)

    top_score = chunks[0]["score"] if chunks else 0
    top_matched = 0
    if chunks and chunks[0].get("score_breakdown"):
        top_matched = len(chunks[0]["score_breakdown"].get("matched_terms", []))
    domain = canonical_domain(domain_filter or infer_domain(query, query_topics or legal_keywords))
    in_scope = retrieval_ok
    confidence = confidence_from_retrieval(domain, chunks, classification, legal_keywords)

    # 3. AI generation (provider or fallback)
    ai_result = None
    # Strict RAG grounding: never call LLM if no chunks, always use prompt template
    if chunks:
        ai_result = generate_answer(query, chunks, chat_history_text, domain)
    else:
        ai_result = "No relevant legal information found"

    if isinstance(ai_result, str):
        if ai_result == "No relevant legal information found":
            ai_powered = False
        else:
            ai_powered = False
        ai_result = {
            "analysis": ai_result,
            "summary": ai_result,
            "key_points": [],
            "is_follow_up": False,
        }
    elif ai_result is None:
        ai_result = fallback_analysis(query, chunks)
        ai_powered = False
    else:
        ai_powered = True

    # 4. Build article references from both AI output and RAG
    article_refs = ai_result.get("applicable_articles", [])

    # 5. Build retrieved sections for display
    retrieved_sections = [
        {
            "title": c["title"],
            "excerpt": c["text"][:800],
            "score": c["score"],
            "article_numbers": c["article_numbers"],
            "score_breakdown": c.get("score_breakdown"),
            "metadata": c.get("metadata", {}),
        }
        for c in chunks
    ]

    meta = {
        "domain": domain,
        "case_type": (
            ai_result.get("case_type")
            if ai_powered and ai_result.get("case_type")
            else DOMAIN_PROFILES.get(domain, {}).get(
                "case_type",
                f"{(query_topics or legal_keywords)[0].title()} Query" if (query_topics or legal_keywords) else "Legal Query",
            )
        ),
        "confidence": confidence,
        "in_scope": in_scope,
        "ai_powered": ai_powered,
        "llm_provider": LLM_PROVIDER,
    }

    structured = build_structured_fallback(
        query,
        legal_keywords,
        rights,
        next_steps,
        chunks,
        meta,
        "This is AI-generated legal information for educational purposes only. It does not constitute legal advice. Please consult a qualified lawyer for your specific situation.",
    )
    case_type = meta["case_type"]
    if isinstance(ai_result, dict) and "meta" in ai_result:
        structured = deep_merge(structured, ai_result)
        case_type = ai_result.get("meta", {}).get("case_type") or case_type
    structured["meta"] = {**meta, "case_type": case_type}

    has_structured = isinstance(ai_result, dict) and "meta" in ai_result
    summary_text = structured.get("summary", {}).get("one_line", "") or ai_result.get("summary", "")
    analysis_text = ai_result.get("analysis", "")
    if not analysis_text or analysis_text == "No relevant legal information found" or ai_result.get("fallback"):
        analysis_text = structured.get("plain_words", {}).get("short_explanation", "")
    rights_points = structured.get("rights_vs_limits", {}).get("rights", [])
    limits_points = structured.get("rights_vs_limits", {}).get("limits", [])
    key_points = ai_result.get("key_points", [])
    if not key_points:
        key_points = rights_points[:3] + limits_points[:2]

    if not article_refs and structured.get("applicable_laws"):
        derived = []
        for law in structured.get("applicable_laws", []):
            for citation in law.get("citations", [])[:2]:
                derived.append({
                    "number": citation,
                    "title": law.get("name", ""),
                    "relevance": law.get("why_it_applies", ""),
                })
        article_refs = derived

    # Explainability metadata

    retrieval_details = []
    for c in chunks:
        score_breakdown = c.get("score_breakdown", {})
        retrieval_details.append({
            "text_preview": c.get("text", "")[:150],
            "domain": c.get("metadata", {}).get("domain", "unknown"),
            "score": {
                "bm25": score_breakdown.get("bm25"),
                "cosine": score_breakdown.get("cosine"),
                "hybrid": score_breakdown.get("hybrid"),
            }
        })

    explainability = {
        "detected_domain": classification.get("domain"),
        "confidence": classification.get("confidence"),
        "matched_keywords": classification.get("matched_keywords", []),
        "number_of_chunks_used": len(chunks),
        "source_documents": list(dict.fromkeys(
            c.get("metadata", {}).get("source", "Unknown source") for c in chunks
        )),
        "short_explanation": f"Domain '{classification.get('domain')}' was selected because the following keywords matched: {', '.join(classification.get('matched_keywords', [])) or 'none found'}.",
        "retrieval_details": retrieval_details,
    }

    response = {
        "query": query,
        "ai_powered": ai_powered,
        "urgency": urgency,
        "case_type": meta["case_type"],
        "summary": summary_text or ai_result.get("summary", ""),
        "analysis": analysis_text or ai_result.get("analysis", ""),
        "key_points": key_points or ai_result.get("key_points", []),
        "is_follow_up": ai_result.get("is_follow_up", False),
        "legal_topics": legal_keywords,
        "articles_cited": article_refs,
        "your_rights": rights,
        "next_steps": next_steps,
        "retrieved_sections": retrieved_sections,
        "structured": structured,
        "explainability": explainability,
        "disclaimer": "This is AI-generated legal information for educational purposes only. It does not constitute legal advice. Please consult a qualified lawyer for your specific situation.",
    }
    return jsonify(response)


def test_rights_module():
    """
    Run basic integration tests for rights module retrieval modes.
    """
    corpus_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "corpus"))
    load_legal_corpus(corpus_path, rag_index.build)

    tests = [
        {
            "mode": "situation",
            "query": "My employer fired me without notice and hasn't paid my last month salary",
        },
        {
            "mode": "compliance",
            "query": "I run a restaurant with 12 employees in Maharashtra",
        },
        {
            "mode": "direct",
            "query": "What are my fundamental rights under the Indian constitution?",
        },
    ]

    for test in tests:
        result = handle_rights_query(test["query"], rag_index.retrieve, mode=test["mode"])
        preview = result["answer"] if result["answer"] else ""
        print("Query:", test["query"])
        print("Mode used:", result.get("mode_used"))
        print("Domain detected:", result.get("domain_detected"))
        safe_preview = preview[:300].replace("\n", " ").encode('ascii', 'replace').decode('ascii')
        print("Output preview:", safe_preview)
        print("-" * 80)



def generate_text_report(prompt: str) -> str:
    if LLM_PROVIDER == "gemini" and gemini_available and model is not None:
        try:
            import google.generativeai as genai
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0,
                    max_output_tokens=4096,
                ),
            )
            return (response.text or "").strip()
        except Exception as e:
            print(f"[WARN] Gemini text generation error: {e}")
            return ""

    if LLM_PROVIDER == "ollama":
        url = OLLAMA_HOST.rstrip("/") + "/api/generate"
        import urllib.request, json
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": 4096, "temperature": 0},
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return (data.get("response") or "").strip()
        except Exception as e:
            print(f"[WARN] Ollama text generation error: {e}")
            return ""
    return ""


from routes.advanced_stub_routes import advanced_stub_bp
from routes.amendment_routes import amendment_bp
from routes.chat_routes import chat_bp
from routes.comparator_routes import comparator_bp
from routes.fairness_routes import fairness_bp
from routes.rights_card_routes import rights_card_bp
from routes.scenario_routes import scenario_bp
from routes.translator_routes import translator_bp
from utils.llm_client import configure_llm
from utils.retriever import configure_retriever


configure_retriever(rag_index.retrieve)
configure_llm(generate_text_report if ((LLM_PROVIDER == "ollama") or gemini_available) else None)
app.register_blueprint(fairness_bp)
app.register_blueprint(rights_card_bp)
app.register_blueprint(scenario_bp)
app.register_blueprint(translator_bp)
app.register_blueprint(amendment_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(comparator_bp)
app.register_blueprint(advanced_stub_bp)

@app.route("/document-intel/upload", methods=["POST"])
def upload_document():
    global INDEX_BUILD_LOCK
    if "file" not in request.files:
        return jsonify({"error": "Upload a file in multipart form-data under key 'file'."}), 400

    uploaded = request.files["file"]
    if not uploaded or not uploaded.filename:
        return jsonify({"error": "No file selected."}), 400

    suffix = os.path.splitext(uploaded.filename)[1] or ".bin"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            uploaded.save(tmp.name)
            tmp_path = tmp.name

        text = extract_text(tmp_path)
        if not text.strip():
            return jsonify({"error": "No readable text found in the uploaded document."}), 422

        doc = doc_store.add(uploaded.filename, text)
        INDEX_BUILD_LOCK = False
        build_index()
        return jsonify(
            {
                "status": "ok",
                "doc_id": doc.doc_id,
                "name": doc.name,
                "chars_extracted": len(text),
                "uploaded_docs": doc_store.list_docs(),
                "index_chunks": len(rag_index.chunks),
            }
        )
    except Exception as e:
        return jsonify({"error": f"Document ingestion failed: {e}"}), 500
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

@app.route("/document-intel/summarize", methods=["POST"])
def summarize_document():
    if "file" not in request.files:
        return jsonify({"error": "Upload a file in multipart form-data under key 'file'."}), 400

    uploaded = request.files["file"]
    if not uploaded or not uploaded.filename:
        return jsonify({"error": "No file selected."}), 400

    export_pdf = str(request.form.get("export_pdf", "false")).lower() == "true"
    export_docx = str(request.form.get("export_docx", "false")).lower() == "true"

    suffix = os.path.splitext(uploaded.filename)[1] or ".bin"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            uploaded.save(tmp.name)
            tmp_path = tmp.name

        llm_fn = generate_text_report if ((LLM_PROVIDER == "ollama") or gemini_available) else None
        report = build_legal_document_report(
            file_path=tmp_path,
            filename=uploaded.filename,
            llm_text_fn=llm_fn,
            export_pdf=export_pdf,
            export_docx=export_docx,
        )
        return jsonify(report)
    except Exception as e:
        return jsonify({"error": f"Document summarization failed: {e}"}), 500
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

@app.route("/document-intel/contract-analyze", methods=["POST"])
def contract_analyze():
    data = request.json or {}
    contract_text = (data.get("text") or "").strip()
    if not contract_text:
        return jsonify({"error": "Missing 'text' in request body."}), 400
    return jsonify(analyze_contract(contract_text, rag_index))

@app.route("/document-intel/court-notice-decode", methods=["POST"])
def court_notice_decode():
    data = request.json or {}
    notice_text = (data.get("text") or "").strip()
    if not notice_text:
        return jsonify({"error": "Missing 'text' in request body."}), 400
    return jsonify(decode_court_notice(notice_text, rag_index))


def quick_template_sanitize(text: str) -> str:
    cleaned = re.sub(r"\n?\s*Page\s+\d+\s*(?:of\s+\d+)?\s*\n?", "\n", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"https?://\S+|www\.\S+", "", cleaned)
    cleaned = re.sub(r"_{3,}", "{{blank_field}}", cleaned)
    cleaned = re.sub(r"\[([A-Za-z][A-Za-z0-9 _/-]{2,60})\]", lambda m: "{{" + re.sub(r"[^a-z0-9]+", "_", m.group(1).lower()).strip("_") + "}}", cleaned)
    cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def nyayadraft_template_path(template_name: str):
    safe_name = os.path.basename(str(template_name or ""))
    if not safe_name or safe_name != template_name or not safe_name.lower().endswith(".txt"):
        return None

    template_dir = os.path.abspath(os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "drafting_module", "templates")
    ))
    path = os.path.abspath(os.path.normpath(os.path.join(template_dir, safe_name)))
    if os.path.commonpath([template_dir, path]) != template_dir:
        return None
    return path


@app.route("/nyayadraft/templates", methods=["GET"])
def nyayadraft_templates():
    try:
        from drafting_module.processor import extract_placeholders, list_templates

        templates = []
        for path in list_templates():
            text = path.read_text(encoding="utf-8")
            templates.append(
                {
                    "name": path.name,
                    "title": path.stem.replace("_", " ").title(),
                    "placeholder_count": len(extract_placeholders(text)),
                }
            )
        return jsonify({"templates": templates})
    except Exception as e:
        return jsonify({"error": f"Template listing failed: {e}"}), 500


@app.route("/nyayadraft/ingest-templates", methods=["POST"])
def nyayadraft_ingest_templates():
    try:
        from drafting_module.ingestor import ingest_all_pdfs

        results = ingest_all_pdfs(overwrite=True)
        created = [
            {
                "source_pdf": result.source_pdf.name,
                "output_template": result.output_template.name if result.output_template else None,
                "status": result.status,
                "message": result.message,
                "raw_characters": result.raw_characters,
                "cleaned_characters": result.cleaned_characters,
            }
            for result in results
        ]
        return jsonify(
            {
                "template_count": sum(1 for result in results if result.output_template),
                "results": created,
            }
        )
    except Exception as e:
        return jsonify({"error": f"Template ingestion failed: {e}"}), 500


@app.route("/nyayadraft/templates/<template_name>", methods=["GET"])
def nyayadraft_template(template_name):
    path = nyayadraft_template_path(template_name)
    if path is None or not os.path.exists(path):
        return jsonify({"error": "Template not found."}), 404

    try:
        from drafting_module.processor import extract_placeholders

        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        return jsonify(
            {
                "name": os.path.basename(path),
                "title": os.path.splitext(os.path.basename(path))[0].replace("_", " ").title(),
                "text": text,
                "placeholders": extract_placeholders(text),
            }
        )
    except Exception as e:
        return jsonify({"error": f"Template loading failed: {e}"}), 500


@app.route("/nyayadraft/docx", methods=["POST"])
def nyayadraft_docx():
    data = request.json or {}
    document_text = str(data.get("text") or "").strip()
    title = str(data.get("title") or "NyayaDraft Document").strip()
    if not document_text:
        return jsonify({"error": "Missing 'text' in request body."}), 400

    try:
        from drafting_module.processor import text_to_docx_bytes

        buffer = text_to_docx_bytes(document_text, title=title)
        return send_file(
            buffer,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            as_attachment=True,
            download_name=f"{re.sub(r'[^A-Za-z0-9_-]+', '_', title).strip('_') or 'nyayadraft'} .docx".replace(" .docx", ".docx"),
        )
    except Exception as e:
        return jsonify({"error": f"DOCX generation failed: {e}"}), 500


@app.route("/nyayadraft/sanitize-pdf", methods=["POST"])
def nyayadraft_sanitize_pdf():
    if "file" not in request.files:
        return jsonify({"error": "Upload a PDF under form field 'file'."}), 400

    uploaded = request.files["file"]
    if not uploaded or not uploaded.filename:
        return jsonify({"error": "No PDF selected."}), 400
    if not uploaded.filename.lower().endswith(".pdf"):
        return jsonify({"error": "NyayaDraft sanitizer currently accepts PDF files only."}), 400

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            uploaded.save(tmp.name)
            tmp_path = tmp.name

        text = extract_text(tmp_path)
        if not text.strip():
            return jsonify({"error": "No readable text found in the uploaded PDF."}), 422

        prompt = (
            "Clean this messy legal text extracted from a PDF. "
            "1. Remove page numbers, headers, and website noise. "
            "2. Identify all underscores, blanks, or bracketed text and replace them with descriptive "
            "placeholders in double curly braces, e.g., {{landlord_name}}. "
            "3. Return ONLY the cleaned legal document text.\n\n"
            f"{text[:6500]}"
        )
        sanitized = generate_text_report(prompt).strip() if LLM_PROVIDER == "ollama" else ""
        if not sanitized:
            sanitized = quick_template_sanitize(text)

        placeholders = sorted(set(re.findall(r"\{\{(.*?)\}\}", sanitized)))
        return jsonify(
            {
                "filename": uploaded.filename,
                "chars_extracted": len(text),
                "chars_sanitized": len(sanitized),
                "placeholder_count": len(placeholders),
                "placeholders": placeholders,
                "sanitized_text": sanitized,
            }
        )
    except Exception as e:
        return jsonify({"error": f"PDF sanitization failed: {e}"}), 500
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.route("/judgement-prediction", methods=["POST"])
def judgement_prediction():
    data = request.json or {}
    facts = str(data.get("facts") or data.get("query") or "").strip()
    if not facts:
        return jsonify({"error": "Missing 'facts' in request body."}), 400

    model_name = data.get("model") or APP_CONFIG.get("judgement_model") or OLLAMA_MODEL
    try:
        case_count = int(data.get("case_count") or data.get("top_k") or 5)
    except (TypeError, ValueError):
        case_count = 5
    case_count = max(5, min(20, case_count))
    try:
        result = predict_judgement(
            facts=facts,
            ollama_host=OLLAMA_HOST,
            model=model_name,
            timeout=OLLAMA_TIMEOUT,
            top_k=case_count,
        )
        return jsonify(result)
    except Exception as e:
        print(f"[ERROR] Judgement prediction failed: {e}")
        return jsonify({"error": f"Judgement prediction failed: {e}"}), 500

@app.route("/", methods=["GET"])
def home():
    return jsonify(
        {
            "service": "NyayaSetu Backend API",
            "status": "ok",
            "message": "Backend is running. Open frontend on http://localhost:3000",
            "endpoints": [
                "/health",
                "/legal-help",
                "/judgement-prediction",
                "/nyayadraft/templates",
                "/nyayadraft/ingest-templates",
                "/nyayadraft/templates/<template_name>",
                "/nyayadraft/docx",
                "/nyayadraft/sanitize-pdf",
                "/document-intel/upload",
                "/document-intel/summarize",
                "/document-intel/contract-analyze",
                "/document-intel/court-notice-decode",
                "/api/fairness-check",
                "/api/rights-card",
                "/api/simulate-scenario",
                "/api/translate",
                "/api/amendments",
                "/api/amendments/<article_number>",
                "/api/compare-articles",
                "/api/chat",
                "/api/document-analyzer",
                "/api/petition-draft",
                "/api/landmark-cases?topic=",
                "/api/bail-eligibility",
                "/api/legal-timeline",
            ],
        }
    )
@app.route('/health', methods=['GET'])
def health():
    domain_counts = {}
    for chunk in rag_index.chunks:
        domain = chunk.get("metadata", {}).get("domain", "unknown")
        domain_counts[domain] = domain_counts.get(domain, 0) + 1

    return jsonify({
        "status": "ok",
        "gemini_available": gemini_available,
        "ai_available": (LLM_PROVIDER == "ollama") or gemini_available,
        "llm_provider": LLM_PROVIDER,
        "index_chunks": len(rag_index.chunks),
        "uploaded_docs": len(doc_store.list_docs()),
        "domain_counts": domain_counts,
    })


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5555, debug=True)
