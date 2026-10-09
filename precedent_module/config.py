from pathlib import Path
import os


MODULE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = MODULE_DIR.parent

CASE_CORPUS_DIR = PROJECT_ROOT / "case_corpus"
DATA_DIR = MODULE_DIR / "data"
CHROMA_DIR = DATA_DIR / "chroma"
BM25_PATH = DATA_DIR / "bm25_index.pkl"
EVALUATION_REPORT_PATH = DATA_DIR / "evaluation_report.csv"

OLLAMA_BASE_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434")
REASONING_MODEL = os.getenv("PRECEDENT_REASONING_MODEL", "phi3:mini")
EMBEDDING_MODEL = os.getenv("PRECEDENT_EMBEDDING_MODEL", "nomic-embed-text")

CHUNK_SIZE = int(os.getenv("PRECEDENT_CHUNK_SIZE", "1800"))
CHUNK_OVERLAP = int(os.getenv("PRECEDENT_CHUNK_OVERLAP", "220"))
VECTOR_COLLECTION_NAME = "nyayasetu_precedents"
VERDICT_TAIL_CHARS = 3000
INDEX_BATCH_SIZE = int(os.getenv("PRECEDENT_INDEX_BATCH_SIZE", "64"))
MAX_INDEX_FILES = int(os.getenv("PRECEDENT_MAX_INDEX_FILES", "140"))
