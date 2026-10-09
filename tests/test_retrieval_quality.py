import csv
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from utils.retriever import Chunk


TEST_QUERIES = [
    ("fairness", "unpaid overtime wages", ["wages"]),
    ("fairness", "wrongful termination without notice", ["termination"]),
    ("rights_card", "arrest rights lawyer magistrate", ["Article 22"]),
    ("rights_card", "consumer defective product refund", ["Consumer Protection Act"]),
    ("scenario", "fired without notice", ["termination"]),
    ("scenario", "landlord eviction notice", ["eviction"]),
    ("translator", "locked up without reason", ["Article 22"]),
    ("translator", "deficient service", ["Consumer Protection Act"]),
    ("amendment", "Article 21 amendment", ["Article 21"]),
    ("comparator", "Article 14 Article 21", ["Article 14", "Article 21"]),
]


CORPUS = [
    Chunk("wages", "The wages law covers unpaid wages and overtime.", "Code on Wages Act, 2019", None, "labour", 5, 1, 5),
    Chunk("termination", "Termination without notice may be reviewed under labour law.", "Labour corpus", None, "labour", 4, 1, 4),
    Chunk("arrest", "Article 22 protects arrested persons, lawyer consultation and magistrate production.", "Constitution of India", None, "general", 5, 1, 5),
    Chunk("consumer", "Consumer Protection Act covers defective product refund and deficient service.", "Consumer Protection Act, 2019", None, "consumer", 5, 1, 5),
    Chunk("tenant", "Eviction notice and landlord obligations are discussed here.", "Tenant corpus", None, "tenant", 4, 1, 4),
    Chunk("article14", "Article 14 concerns equality before law.", "Constitution of India", None, "general", 4, 1, 4),
    Chunk("article21", "Article 21 protects life and personal liberty.", "Constitution of India", None, "general", 4, 1, 4),
]


def fake_retrieve(query):
    query_terms = set(query.lower().split())
    scored = []
    for chunk in CORPUS:
        score = sum(1 for term in query_terms if term in chunk.text.lower())
        scored.append((score, chunk))
    return [chunk for score, chunk in sorted(scored, key=lambda item: item[0], reverse=True) if score > 0][:5]


class RetrievalQualityTest(unittest.TestCase):
    def test_precision_recall_mrr_and_csv_logging(self):
        rows = []
        precision_total = recall_total = mrr_total = 0.0
        for feature, query, expected_refs in TEST_QUERIES:
            results = fake_retrieve(query)
            haystacks = [f"{c.id} {c.text} {c.source_file}" for c in results]
            hits = [any(ref.lower() in h.lower() for h in haystacks) for ref in expected_refs]
            precision = sum(hits) / 5
            recall = sum(hits) / len(expected_refs)
            reciprocal = 0.0
            for idx, text in enumerate(haystacks, start=1):
                if any(ref.lower() in text.lower() for ref in expected_refs):
                    reciprocal = 1 / idx
                    break
            precision_total += precision
            recall_total += recall
            mrr_total += reciprocal
            rows.append({"feature": feature, "query": query, "precision_at_5": precision, "recall_at_5": recall, "mrr": reciprocal})

        out = Path(tempfile.gettempdir()) / "nyayasetu_retrieval_scores.csv"
        with out.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

        self.assertTrue(out.exists())
        self.assertGreaterEqual(precision_total / len(TEST_QUERIES), 0.1)
        self.assertGreaterEqual(recall_total / len(TEST_QUERIES), 0.8)
        self.assertGreaterEqual(mrr_total / len(TEST_QUERIES), 0.5)


if __name__ == "__main__":
    unittest.main()
