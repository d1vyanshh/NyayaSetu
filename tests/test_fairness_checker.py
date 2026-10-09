import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from features import fairness_checker
from utils.retriever import Chunk


def chunk(text, source="Code on Wages Act, 2019", domain="labour"):
    return Chunk("c1", text, source, None, domain, 5.0, 0.8, 2.48, title="Wages")


class FairnessCheckerTest(unittest.TestCase):
    def test_extracts_unpaid_wage_keywords(self):
        found = fairness_checker.extract_violation_keywords("My employer has unpaid overtime wages.")
        self.assertIn("unpaid_wages", found)

    @patch("features.fairness_checker.llm_generate")
    @patch("features.fairness_checker.shared_retrieve")
    def test_run_uses_retrieval_before_generation(self, mock_retrieve, mock_llm):
        mock_retrieve.return_value = [chunk("Worker wages and overtime are covered by this retrieved labour law.")]
        mock_llm.return_value = '{"possible_violations":[],"suggested_next_steps":[]}'
        result = fairness_checker.run("My employer did not pay overtime.")
        self.assertEqual(result["feature"], "fairness_check")
        self.assertEqual(mock_retrieve.call_count, 1)
        self.assertEqual(mock_llm.call_count, 1)

    def test_generate_without_chunks_never_calls_llm(self):
        with patch("features.fairness_checker.llm_generate") as mock_llm:
            data = fairness_checker.generate([], fairness_checker.FairnessContext("x", "labour", []))
        self.assertEqual(mock_llm.call_count, 0)
        self.assertEqual(data["possible_violations"], [])

    @patch("features.fairness_checker.llm_generate")
    def test_correct_act_can_appear_in_top_violation(self, mock_llm):
        mock_llm.return_value = '{"possible_violations":[{"right":"Right to wages","act":"Code on Wages Act, 2019","why_applicable":"Retrieved text discusses wages.","confidence":0.8,"source_chunk_ids":["c1"]}],"suggested_next_steps":["File complaint"]}'
        data = fairness_checker.generate([chunk("Code on Wages Act, 2019 contains wage obligations.")], fairness_checker.FairnessContext("unpaid wages", "labour", ["unpaid_wages"]))
        top3 = data["possible_violations"][:3]
        self.assertTrue(any("Code on Wages Act" in item.get("act", "") for item in top3))

    def test_response_contract_on_insufficient_data(self):
        with patch("features.fairness_checker.shared_retrieve", return_value=[]):
            result = fairness_checker.run("unknown issue")
        self.assertEqual(result["status"], "insufficient_data")
        self.assertIn("explainability", result)
        self.assertIn("warnings", result)


if __name__ == "__main__":
    unittest.main()
