import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from utils.hallucination_guard import verify_claims
from utils.retriever import Chunk


class HallucinationGuardTest(unittest.TestCase):
    def setUp(self):
        self.chunks = [
            Chunk("c1", "Article 22 says a person arrested shall be informed of grounds of arrest and may consult a legal practitioner.", "Constitution of India", None, "general", 1, 1, 1),
            Chunk("c2", "The Consumer Protection Act, 2019 provides remedies for defective goods and deficient services.", "Consumer Protection Act, 2019", None, "consumer", 1, 1, 1),
            Chunk("c3", "Section 17 discusses unfair contracts in the consumer context.", "Consumer Protection Act, 2019", None, "consumer", 1, 1, 1),
        ]

    def test_grounded_article_is_not_flagged(self):
        self.assertEqual(verify_claims("Article 22 applies here.", self.chunks), [])

    def test_grounded_act_is_not_flagged(self):
        self.assertEqual(verify_claims("Consumer Protection Act, 2019 may apply.", self.chunks), [])

    def test_fake_article_is_flagged(self):
        flagged = verify_claims("Article 999 creates a right to instant refund.", self.chunks)
        self.assertEqual(flagged[0]["claim"], "Article 999")

    def test_fake_act_is_flagged(self):
        flagged = verify_claims("The Imaginary Remedies Act, 2099 applies.", self.chunks)
        self.assertTrue(any("Imaginary Remedies Act" in item["claim"] for item in flagged))

    def test_precision_recall_fixture(self):
        grounded = [f"Grounded Article 22 claim {i}" for i in range(10)]
        fake = [f"Fake Article {900 + i} claim" for i in range(10)]
        true_positive = sum(1 for text in fake if verify_claims(text, self.chunks))
        false_positive = sum(1 for text in grounded if verify_claims(text, self.chunks))
        precision = true_positive / max(true_positive + false_positive, 1)
        recall = true_positive / len(fake)
        self.assertGreaterEqual(precision, 0.9)
        self.assertGreaterEqual(recall, 0.9)


if __name__ == "__main__":
    unittest.main()
