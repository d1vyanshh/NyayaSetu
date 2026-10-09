"""PDF ingestion pipeline for NyayaDraft.

This module reads raw legal PDFs, extracts text with pdfplumber, sends the
text through the NyayaDraft sanitizer, and saves cleaned .txt templates.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

import pdfplumber

try:
    from .sanitizer import sanitize_legal_text
except ImportError:
    try:
        from sanitizer import sanitize_legal_text
    except ImportError:
        sanitize_legal_text = None


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DEFAULT_PDF_DIR = PROJECT_ROOT / "legal_templates_pdf"
FALLBACK_PDF_DIR = BASE_DIR / "legal_templates_pdf"
TEMPLATE_DIR = BASE_DIR / "templates"

SanitizerFn = Callable[[str], str]


@dataclass(frozen=True)
class IngestionResult:
    """Summary of one PDF-to-template ingestion."""

    source_pdf: Path
    output_template: Path | None
    raw_characters: int
    cleaned_characters: int
    status: str
    message: str = ""


def get_pdf_dir() -> Path:
    """Return the preferred legal_templates_pdf directory."""
    if DEFAULT_PDF_DIR.exists():
        return DEFAULT_PDF_DIR
    return FALLBACK_PDF_DIR


def normalize_extracted_text(text: str) -> str:
    """Apply light cleanup before LLM sanitization."""
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()


def extract_text_from_pdf(pdf_path: str | Path) -> str:
    """Extract a raw text string from all pages in one PDF."""
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a .pdf file, got: {path.name}")

    page_texts: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text(x_tolerance=1, y_tolerance=3) or ""
            page_text = normalize_extracted_text(page_text)
            if page_text:
                page_texts.append(page_text)

    return "\n\n".join(page_texts).strip()


def discover_pdfs(input_dir: str | Path | None = None) -> list[Path]:
    """Read all .pdf files from legal_templates_pdf/."""
    folder = Path(input_dir) if input_dir else get_pdf_dir()
    folder.mkdir(parents=True, exist_ok=True)
    return sorted(path for path in folder.glob("*.pdf") if path.is_file())


def template_name_for_pdf(pdf_path: str | Path) -> str:
    """Build a safe .txt filename from a PDF filename."""
    stem = Path(pdf_path).stem.lower()
    stem = re.sub(r"[^a-z0-9]+", "_", stem).strip("_")
    return f"{stem or 'template'}.txt"


def ingest_pdf(
    pdf_path: str | Path,
    output_dir: str | Path = TEMPLATE_DIR,
    sanitizer: SanitizerFn | None = None,
    overwrite: bool = True,
) -> IngestionResult:
    """Extract, sanitize, and save one PDF as a .txt template."""
    source = Path(pdf_path)
    destination_dir = Path(output_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / template_name_for_pdf(source)

    if destination.exists() and not overwrite:
        return IngestionResult(
            source_pdf=source,
            output_template=destination,
            raw_characters=0,
            cleaned_characters=len(destination.read_text(encoding="utf-8")),
            status="skipped",
            message="Template already exists.",
        )

    raw_text = extract_text_from_pdf(source)
    if not raw_text:
        return IngestionResult(
            source_pdf=source,
            output_template=None,
            raw_characters=0,
            cleaned_characters=0,
            status="failed",
            message="No extractable text found in PDF.",
        )

    sanitizer_fn = sanitizer or sanitize_legal_text
    if sanitizer_fn is None:
        raise RuntimeError(
            "sanitize_legal_text is not available. Add drafting_module/sanitizer.py "
            "or pass a sanitizer function to ingest_pdf()."
        )

    cleaned_text = sanitizer_fn(raw_text).strip()
    if not cleaned_text:
        return IngestionResult(
            source_pdf=source,
            output_template=None,
            raw_characters=len(raw_text),
            cleaned_characters=0,
            status="failed",
            message="Sanitizer returned empty text.",
        )

    destination.write_text(cleaned_text + "\n", encoding="utf-8")
    return IngestionResult(
        source_pdf=source,
        output_template=destination,
        raw_characters=len(raw_text),
        cleaned_characters=len(cleaned_text),
        status="created",
        message="Template created successfully.",
    )


def ingest_all_pdfs(
    input_dir: str | Path | None = None,
    output_dir: str | Path = TEMPLATE_DIR,
    sanitizer: SanitizerFn | None = None,
    overwrite: bool = True,
) -> list[IngestionResult]:
    """Process every PDF in legal_templates_pdf/."""
    results: list[IngestionResult] = []
    for pdf_path in discover_pdfs(input_dir):
        try:
            results.append(
                ingest_pdf(
                    pdf_path=pdf_path,
                    output_dir=output_dir,
                    sanitizer=sanitizer,
                    overwrite=overwrite,
                )
            )
        except Exception as exc:
            results.append(
                IngestionResult(
                    source_pdf=pdf_path,
                    output_template=None,
                    raw_characters=0,
                    cleaned_characters=0,
                    status="failed",
                    message=str(exc),
                )
            )
    return results


def print_results(results: Iterable[IngestionResult]) -> None:
    """Print a compact ingestion report for CLI usage."""
    for result in results:
        output = result.output_template.name if result.output_template else "-"
        print(
            f"{result.status.upper():8} {result.source_pdf.name} -> {output} "
            f"raw={result.raw_characters} cleaned={result.cleaned_characters} "
            f"{result.message}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest legal template PDFs for NyayaDraft.")
    parser.add_argument(
        "--input-dir",
        default=None,
        help="Folder containing raw .pdf files. Defaults to legal_templates_pdf/.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(TEMPLATE_DIR),
        help="Folder for cleaned .txt templates.",
    )
    parser.add_argument(
        "--no-overwrite",
        action="store_true",
        help="Skip PDFs whose .txt template already exists.",
    )
    args = parser.parse_args()

    results = ingest_all_pdfs(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        overwrite=not args.no_overwrite,
    )
    if not results:
        print(f"No PDFs found in {args.input_dir or get_pdf_dir()}")
        return
    print_results(results)


if __name__ == "__main__":
    main()
