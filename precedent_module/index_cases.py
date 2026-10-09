"""Build Chroma and BM25 indexes for Supreme Court precedent retrieval."""

from __future__ import annotations

import argparse
import pickle
import re
from pathlib import Path
from typing import Iterable

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rank_bm25 import BM25Okapi

from config import (
    BM25_PATH,
    CASE_CORPUS_DIR,
    CHROMA_DIR,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    EMBEDDING_MODEL,
    INDEX_BATCH_SIZE,
    MAX_INDEX_FILES,
    OLLAMA_BASE_URL,
    VECTOR_COLLECTION_NAME,
)


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_./:-]+")


def tokenize(text: str) -> list[str]:
    """Tokenize legal text while preserving section/citation-like tokens."""
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


def read_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=encoding, errors="ignore")
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="ignore")


def iter_case_files(corpus_dir: Path, max_files: int | None = None) -> Iterable[Path]:
    files = sorted(path for path in corpus_dir.glob("*.txt") if path.is_file())
    if max_files and max_files > 0:
        return files[:max_files]
    return files


def section_for_chunk(start_index: int, total_length: int) -> str:
    if total_length <= 0:
        return "FACTS"
    position_ratio = start_index / total_length
    return "FACTS" if position_ratio < 0.80 else "VERDICT"


def build_documents(corpus_dir: Path, max_files: int | None = None) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        add_start_index=True,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    documents: list[Document] = []

    for case_file in iter_case_files(corpus_dir, max_files=max_files):
        text = read_text(case_file).strip()
        if not text:
            continue

        chunks = splitter.create_documents([text])
        for chunk_number, chunk in enumerate(chunks):
            start_index = int(chunk.metadata.get("start_index", 0))
            documents.append(
                Document(
                    page_content=chunk.page_content,
                    metadata={
                        "source_file": case_file.name,
                        "source_path": str(case_file.resolve()),
                        "section": section_for_chunk(start_index, len(text)),
                        "chunk_number": chunk_number,
                        "start_index": start_index,
                    },
                )
            )

    return documents


def build_vector_index(documents: list[Document], reset: bool) -> None:
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)

    if reset and CHROMA_DIR.exists():
        import shutil

        shutil.rmtree(CHROMA_DIR)
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    vector_store = Chroma(
        collection_name=VECTOR_COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR),
    )

    ids = [
        f"{doc.metadata['source_file']}::{doc.metadata['chunk_number']}"
        for doc in documents
    ]
    for start in range(0, len(documents), INDEX_BATCH_SIZE):
        end = start + INDEX_BATCH_SIZE
        vector_store.add_documents(documents=documents[start:end], ids=ids[start:end])
        print(f"Indexed vector chunks {min(end, len(documents))}/{len(documents)}")


def build_bm25_index(documents: list[Document]) -> None:
    BM25_PATH.parent.mkdir(parents=True, exist_ok=True)
    tokenized_corpus = [tokenize(doc.page_content) for doc in documents]
    payload = {
        "tokenized_corpus": tokenized_corpus,
        "documents": [
            {"page_content": doc.page_content, "metadata": dict(doc.metadata)}
            for doc in documents
        ],
        "bm25": BM25Okapi(tokenized_corpus),
    }

    with BM25_PATH.open("wb") as file:
        pickle.dump(payload, file)


def main() -> None:
    parser = argparse.ArgumentParser(description="Index SC judgments for PrecedentForecaster.")
    parser.add_argument("--corpus-dir", type=Path, default=CASE_CORPUS_DIR)
    parser.add_argument("--reset", action="store_true", help="Clear and rebuild Chroma.")
    parser.add_argument(
        "--max-files",
        type=int,
        default=MAX_INDEX_FILES,
        help="Limit indexed files for faster local/Docker startup. Use 0 for the full corpus.",
    )
    args = parser.parse_args()

    if not args.corpus_dir.exists():
        raise FileNotFoundError(f"Corpus directory not found: {args.corpus_dir}")

    max_files = args.max_files if args.max_files > 0 else None
    documents = build_documents(args.corpus_dir, max_files=max_files)
    if not documents:
        raise RuntimeError(f"No .txt judgments found in {args.corpus_dir}")

    print(f"Prepared {len(documents)} chunks from {args.corpus_dir}")
    build_vector_index(documents, reset=args.reset)
    build_bm25_index(documents)
    print(f"Chroma index: {CHROMA_DIR}")
    print(f"BM25 index:   {BM25_PATH}")


if __name__ == "__main__":
    main()
