"""
Hybrid RAG Engine for LegalAI
Combines TF-IDF vector similarity + BM25-style keyword scoring for robust retrieval
without depending on external embedding APIs.
"""

import re
import math
from collections import Counter, defaultdict


# ────────────────────────────────────────────────
# Text preprocessing
# ────────────────────────────────────────────────

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "being", "by", "do",
    "for", "from", "has", "have", "he", "her", "him", "his", "how", "i",
    "in", "is", "it", "its", "me", "my", "not", "of", "on", "or", "our",
    "she", "so", "that", "the", "their", "them", "they", "this", "to",
    "up", "us", "was", "we", "were", "what", "when", "where", "which",
    "who", "will", "with", "you", "your", "can", "did", "does", "had",
    "into", "no", "than", "then", "there", "these", "those", "through",
    "under", "upon", "very", "would",
}

LEGAL_SYNONYMS = {
    "accident": ["accident", "injury", "harm", "damage", "negligence", "tort"],
    "police": ["police", "constable", "officer", "fir", "arrest", "custody", "detention"],
    "property": ["property", "land", "immovable", "estate", "ownership", "possession"],
    "worker": ["worker", "labour", "employee", "employment", "wages", "salary", "labourer"],
    "woman": ["woman", "women", "female", "gender", "maternity", "harassment", "sexual"],
    "education": ["education", "school", "right to education", "rte", "child", "student"],
    "arrest": ["arrest", "detention", "custody", "remand", "bail", "fir", "police"],
    "rent": ["rent", "tenant", "landlord", "eviction", "lease", "house"],
    "discrimination": ["discrimination", "equality", "caste", "untouchability", "sc", "st"],
        "consumer": ["consumer", "product", "defect", "fraud", "cheating", "refund", "warranty", "repair", "replacement", "service"],
    "environment": ["environment", "pollution", "forest", "wildlife", "river", "air", "water"],
    "marriage": ["marriage", "divorce", "matrimonial", "dowry", "husband", "wife", "spouse"],
    "death": ["death", "murder", "homicide", "suicide", "accident", "compensation"],
    "tax": ["tax", "income", "revenue", "gst", "vat", "custom", "duty"],
    "loan": ["loan", "debt", "bank", "interest", "mortgage", "recovery", "default"],
}


def tokenize(text: str) -> list[str]:
    """Lowercase, strip punctuation, remove stop words, return tokens."""
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())
    tokens = [w for w in text.split() if w and w not in STOP_WORDS and len(w) > 1]
    return tokens


def expand_query(query: str) -> list[str]:
    """Add legal synonyms to query tokens for better recall."""
    tokens = tokenize(query)
    expanded = list(tokens)
    query_lower = query.lower()
    for key, synonyms in LEGAL_SYNONYMS.items():
        if key in query_lower or any(s in query_lower for s in synonyms[:2]):
            for syn in synonyms:
                expanded.extend(tokenize(syn))
            if key == "education":
                expanded.append("21a")
    if any(k in query_lower for k in ["social media", "post", "tweet", "censorship", "criticised", "criticized"]):
        expanded.extend(["speech", "expression", "freedom"])
    return list(set(expanded))


def _contains_signal(text: str, signal: str) -> bool:
    """Match multi-word signals by phrase and short tokens by word boundary."""
    signal = signal.lower()
    if " " in signal or "-" in signal:
        return signal in text
    return re.search(rf"\b{re.escape(signal)}\b", text) is not None


# ────────────────────────────────────────────────
# Corpus indexing
# ────────────────────────────────────────────────

