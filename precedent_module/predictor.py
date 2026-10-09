"""Hybrid RAG predictor for legal outcome forecasting."""

from __future__ import annotations

import json
import pickle
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings, OllamaLLM

from config import (
    BM25_PATH,
    CASE_CORPUS_DIR,
    CHROMA_DIR,
    EMBEDDING_MODEL,
    OLLAMA_BASE_URL,
    REASONING_MODEL,
    VECTOR_COLLECTION_NAME,
    VERDICT_TAIL_CHARS,
)
from index_cases import tokenize


VERDICT_SCORES = {"ALLOWED": 1.0, "PARTIAL": 0.5, "DISMISSED": 0.0}


creatclass PrecedentForecaster:
    def __init__(self, corpus_dir: Path = CASE_CORPUS_DIR) -> None:
        self.corpus_dir = Path(corpus_dir)
        self.embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        self.llm = OllamaLLM(model=REASONING_MODEL, temperature=0)
        self.vector_store = Chroma(
            collection_name=VECTOR_COLLECTION_NAME,
            embedding_function=self.embeddings,
            persist_directory=str(CHROMA_DIR),
        )
        self.bm25_payload = self._load_bm25()

    def _load_bm25(self) -> Any:
        if not BM25_PATH.exists():
            raise FileNotFoundError(
                f"BM25 index missing at {BM25_PATH}. Run `python index_cases.py --reset` first."
            )
        with BM25_PATH.open("rb") as file:
            return pickle.load(file)

    def hybrid_retrieve(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        scores: dict[str, dict[str, Any]] = defaultdict(lambda: {"score": 0.0, "evidence": []})

        query_tokens = tokenize(query)
        bm25_scores = self.bm25_payload["bm25"].get_scores(query_tokens)
        ranked_indexes = sorted(
            range(len(bm25_scores)), key=lambda index: bm25_scores[index], reverse=True
        )[: max(top_k * 4, 12)]

        max_bm25 = max([bm25_scores[index] for index in ranked_indexes] or [1.0]) or 1.0
        for index in ranked_indexes:
            raw_doc = self.bm25_payload["documents"][index]
            metadata = raw_doc["metadata"]
            source_file = metadata["source_file"]
            normalized = float(bm25_scores[index]) / float(max_bm25)
            scores[source_file]["score"] += 0.45 * normalized
            scores[source_file]["source_file"] = source_file
            scores[source_file]["evidence"].append(
                {
                    "retriever": "BM25",
                    "section": metadata.get("section"),
                    "chunk": raw_doc["page_content"][:700],
                    "score": round(normalized, 4),
                }
            )

        vector_hits = self.vector_store.similarity_search_with_relevance_scores(
            query, k=max(top_k * 4, 12)
        )
        for doc, relevance in vector_hits:
            source_file = doc.metadata["source_file"]
            safe_relevance = max(0.0, float(relevance))
            scores[source_file]["score"] += 0.55 * safe_relevance
            scores[source_file]["source_file"] = source_file
            scores[source_file]["evidence"].append(
                {
                    "retriever": "Vector",
                    "section": doc.metadata.get("section"),
                    "chunk": doc.page_content[:700],
                    "score": round(safe_relevance, 4),
                }
            )

        ranked = sorted(scores.values(), key=lambda item: item["score"], reverse=True)
        return ranked[:top_k]

    def read_verdict_tail(self, source_file: str) -> str:
        safe_name = Path(source_file).name
        path = self.corpus_dir / safe_name
        if not path.exists():
            raise FileNotFoundError(f"Source judgment not found: {path}")
        text = path.read_text(encoding="utf-8", errors="ignore")
        return text[-VERDICT_TAIL_CHARS:]

    def analyze_case(self, user_facts: str, retrieved_case: dict[str, Any]) -> dict[str, Any]:
        source_file = retrieved_case["source_file"]
        verdict_text = self.read_verdict_tail(source_file)
        prompt = f"""
You are PrecedentForecaster, a legal outcome analysis module for Indian Supreme Court judgments.
Use only the precedent verdict excerpt below. Do not invent facts.

User facts:
{user_facts}

Precedent source_file:
{source_file}

Final 3000 characters of precedent judgment:
{verdict_text}

Apply this exact logic:
1. Identify the legal principle (Ratio Decidendi) that decided this case.
2. Compare the user's facts to this principle.
3. Output the verdict: ALLOWED, DISMISSED, or PARTIAL.

Return strict JSON only with these keys:
source_file, ratio_decidendi, comparison, predicted_verdict, confidence, similarity_reason.
confidence must be a number from 0 to 1.
"""
        raw = self.llm.invoke(prompt)
        parsed = self._parse_json(raw)
        parsed.setdefault("source_file", source_file)
        parsed["predicted_verdict"] = self._normalize_verdict(parsed.get("predicted_verdict"))
        parsed["confidence"] = self._normalize_confidence(parsed.get("confidence"))
        parsed["retrieval_score"] = round(float(retrieved_case.get("score", 0.0)), 4)
        parsed["verdict_excerpt"] = verdict_text
        return parsed

    def predict(self, user_facts: str) -> dict[str, Any]:
        similar_cases = self.hybrid_retrieve(user_facts, top_k=5)
        top_cases = similar_cases[:3]
        analyses = [self.analyze_case(user_facts, case) for case in top_cases]

        weighted_total = 0.0
        weight_sum = 0.0
        for analysis in analyses:
            verdict_score = VERDICT_SCORES.get(analysis["predicted_verdict"], 0.5)
            weight = max(0.1, float(analysis.get("confidence", 0.5)))
            weighted_total += verdict_score * weight
            weight_sum += weight

        success_probability = weighted_total / weight_sum if weight_sum else 0.5
        return {
            "success_probability": round(success_probability, 3),
            "success_percentage": round(success_probability * 100, 1),
            "top_case_analyses": analyses,
            "similar_cases": self._summarize_similar_cases(similar_cases),
        }

    def _summarize_similar_cases(self, cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
        summarized = []
        for case in cases:
            best_evidence = max(case.get("evidence", []), key=lambda item: item.get("score", 0))
            summarized.append(
                {
                    "source_file": case["source_file"],
                    "retrieval_score": round(float(case.get("score", 0.0)), 4),
                    "matched_section": best_evidence.get("section"),
                    "why_similar": best_evidence.get("chunk", "").replace("\n", " ")[:450],
                }
            )
        return summarized

    @staticmethod
    def _parse_json(raw: str) -> dict[str, Any]:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
        return {
            "ratio_decidendi": "The model did not return parseable JSON.",
            "comparison": raw[:1000],
            "predicted_verdict": "PARTIAL",
            "confidence": 0.3,
            "similarity_reason": "Fallback result from unstructured model output.",
        }

    @staticmethod
    def _normalize_verdict(value: Any) -> str:
        text = str(value or "PARTIAL").upper()
        for verdict in ("ALLOWED", "DISMISSED", "PARTIAL"):
            if verdict in text:
                return verdict
        return "PARTIAL"

    @staticmethod
    def _normalize_confidence(value: Any) -> float:
        try:
            confidence = float(value)
        except (TypeError, ValueError):
            return 0.5
        return min(1.0, max(0.0, confidence))


if __name__ == "__main__":
    facts = input("Enter case facts: ").strip()
    print(json.dumps(PrecedentForecaster().predict(facts), indent=2))
