"""
Standalone RAG benchmark evaluation.

Runs Recall@5 over a fixed legal QA set without importing the Flask app or
changing the main application flow.

Usage:
    python backend/rag_benchmark.py
    python backend/rag_benchmark.py --ragas
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

from rag_engine import HybridRAGIndex


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
CONSTITUTION_PATHS = [
    BASE_DIR / "constitution.txt",
    BASE_DIR / "static" / "constitution.txt",
]
CORPUS_DIR = PROJECT_ROOT / "corpus"
CORPUS_PDFS = {
    "consumer_protection_act_2019.pdf": "Consumer Protection Act, 2019",
    "domestic_violence_act_2005.pdf": "Protection of Women from Domestic Violence Act, 2005",
    "shops_establishments_act.pdf": "Shops and Establishments Act",
    "wages_act_2019.pdf": "Code on Wages, 2019",
}


@dataclass(frozen=True)
class BenchmarkCase:
    question: str
    expected: str
    aliases: tuple[str, ...] = ()


TEST_QUESTIONS: list[BenchmarkCase] = [
    BenchmarkCase("Which provision guarantees equality before law?", "Article 14"),
    BenchmarkCase("Which article prohibits discrimination by the State?", "Article 15"),
    BenchmarkCase("Which article covers equality of opportunity in public employment?", "Article 16"),
    BenchmarkCase("Which constitutional provision abolishes untouchability?", "Article 17"),
    BenchmarkCase("Which article abolishes titles?", "Article 18"),
    BenchmarkCase("Which article protects freedom of speech and expression?", "Article 19"),
    BenchmarkCase("Which article protects against ex post facto criminal laws?", "Article 20"),
    BenchmarkCase("Which article protects against double jeopardy?", "Article 20"),
    BenchmarkCase("Which article protects against self-incrimination?", "Article 20"),
    BenchmarkCase("Which article guarantees life and personal liberty?", "Article 21"),
    BenchmarkCase("Which article provides education for children aged 6 to 14?", "Article 21A", ("Article 21-A",)),
    BenchmarkCase("Which article gives safeguards after arrest and detention?", "Article 22"),
    BenchmarkCase("Which article prohibits human trafficking and forced labour?", "Article 23"),
    BenchmarkCase("Which article bans employment of children in factories?", "Article 24"),
    BenchmarkCase("Which article protects freedom of conscience and religion?", "Article 25"),
    BenchmarkCase("Which article protects the right to manage religious affairs?", "Article 26"),
    BenchmarkCase("Which article bars tax proceeds from promoting a particular religion?", "Article 27"),
    BenchmarkCase("Which article concerns religious instruction in educational institutions?", "Article 28"),
    BenchmarkCase("Which article protects interests of minorities?", "Article 29"),
    BenchmarkCase("Which article lets minorities establish and administer educational institutions?", "Article 30"),
    BenchmarkCase("Which article provides remedies before the Supreme Court?", "Article 32"),
    BenchmarkCase("Which article allows High Courts to issue writs?", "Article 226"),
    BenchmarkCase("Which article protects property from deprivation except by law?", "Article 300A", ("Article 300-A",)),
    BenchmarkCase("Which article directs the State to provide free legal aid?", "Article 39A", ("Article 39-A",)),
    BenchmarkCase("Which article asks the State to organise village panchayats?", "Article 40"),
    BenchmarkCase("Which article deals with just and humane conditions of work and maternity relief?", "Article 42"),
    BenchmarkCase("Which article directs the State to secure a living wage for workers?", "Article 43"),
    BenchmarkCase("Which article directs promotion of education and economic interests of weaker sections?", "Article 46"),
    BenchmarkCase("Which article concerns protection of monuments and places of national importance?", "Article 49"),
    BenchmarkCase("Which article separates the judiciary from the executive?", "Article 50"),
    BenchmarkCase("Which law protects buyers from defective goods and deficient services?", "Consumer Protection Act, 2019", ("Consumer Protection Act",)),
    BenchmarkCase("Which act lets consumers file complaints before consumer commissions?", "Consumer Protection Act, 2019", ("Consumer Protection Act",)),
    BenchmarkCase("Which law defines unfair trade practice and product liability?", "Consumer Protection Act, 2019", ("Consumer Protection Act",)),
    BenchmarkCase("Which law protects women from domestic violence at home?", "Protection of Women from Domestic Violence Act, 2005", ("Domestic Violence Act",)),
    BenchmarkCase("Which act provides protection orders for domestic violence survivors?", "Protection of Women from Domestic Violence Act, 2005", ("Domestic Violence Act",)),
    BenchmarkCase("Which act deals with residence orders in domestic violence cases?", "Protection of Women from Domestic Violence Act, 2005", ("Domestic Violence Act",)),
    BenchmarkCase("Which law governs minimum wages in the current wage code?", "Code on Wages, 2019", ("Wages Act", "minimum wages")),
    BenchmarkCase("Which law covers payment of wages and timely wage payment?", "Code on Wages, 2019", ("Wages Act", "payment of wages")),
    BenchmarkCase("Which law deals with bonus payments to employees?", "Code on Wages, 2019", ("Payment of Bonus", "bonus")),
    BenchmarkCase("Which law prohibits gender discrimination in wages?", "Code on Wages, 2019", ("equal remuneration", "gender discrimination")),
    BenchmarkCase("Which law regulates registration of shops and commercial establishments?", "Shops and Establishments Act", ("shop", "establishment")),
    BenchmarkCase("Which law governs working hours in shops and establishments?", "Shops and Establishments Act", ("working hours", "establishment")),
    BenchmarkCase("Which law covers weekly holidays for shop employees?", "Shops and Establishments Act", ("weekly holiday", "establishment")),
    BenchmarkCase("Which law governs leave rules for employees in shops?", "Shops and Establishments Act", ("leave", "establishment")),
    BenchmarkCase("Which article supports the right to privacy as part of personal liberty?", "Article 21"),
    BenchmarkCase("Which article is cited for the right to speedy trial?", "Article 21"),
    BenchmarkCase("Which article is cited for clean environment as part of life?", "Article 21"),
    BenchmarkCase("Which article protects the right to form associations or unions?", "Article 19"),
    BenchmarkCase("Which article protects movement throughout India?", "Article 19"),
    BenchmarkCase("Which article protects the right to practise a profession?", "Article 19"),
]


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract PDF text with whichever local PDF library is available."""
    try:
        import fitz

        doc = fitz.open(str(pdf_path))
        try:
            return "\n".join(page.get_text() for page in doc)
        finally:
            doc.close()
    except ImportError:
        pass
    except Exception as exc:
        print(f"[WARN] PyMuPDF failed for {pdf_path.name}: {exc}")

    try:
        import PyPDF2

        with pdf_path.open("rb") as file:
            reader = PyPDF2.PdfReader(file)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
    except ImportError:
        print("[WARN] No PDF extraction library found. Install PyMuPDF or PyPDF2 to include corpus PDFs.")
    except Exception as exc:
        print(f"[WARN] PyPDF2 failed for {pdf_path.name}: {exc}")
    return ""