class HybridRAGIndex:
    """
    Hybrid retrieval index combining:
    1. BM25-style keyword scoring (sparse)
    2. TF-IDF cosine similarity (dense-lite)
    3. Article/section title boosting
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.chunks: list[dict] = []          # [{id, title, text, tokens}]
        self.idf: dict[str, float] = {}
        self.avg_dl: float = 0
        self._built = False

    # ── Build ────────────────────────────────────

    def build(
        self,
        text: str,
        chunk_size: int = 2000,
        overlap: int = 400,
        domain: str = None,
        source: str = None,
        append: bool = False,
    ):
        """
        Split text into overlapping chunks, tag them, and build BM25 + TF-IDF.

        By default this replaces the current index. Use append=True when loading
        additional tagged documents into the same retriever.
        """
        if not append:
            self.chunks = []

        # Skip the table of contents if present by starting from the last PREAMBLE
        # (the first PREAMBLE usually appears in the contents section).
        preamble_matches = list(re.finditer(r"\bPREAMBLE\b", text))
        if preamble_matches:
            text = text[preamble_matches[-1].start():]

        # Try to split on article/section boundaries first
        article_splits = re.split(
            r'(?m)(?=^(?:ARTICLE|Article|PART|Part|SCHEDULE|Schedule)\s+\w+|^(?:\d+\[)?\d{1,3}[A-Z]?\.)',
            text
        )

        raw_chunks = []
        for seg in article_splits:
            if len(seg) > chunk_size:
                # further split large segments with overlap
                for i in range(0, len(seg), chunk_size - overlap):
                    raw_chunks.append(seg[i: i + chunk_size])
            else:
                if seg.strip():
                    raw_chunks.append(seg)

        start_id = len(self.chunks)
        for i, chunk in enumerate(raw_chunks):
            chunk = chunk.strip()
            if not chunk:
                continue
            # Try to extract article/part title
            title_match = re.match(
                r'^((?:ARTICLE|Article|PART|Part|SCHEDULE|Schedule)\s+[\w]+[^\n]*)',
                chunk
            )
            if title_match:
                title = title_match.group(1).strip()
            else:
                # Fallback for numbered article lines like "19.Protection of..."
                num_match = re.match(r'^(?:\d+\[)?(\d{1,3}[A-Z]?)\.\s*([^\n]{0,80})', chunk)
                if num_match:
                    num = num_match.group(1)
                    head = num_match.group(2).strip()
                    if head:
                        if re.search(r"\bSCHEDULE\b", chunk[:120], flags=re.IGNORECASE):
                            title = f"Schedule item {num} - {head}"
                        elif domain and domain != "general":
                            title = f"Section {num} - {head}"
                        else:
                            title = f"Article {num} - {head}"
                    else:
                        title = f"Section {num}" if domain and domain != "general" else f"Article {num}"
                else:
                    title = f"Section {i+1}"

            tokens = tokenize(chunk)
            self.chunks.append({
                "id": start_id + i,
                "title": title,
                "text": chunk,
                "tokens": tokens,
                "tf": Counter(tokens),
                "metadata": {
                    "domain": domain if domain else "general",
                    "source": source if source else "Constitution of India" if domain in (None, "general") else domain,
                },
            })

        # Compute IDF
        N = len(self.chunks)
        df: dict[str, int] = defaultdict(int)
        total_len = 0
        for chunk in self.chunks:
            for term in set(chunk["tokens"]):
                df[term] += 1
            total_len += len(chunk["tokens"])

        self.avg_dl = total_len / max(N, 1)
        self.idf = {
            term: math.log((N - freq + 0.5) / (freq + 0.5) + 1)
            for term, freq in df.items()
        }
        self._built = True
        print(f"[RAG] Index built: {len(self.chunks)} chunks, avg_dl={self.avg_dl:.0f} tokens")

    # ── Retrieval ────────────────────────────────

    def bm25_score(self, query_tokens: list[str], chunk: dict) -> float:
        score = 0.0
        dl = len(chunk["tokens"])
        for term in query_tokens:
            if term not in chunk["tf"]:
                continue
            tf = chunk["tf"][term]
            idf = self.idf.get(term, 0)
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * dl / max(self.avg_dl, 1))
            score += idf * (numerator / denominator)
        return score

    def tfidf_cosine(self, query_tokens: list[str], chunk: dict) -> float:
        """Lightweight TF-IDF cosine between query and chunk."""
        dl = len(chunk["tokens"])
        q_vec: dict[str, float] = {}
        for t in query_tokens:
            q_vec[t] = q_vec.get(t, 0) + 1

        dot, q_norm, d_norm = 0.0, 0.0, 0.0
        for term, qval in q_vec.items():
            idf = self.idf.get(term, 0)
            q_tfidf = (qval / max(len(query_tokens), 1)) * idf
            d_tf = chunk["tf"].get(term, 0) / max(dl, 1)
            d_tfidf = d_tf * idf
            dot += q_tfidf * d_tfidf
            q_norm += q_tfidf ** 2
            d_norm += d_tfidf ** 2

        if q_norm == 0 or d_norm == 0:
            return 0.0
        return dot / (math.sqrt(q_norm) * math.sqrt(d_norm))

    def retrieve(self, query: str, top_k: int = 5, domain_filter: str = None) -> list[dict]:
        """
        Retrieve top-k chunks using hybrid BM25 + TF-IDF + title boost.
        Returns list of {title, text, score, article_numbers}.
        """
        if not self._built:
            raise RuntimeError("Index not built. Call build() first.")

        query_tokens = expand_query(query)
        if not query_tokens:
            query_tokens = tokenize(query)

        candidate_chunks = self.chunks
        if domain_filter:
            candidate_chunks = [chunk for chunk in self.chunks if chunk.get("metadata", {}).get("domain") == domain_filter]
            print(f"Using domain filter: {domain_filter}")

        scored = []
        for chunk in candidate_chunks:
            bm25 = self.bm25_score(query_tokens, chunk)
            cosine = self.tfidf_cosine(query_tokens, chunk)

            # Title boost: if query terms appear in article title
            title_boost = 0
            title_lower = chunk["title"].lower()
            if title_lower.startswith("article") or title_lower.startswith("part"):
                for t in query_tokens:
                    if t in title_lower:
                        title_boost += 2

            hybrid_score = 0.6 * bm25 + 0.4 * cosine * 10 + title_boost

            matched_terms = []
            seen_terms = set()
            for term in query_tokens:
                if term in chunk["tf"] and term not in seen_terms:
                    matched_terms.append(term)
                    seen_terms.add(term)

            if hybrid_score > 0:
                scored.append({
                    "score": hybrid_score,
                    "bm25": bm25,
                    "cosine": cosine,
                    "title_boost": title_boost,
                    "matched_terms": matched_terms,
                    "chunk": chunk,
                })

        scored.sort(key=lambda x: x["score"], reverse=True)
        results = []
        for entry in scored[:top_k]:
            chunk = entry["chunk"]
            article_nums = re.findall(r'(?i)Article\s+(\d+[A-Z]?)', chunk["text"])
            if chunk.get("metadata", {}).get("domain") == "general":
                article_nums += re.findall(r'(?m)^(?:\d+\[)?(\d{1,3}[A-Z]?)\.', chunk["text"])
            results.append({
                "title": chunk["title"],
                "text": chunk["text"],
                "score": round(entry["score"], 3),
                "article_numbers": list(dict.fromkeys(article_nums))[:5],  # deduplicate
                "metadata": chunk.get("metadata", {}),
                "score_breakdown": {
                    "bm25": round(entry["bm25"], 3),
                    "cosine": round(entry["cosine"], 3),
                    "title_boost": round(entry["title_boost"], 3),
                    "hybrid": round(entry["score"], 3),
                    "matched_terms": entry["matched_terms"][:12],
                },
            })
        return results


def BuildHybridIndex(
    text: str,
    chunk_size: int = 2000,
    overlap: int = 400,
    domain: str = None,
    source: str = None,
):
    """
    Wrapper for corpus loading that builds and returns a standalone index.
    """
    index = HybridRAGIndex()
    index.build(text, chunk_size=chunk_size, overlap=overlap, domain=domain, source=source)
    return index


# ────────────────────────────────────────────────
# Keyword extraction for display
# ────────────────────────────────────────────────

LEGAL_KEYWORDS_MAP = {
    # Fundamental Rights
    "right to equality": ["equality", "equal", "discrimination", "Article 14", "Article 15", "Article 16"],
    "right to freedom": ["freedom", "speech", "expression", "liberty", "Article 19", "Article 21"],
    "right against exploitation": ["exploitation", "forced labour", "trafficking", "Article 23", "Article 24"],
    "right to education": ["education", "school", "child", "RTE", "Article 21A"],
    "right to constitutional remedies": ["habeas corpus", "mandamus", "Article 32", "Article 226"],
    "freedom of religion": ["religion", "religious", "worship", "Article 25", "Article 26"],

    # Criminal / Tort
    "police brutality / unlawful arrest": ["arrest", "detention", "police", "custody", "FIR", "remand"],
    "accident / personal injury": ["accident", "injury", "road", "motor vehicle", "compensation"],
    "property dispute": ["property", "land", "ownership", "encroachment", "rent", "eviction"],

    # Labour
    "labour rights": ["worker", "employee", "wages", "salary", "factory", "dismissal", "labour"],
    "consumer protection": ["consumer", "product", "defect", "fraud", "refund", "cheating"],

    # Family
    "matrimonial / family law": ["marriage", "divorce", "dowry", "custody", "maintenance", "wife", "husband"],

    # Environment
    "environmental rights": ["pollution", "environment", "forest", "wildlife", "clean air", "water"],
}


def extract_legal_keywords(query: str, retrieved_chunks: list[dict]) -> list[str]:
    """Identify which high-level legal topics are triggered."""
    combined = (query + " " + " ".join(c["text"] for c in retrieved_chunks)).lower()
    found = []
    for topic, signals in LEGAL_KEYWORDS_MAP.items():
        if any(_contains_signal(combined, s.lower()) for s in signals):
            found.append(topic)
    return found[:6]  # cap at 6


# ────────────────────────────────────────────────
# Rights & next steps knowledge base
# ────────────────────────────────────────────────

RIGHTS_DB = {
    "accident": [
        "Right to compensation under the Motor Vehicles Act, 1988",
        "Right to free first-aid and emergency treatment (Article 21)",
        "Right to file FIR against negligent driver",
        "Right to approach Motor Accident Claims Tribunal (MACT)",
    ],
    "police": [
        "Right to know reason of arrest (Article 22(1))",
        "Right to consult and be defended by a lawyer of choice",
        "Right to be produced before magistrate within 24 hours (Article 22(2))",
        "Right against self-incrimination (Article 20(3))",
        "Right to bail in bailable offences",
        "Right to file complaint against police misconduct",
    ],
    "property": [
        "Right to approach civil court for property disputes",
        "Right to file complaint under Rent Control Act for illegal eviction",
        "Right against unlawful dispossession without due process",
        "Right to seek injunction against encroachment",
    ],
    "worker": [
        "Right to fair wages (Minimum Wages Act, 1948)",
        "Right against forced labour (Article 23)",
        "Right to safe working conditions (Factories Act, 1948)",
        "Right to file complaint with Labour Commissioner",
        "Right to provident fund and gratuity",
    ],
    "discrimination": [
        "Right to equality before law (Article 14)",
        "Right against discrimination on grounds of religion, race, caste, sex (Article 15)",
        "Right to file complaint under SC/ST (Prevention of Atrocities) Act",
        "Right to approach NHRC / State Human Rights Commission",
    ],
    "consumer": [
        "Right to file complaint in Consumer Dispute Redressal Forum",
        "Right to refund / replacement under Consumer Protection Act, 2019",
        "Right to file complaint with district, state, or national consumer commission",
        "Right to compensation for defective goods / deficient services",
    ],
    "marriage": [
        "Right to live separately without divorce (maintenance under Section 125 CrPC)",
        "Right to file complaint for domestic violence (Protection of Women from Domestic Violence Act, 2005)",
        "Right to seek divorce under personal laws or Special Marriage Act",
        "Right against dowry harassment (Dowry Prohibition Act / IPC 498A)",
    ],
    "education": [
        "Right to free and compulsory education for children 6–14 years (Article 21A, RTE Act 2009)",
        "Right against discrimination in school admission",
        "Right to reservation of seats in private schools (25% EWS/disadvantaged)",
    ],
    "environment": [
        "Right to a clean and healthy environment (derived from Article 21)",
        "Right to file public interest litigation (PIL) for environmental issues",
        "Right to approach NGT (National Green Tribunal)",
    ],
    "default": [
        "Right to approach High Court under Article 226",
        "Right to approach Supreme Court under Article 32",
        "Right to free legal aid if unable to afford lawyer (Legal Services Authorities Act, 1987)",
        "Right to file a complaint with relevant regulatory body",
    ],
}

NEXT_STEPS_DB = {
    "accident": [
        "File an FIR at the nearest police station immediately",
        "Seek immediate medical attention and preserve all medical records",
        "Collect names and contact details of witnesses",
        "Note vehicle registration numbers involved",
        "File a claim petition before the Motor Accident Claims Tribunal (MACT)",
        "Consult a personal injury lawyer for compensation assessment",
    ],
    "police": [
        "Remain calm and do not resist arrest",
        "Ask for the reason for arrest and demand to see the warrant if applicable",
        "Immediately inform a family member or lawyer",
        "Do not sign any document without legal counsel",
        "Apply for bail at the earliest opportunity",
        "File a complaint with the SP / DGP / NHRC if rights are violated",
    ],
    "property": [
        "Gather all property documents, title deeds, and sale agreements",
        "Send a legal notice to the opposing party through a lawyer",
        "File a civil suit in the district court for title dispute",
        "Apply for an injunction to prevent further encroachment",
        "Contact the district administration or tehsildar for land records",
    ],
    "worker": [
        "Document all evidence of violations (pay slips, communications)",
        "File a complaint with the Labour Commissioner",
        "Approach the nearest Labour Court or Industrial Tribunal",
        "Contact a trade union or labour rights organization",
        "File a complaint for non-payment of wages under Payment of Wages Act",
    ],
    "consumer": [
        "Preserve all receipts, warranties, and communication records",
        "Send a formal complaint letter to the company / seller",
        "File a complaint in the District Consumer Disputes Redressal Commission",
        "You can also file online at consumerhelpline.gov.in",
        "No court fees for claims up to ₹5 lakh",
    ],
    "default": [
        "Document everything – dates, witnesses, evidence, communications",
        "Consult a qualified lawyer for personalized legal advice",
        "Contact the nearest District Legal Services Authority (DLSA) for free legal aid",
        "You can call Tele-Law helpline: 15100 for free legal guidance",
        "File a complaint with relevant government authority or court",
    ],
}


def get_rights_and_steps(query: str) -> tuple[list[str], list[str]]:
    """Return relevant rights and next steps based on query keywords."""
    q = query.lower()
    rights, steps = [], []

    category_map = {
        "accident": ["accident", "injury", "road", "vehicle", "crash", "hurt"],
        "police": ["police", "arrest", "fir", "custody", "detention", "constable", "officer"],
        "property": ["property", "land", "rent", "eviction", "tenant", "landlord", "encroach"],
        "worker": ["worker", "employee", "salary", "wages", "job", "labour", "dismiss", "fire"],
        "discrimination": ["caste", "discrimination", "untouchability", "sc", "st", "dalit"],
        "consumer": ["consumer", "product", "fraud", "cheat", "refund", "defect", "scam", "warranty", "replacement", "repair", "company", "seller", "service"],
        "marriage": ["marriage", "divorce", "dowry", "domestic violence", "wife", "husband", "matrimonial"],
        "education": ["school", "education", "child", "admission", "rte", "teacher"],
        "environment": ["pollution", "environment", "noise", "waste", "forest", "river"],
    }

    matched_categories = []
    for cat, signals in category_map.items():
        if any(_contains_signal(q, s) for s in signals):
            matched_categories.append(cat)

    if not matched_categories:
        matched_categories = ["default"]

    for cat in matched_categories:
        rights.extend(RIGHTS_DB.get(cat, RIGHTS_DB["default"]))
        steps.extend(NEXT_STEPS_DB.get(cat, NEXT_STEPS_DB["default"]))

    # Always add default legal remedies
    rights.extend(RIGHTS_DB["default"])
    steps.extend(NEXT_STEPS_DB["default"])

    # Deduplicate while preserving order
    seen = set()
    rights = [r for r in rights if not (r in seen or seen.add(r))]
    seen = set()
    steps = [s for s in steps if not (s in seen or seen.add(s))]

    return rights[:8], steps[:7]


def assess_urgency(query: str) -> dict:
    """Assess urgency level and case type."""
    q = query.lower()
    if any(w in q for w in ["murder", "rape", "kidnap", "life threat", "dangerous", "emergency", "die", "death", "attack"]):
        return {"level": "CRITICAL", "color": "#ef4444", "message": "Seek immediate police assistance and legal counsel"}
    if any(w in q for w in ["arrest", "custody", "detained", "eviction", "assault", "violence", "abuse"]):
        return {"level": "HIGH", "color": "#f59e0b", "message": "Time-sensitive — take action within 24–48 hours"}
    if any(w in q for w in ["dispute", "complaint", "fraud", "cheat", "accident", "injury"]):
        return {"level": "MEDIUM", "color": "#3b82f6", "message": "Action recommended within the week"}
    return {"level": "STANDARD", "color": "#10b981", "message": "Consult a lawyer at your convenience"}
