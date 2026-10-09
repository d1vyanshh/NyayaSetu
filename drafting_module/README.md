# NyayaDraft

Automated legal document drafting module for NyayaSetu.

## Structure

```text
drafting_module/
  app.py                 # Streamlit UI, added in the next step
  ingestor.py            # PDF extraction and template creation
  processor.py           # Placeholder parsing and DOCX generation
  sanitizer.py           # Ollama cleanup, added in the next step
  requirements.txt
  legal_templates_pdf/   # Put raw legal PDFs here
  templates/             # AI-cleaned .txt templates are written here
  generated/             # Optional local output folder
```

## Current Flow

1. Put PDFs in `legal_templates_pdf/`.
2. Run `python ingestor.py`.
3. The ingestor extracts PDF text with `pdfplumber`.
4. The extracted text is passed to `sanitize_legal_text` from `sanitizer.py`.
5. Cleaned `.txt` templates are saved in `templates/`.
6. `processor.py` finds `{{placeholders}}`, fills them, and exports `.docx`.

