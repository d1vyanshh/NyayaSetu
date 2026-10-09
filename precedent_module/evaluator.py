"""Ragas evaluation pipeline for PrecedentForecaster outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from datasets import Dataset
from langchain_ollama import OllamaEmbeddings, OllamaLLM

from config import EMBEDDING_MODEL, EVALUATION_REPORT_PATH, OLLAMA_BASE_URL, REASONING_MODEL


def run_ragas_evaluation(
    user_facts: str,
    prediction: dict[str, Any],
    output_path: Path = EVALUATION_REPORT_PATH,
) -> pd.DataFrame:
    """Evaluate the latest prediction and write evaluation_report.csv."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from ragas import evaluate
        from ragas.integrations.langchain import LangchainEmbeddingsWrapper, LangchainLLMWrapper
        from ragas.metrics import answer_relevancy, context_recall, faithfulness
    except Exception as exc:
        report = pd.DataFrame(
            [
                {
                    "metric": "ragas_import",
                    "score": 0.0,
                    "note": f"Ragas is not available or has incompatible imports: {exc}",
                }
            ]
        )
        report.to_csv(output_path, index=False)
        return report

    contexts = [
        analysis.get("verdict_excerpt", "")
        for analysis in prediction.get("top_case_analyses", [])
        if analysis.get("verdict_excerpt")
    ]
    answer = _prediction_to_answer(prediction)
    reference = _prediction_to_reference(prediction)

    dataset = Dataset.from_list(
        [
            {
                "user_input": user_facts,
                "query": user_facts,
                "answer": answer,
                "response": answer,
                "retrieved_contexts": contexts,
                "contexts": contexts,
                "reference": reference,
                "ground_truth": reference,
            }
        ]
    )

    llm = LangchainLLMWrapper(OllamaLLM(model=REASONING_MODEL))
    embeddings = LangchainEmbeddingsWrapper(
        OllamaEmbeddings(model=EMBEDDING_MODEL)
    )

    try:
        result = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy, context_recall],
            llm=llm,
            embeddings=embeddings,
        )
        report = result.to_pandas()
    except Exception as exc:
        report = pd.DataFrame(
            [{"metric": "ragas_runtime", "score": 0.0, "note": f"Evaluation failed: {exc}"}]
        )

    report.to_csv(output_path, index=False)
    return report


def _prediction_to_answer(prediction: dict[str, Any]) -> str:
    lines = [f"Success probability: {prediction.get('success_percentage', 0)}%"]
    for analysis in prediction.get("top_case_analyses", []):
        lines.append(
            " | ".join(
                [
                    f"Case: {analysis.get('source_file')}",
                    f"Verdict: {analysis.get('predicted_verdict')}",
                    f"Ratio: {analysis.get('ratio_decidendi')}",
                    f"Comparison: {analysis.get('comparison')}",
                ]
            )
        )
    return "\n".join(lines)


def _prediction_to_reference(prediction: dict[str, Any]) -> str:
    verdicts = [
        f"{analysis.get('source_file')}: {analysis.get('predicted_verdict')}"
        for analysis in prediction.get("top_case_analyses", [])
    ]
    return "The forecast should be grounded in the retrieved verdict excerpts. " + "; ".join(
        verdicts
    )
