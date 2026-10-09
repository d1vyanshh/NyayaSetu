import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / "frontend" / "public" / "static" / "bot" / "bot_site_knowledge.js"
CLASSIFIER = ROOT / "frontend" / "public" / "static" / "bot" / "bot_intent_classifier.js"


def classify(text: str) -> dict:
    script = f"""
const fs = require('fs');
eval(fs.readFileSync({json.dumps(str(KB))}, 'utf8'));
eval(fs.readFileSync({json.dumps(str(CLASSIFIER))}, 'utf8'));
const text = {json.dumps(text)};
console.log(JSON.stringify({{
  intent: BotIntentClassifier.classify(text),
  feature: BotIntentClassifier.detectFeature(text),
  topic: BotIntentClassifier.detectLegalTopic(text)
}}));
"""
    output = subprocess.check_output(["node", "-e", script], cwd=ROOT, text=True)
    return json.loads(output)


class BotIntentClassifierTest(unittest.TestCase):
    def test_site_guide_question(self):
        result = classify("How do I use the legal translator?")
        self.assertEqual(result["intent"], "guide")
        self.assertEqual(result["feature"], "translator")

    def test_legal_question(self):
        result = classify("Can my landlord evict me without notice?")
        self.assertEqual(result["intent"], "legal")
        self.assertEqual(result["topic"], "landlord")

    def test_short_ambiguous(self):
        result = classify("help")
        self.assertEqual(result["intent"], "ambiguous")

    def test_feature_detection_rights_card(self):
        result = classify("What are my arrest rights?")
        self.assertEqual(result["feature"], "rights_card")

    def test_constitution_topic(self):
        result = classify("Compare Article 14 and Article 21")
        self.assertEqual(result["intent"], "legal")
        self.assertEqual(result["topic"], "constitution")


if __name__ == "__main__":
    unittest.main()
