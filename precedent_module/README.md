# PrecedentForecaster

RAG-based legal outcome prediction module for NyayaSetu using local Ollama models, ChromaDB, BM25, Streamlit, and Ragas.

## Project Structure

```text
precedent_module/
  app.py              # Streamlit dashboard
  config.py           # Shared paths and model settings
  evaluator.py        # Ragas evaluation pipeline
  index_cases.py      # Hybrid Chroma + BM25 indexing
  predictor.py        # Hybrid retrieval and outcome prediction
  requirements.txt    # Module-specific Python dependencies
  run.bat             # Install, index, and launch helper
  data/
    chroma/           # Generated Chroma vector DB
    bm25_index.pkl    # Generated BM25 keyword index
    evaluation_report.csv
```

The module reads judgments from the existing root-level `case_corpus/` folder.

## Setup

Install Ollama, start it, and pull the required local models:

```bat
ollama pull phi3:mini
ollama pull nomic-embed-text
```

Install dependencies:

```bat
cd precedent_module
python -m pip install -r requirements.txt
```

## Initialize the Indexes

```bat
python index_cases.py --reset
```

The indexing script:
- chunks every `.txt` judgment in `../case_corpus`
- tags chunks in the first 80 percent of each file as `FACTS`
- tags chunks in the last 20 percent as `VERDICT`
- stores `source_file`, `source_path`, `section`, `chunk_number`, and `start_index`
- creates a persistent Chroma vector store
- serializes a BM25 index for exact keyword retrieval

## Launch the UI

```bat
streamlit run app.py
```

Or run the helper:

```bat
run.bat
```

## Docker Deployment

From the project root:

```bat
docker compose up --build
```

Open:

```text
React app:             http://localhost:3000
Flask backend:         http://localhost:5555
PrecedentForecaster:   http://localhost:8501
Ollama API:            http://localhost:11434
```

To run only the PrecedentForecaster feature and Ollama:

```bat
docker compose up --build precedent-forecaster
```

The first launch downloads the Ollama models and builds the Chroma/BM25 indexes. Later launches reuse Docker volumes:

```text
ollama-data
precedent-data
```

## Prediction Flow

1. Hybrid retrieval combines BM25 keyword matches and Chroma vector search.
2. The top 3 matching source files are selected.
3. For each source file, the predictor reads the final 3000 characters of the full judgment.
4. `phi3:mini` analyzes the ratio, compares user facts, and returns `ALLOWED`, `DISMISSED`, or `PARTIAL`.
5. The module returns per-case logic, five similar cases, and a weighted success probability.

## Evaluation

Click `Run Evaluation` in Streamlit after a prediction. The Ragas report is written to:

```text
precedent_module/data/evaluation_report.csv
```