def load_benchmark_corpus() -> str:
    """Load Constitution text plus any local act PDFs into one benchmark corpus."""
    documents: list[str] = []

    for path in CONSTITUTION_PATHS:
        if path.exists():
            documents.append(f"\n\nDOCUMENT: Constitution of India\n\n{path.read_text(encoding='utf-8')}")
            break
    else:
        raise FileNotFoundError("Could not find constitution.txt in backend/ or backend/static/.")

    for filename, act_name in CORPUS_PDFS.items():
        pdf_path = CORPUS_DIR / filename
        if not pdf_path.exists():
            print(f"[WARN] Missing optional corpus file: {pdf_path}")
            continue
        text = extract_pdf_text(pdf_path)
        if text.strip():
            documents.append(f"\n\nDOCUMENT: {act_name}\nACT: {act_name}\n\n{text}")
        else:
            print(f"[WARN] No text extracted from {pdf_path.name}; skipping.")

    return "\n\n".join(documents)


def normalize_reference(value: str) -> str:
    value = value.lower()
    value = value.replace("-", "")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def chunk_contains_expected(chunk: dict, case: BenchmarkCase) -> bool:
    haystack_parts = [
        chunk.get("title", ""),
        chunk.get("text", ""),
        " ".join(f"Article {num}" for num in chunk.get("article_numbers", [])),
    ]
    haystack = normalize_reference(" ".join(haystack_parts))
    expected_refs = (case.expected, *case.aliases)
    return any(normalize_reference(ref) in haystack for ref in expected_refs)


