"""Load public legal PDFs into the shared RAG index with domain tags."""

from __future__ import annotations

import inspect
from pathlib import Path

import fitz


CORPUS_DOCUMENTS = {
    "wages_act_2019.pdf": {
        "domain": "labour",
        "source": "Code on Wages Act, 2019",
    },
    "shops_establishments_act.pdf": {
        "domain": "tenant",
        "source": "Maharashtra Shops and Establishments Act, 2017",
    },
    "consumer_protection_act_2019.pdf": {
        "domain": "consumer",
        "source": "Consumer Protection Act, 2019",
    },
    "domestic_violence_act_2005.pdf": {
        "domain": "domestic_violence",
        "source": "Protection of Women from Domestic Violence Act, 2005",
    },
}


def extract_text_from_pdf(pdf_path: str | Path) -> str:
    """Extract all text from a PDF file using PyMuPDF."""
    try:
        doc = fitz.open(str(pdf_path))
        try:
            return "\n".join(page.get_text() for page in doc)
        finally:
            doc.close()
    except Exception as exc:
        print(f"Error extracting text from PDF {pdf_path}: {exc}")
        return ""


def resolve_corpus_dir(corpus_dir: str | Path) -> Path:
    """Resolve corpus paths from either repo root or backend working directory."""
    given = Path(corpus_dir)
    candidates = [
        given,
        Path.cwd() / given,
        Path(__file__).resolve().parents[1] / given,
        Path(__file__).resolve().parents[1] / "corpus",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate.resolve()
    return given.resolve()


def _call_index_fn(index_fn, text: str, domain: str, source: str) -> None:
    """Call a shared-index build function with append/source when supported."""
    kwargs = {"domain": domain}
    params = inspect.signature(index_fn).parameters
    if "source" in params:
        kwargs["source"] = source
    if "append" in params:
        kwargs["append"] = True
    index_fn(text, **kwargs)


def load_legal_corpus(corpus_dir: str | Path, index_fn) -> list[dict]:
    """
    Load and index legal corpus PDFs with domain tags.

    Returns a load report so startup/tests can show exactly what was indexed.
    """
    resolved_dir = resolve_corpus_dir(corpus_dir)
    report = []

    for filename, meta in CORPUS_DOCUMENTS.items():
        full_path = resolved_dir / filename
        item = {
            "file": filename,
            "path": str(full_path),
            "domain": meta["domain"],
            "source": meta["source"],
            "indexed": False,
            "characters": 0,
        }

        if not full_path.exists():
            item["message"] = "file not found"
            print(f"Warning: {filename} not found in {resolved_dir}, skipping.")
            report.append(item)
            continue

        text = extract_text_from_pdf(full_path)
        if not text.strip():
            item["message"] = "no extractable text"
            print(f"Warning: No text extracted from {filename}, skipping.")
            report.append(item)
            continue

        _call_index_fn(index_fn, text, domain=meta["domain"], source=meta["source"])
        item["indexed"] = True
        item["characters"] = len(text)
        item["message"] = "indexed"
        print(f"Indexed: {filename} -> domain: {meta['domain']} -> source: {meta['source']}")
        report.append(item)

    return report
