"""Streamlit UI for NyayaSetu PrecedentForecaster."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from evaluator import run_ragas_evaluation
from predictor import PrecedentForecaster


st.set_page_config(page_title="NyayaSetu PrecedentForecaster", layout="wide")


@st.cache_resource(show_spinner=False)
def load_forecaster() -> PrecedentForecaster:
    return PrecedentForecaster()


st.title("PrecedentForecaster")
st.caption("Hybrid RAG outcome prediction over the local Supreme Court judgment corpus.")

case_facts = st.text_area(
    "Case facts",
    height=220,
    placeholder="Paste the material facts, legal issue, and relief sought...",
)

left, right = st.columns([1, 1])
predict_clicked = left.button("Predict Outcome", type="primary", use_container_width=True)
evaluate_clicked = right.button("Run Evaluation", use_container_width=True)

if "prediction" not in st.session_state:
    st.session_state.prediction = None
if "case_facts" not in st.session_state:
    st.session_state.case_facts = ""

if predict_clicked:
    if not case_facts.strip():
        st.warning("Enter case facts before running the forecast.")
    else:
        with st.spinner("Retrieving precedents and forecasting outcome..."):
            forecaster = load_forecaster()
            st.session_state.prediction = forecaster.predict(case_facts)
            st.session_state.case_facts = case_facts

prediction = st.session_state.prediction
if prediction:
    st.metric("Statistical Success Probability", f"{prediction['success_percentage']}%")

    st.subheader("Top Case Logic")
    for analysis in prediction["top_case_analyses"]:
        with st.expander(
            f"{analysis['source_file']} - {analysis['predicted_verdict']} "
            f"({analysis['confidence']:.2f} confidence)",
            expanded=True,
        ):
            st.markdown(f"**Ratio Decidendi:** {analysis.get('ratio_decidendi', '')}")
            st.markdown(f"**Comparison:** {analysis.get('comparison', '')}")
            st.markdown(f"**Similarity:** {analysis.get('similarity_reason', '')}")

    st.subheader("5 Similar Cases")
    similar_df = pd.DataFrame(prediction["similar_cases"])
    st.dataframe(similar_df, use_container_width=True, hide_index=True)

if evaluate_clicked:
    if not st.session_state.prediction or not st.session_state.case_facts:
        st.warning("Run a prediction first, then evaluate it.")
    else:
        with st.spinner("Running Ragas metrics..."):
            report = run_ragas_evaluation(st.session_state.case_facts, st.session_state.prediction)
        st.subheader("Evaluation Report")
        st.dataframe(report, use_container_width=True, hide_index=True)

st.info(
    "Make sure Ollama is running and the models are pulled: "
    "`ollama pull phi3:mini` and `ollama pull nomic-embed-text`."
)