def evaluate_recall_at_5(index: HybridRAGIndex, cases: list[BenchmarkCase]) -> tuple[int, list[dict]]:
    correct = 0
    rows: list[dict] = []

    for case in cases:
        retrieved = index.retrieve(case.question, top_k=5)
        hit_rank = None
        for rank, chunk in enumerate(retrieved, start=1):
            if chunk_contains_expected(chunk, case):
                hit_rank = rank
                break

        if hit_rank is not None:
            correct += 1

        rows.append(
            {
                "question": case.question,
                "expected": case.expected,
                "hit": hit_rank is not None,
                "hit_rank": hit_rank,
                "top_titles": [chunk.get("title", "") for chunk in retrieved],
                "contexts": [chunk.get("text", "") for chunk in retrieved],
            }
        )

    return correct, rows


def run_optional_ragas(rows: list[dict]) -> None:
    """Run a small optional RAGAS context precision check when dependencies exist."""
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import context_precision
    except ImportError:
        print("[INFO] RAGAS or datasets is not installed. Skipping optional RAGAS evaluation.")
        return

    dataset = Dataset.from_dict(
        {
            "question": [row["question"] for row in rows],
            "answer": [row["expected"] for row in rows],
            "contexts": [row["contexts"] for row in rows],
            "ground_truth": [row["expected"] for row in rows],
        }
    )

    try:
        result = evaluate(dataset, metrics=[context_precision])
        print("\n[RAGAS] Optional context_precision result:")
        print(result)
    except Exception as exc:
        print(f"[INFO] RAGAS is installed but could not run with the local setup: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run RAG Recall@5 benchmark.")
    parser.add_argument("--ragas", action="store_true", help="Attempt optional RAGAS evaluation.")
    parser.add_argument("--show-misses", action="store_true", help="Print top titles for missed cases.")
    args = parser.parse_args()

    corpus_text = load_benchmark_corpus()
    index = HybridRAGIndex()
    index.build(corpus_text, chunk_size=2000, overlap=400, domain="benchmark")

    correct, rows = evaluate_recall_at_5(index, TEST_QUESTIONS)
    total = len(TEST_QUESTIONS)
    accuracy = (correct / total) * 100 if total else 0.0

    for idx, row in enumerate(rows, start=1):
        marker = "YES" if row["hit"] else "NO"
        rank = f"rank {row['hit_rank']}" if row["hit_rank"] else "not in top 5"
        print(f"Q{idx:02d}: {marker} ({rank}) | Expected: {row['expected']} | {row['question']}")
        if args.show_misses and not row["hit"]:
            for title in row["top_titles"]:
                print(f"      - {title}")

    print(f"\nRecall@5 Accuracy: {accuracy:.2f}% ({correct}/{total})")

    if args.ragas:
        run_optional_ragas(rows)
    else:
        print("[INFO] RAGAS evaluation is optional. Run with --ragas to attempt it if installed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
