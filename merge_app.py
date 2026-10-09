import os

with open('backend/app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.startswith('from rag_engine import ('):
        new_lines.append('import tempfile\n')
        new_lines.append('from document_intelligence import (\n')
        new_lines.append('    DocumentCorpusStore,\n')
        new_lines.append('    analyze_contract,\n')
        new_lines.append('    decode_court_notice,\n')
        new_lines.append('    extract_text,\n')
        new_lines.append(')\n')
        new_lines.append('from legal_doc_intel import build_legal_document_report\n')
        new_lines.append(line)
    elif line.startswith('rag_index = HybridRAGIndex()'):
        new_lines.append(line)
        new_lines.append('doc_store = DocumentCorpusStore()\n')
    elif 'rag_index.build(text, chunk_size=2000, overlap=400, domain="general")' in line:
        new_lines.append('        extra_corpus = doc_store.combined_text()\n')
        new_lines.append('        if extra_corpus.strip():\n')
        new_lines.append('            text = f"{text}\\n\\n{extra_corpus}"\n')
        new_lines.append('        if text.strip():\n')
        new_lines.append('            rag_index.build(text, chunk_size=2000, overlap=400, domain="general")\n')
    elif line.startswith('    return jsonify({') and 'domain_counts' in ''.join(lines[-20:]):
        # We are in health endpoint
        new_lines.append(line)
    elif line.strip() == '"index_chunks": len(rag_index.chunks),':
        new_lines.append(line)
        new_lines.append('        "uploaded_docs": len(doc_store.list_docs()),\n')
    else:
        new_lines.append(line)

# Add generate_text_report and the new routes at the end of the file, just before test_rights_module or health
# Actually let's just append them before the @app.route('/health')
final_lines = []
for idx, line in enumerate(new_lines):
    if line.startswith('@app.route(\'/health\', methods=[\'GET\'])'):
        final_lines.append('''
def generate_text_report(prompt: str) -> str:
    if LLM_PROVIDER == "gemini" and gemini_available and model is not None:
        try:
            import google.generativeai as genai
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0,
                    max_output_tokens=4096,
                ),
            )
            return (response.text or "").strip()
        except Exception as e:
            print(f"[WARN] Gemini text generation error: {e}")
            return ""

    if LLM_PROVIDER == "ollama":
        url = OLLAMA_HOST.rstrip("/") + "/api/generate"
        import urllib.request, json
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": 4096, "temperature": 0},
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return (data.get("response") or "").strip()
        except Exception as e:
            print(f"[WARN] Ollama text generation error: {e}")
            return ""
    return ""

@app.route("/document-intel/upload", methods=["POST"])
def upload_document():
    global INDEX_BUILD_LOCK
    if "file" not in request.files:
        return jsonify({"error": "Upload a file in multipart form-data under key 'file'."}), 400

    uploaded = request.files["file"]
    if not uploaded or not uploaded.filename:
        return jsonify({"error": "No file selected."}), 400

    suffix = os.path.splitext(uploaded.filename)[1] or ".bin"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            uploaded.save(tmp.name)
            tmp_path = tmp.name

        text = extract_text(tmp_path)
        if not text.strip():
            return jsonify({"error": "No readable text found in the uploaded document."}), 422

        doc = doc_store.add(uploaded.filename, text)
        INDEX_BUILD_LOCK = False
        build_index()
        return jsonify(
            {
                "status": "ok",
                "doc_id": doc.doc_id,
                "name": doc.name,
                "chars_extracted": len(text),
                "uploaded_docs": doc_store.list_docs(),
                "index_chunks": len(rag_index.chunks),
            }
        )
    except Exception as e:
        return jsonify({"error": f"Document ingestion failed: {e}"}), 500
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

@app.route("/document-intel/summarize", methods=["POST"])
def summarize_document():
    if "file" not in request.files:
        return jsonify({"error": "Upload a file in multipart form-data under key 'file'."}), 400

    uploaded = request.files["file"]
    if not uploaded or not uploaded.filename:
        return jsonify({"error": "No file selected."}), 400

    export_pdf = str(request.form.get("export_pdf", "false")).lower() == "true"
    export_docx = str(request.form.get("export_docx", "false")).lower() == "true"

    suffix = os.path.splitext(uploaded.filename)[1] or ".bin"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            uploaded.save(tmp.name)
            tmp_path = tmp.name

        llm_fn = generate_text_report if ((LLM_PROVIDER == "ollama") or gemini_available) else None
        report = build_legal_document_report(
            file_path=tmp_path,
            filename=uploaded.filename,
            llm_text_fn=llm_fn,
            export_pdf=export_pdf,
            export_docx=export_docx,
        )
        return jsonify(report)
    except Exception as e:
        return jsonify({"error": f"Document summarization failed: {e}"}), 500
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

@app.route("/document-intel/contract-analyze", methods=["POST"])
def contract_analyze():
    data = request.json or {}
    contract_text = (data.get("text") or "").strip()
    if not contract_text:
        return jsonify({"error": "Missing 'text' in request body."}), 400
    return jsonify(analyze_contract(contract_text, rag_index))

@app.route("/document-intel/court-notice-decode", methods=["POST"])
def court_notice_decode():
    data = request.json or {}
    notice_text = (data.get("text") or "").strip()
    if not notice_text:
        return jsonify({"error": "Missing 'text' in request body."}), 400
    return jsonify(decode_court_notice(notice_text, rag_index))

@app.route("/", methods=["GET"])
def home():
    return jsonify(
        {
            "service": "NyayaSetu Backend API",
            "status": "ok",
            "message": "Backend is running. Open frontend on http://localhost:3000",
            "endpoints": [
                "/health",
                "/legal-help",
                "/document-intel/upload",
                "/document-intel/summarize",
                "/document-intel/contract-analyze",
                "/document-intel/court-notice-decode",
            ],
        }
    )
''')
        final_lines.append(line)
    else:
        final_lines.append(line)

with open('backend/app.py', 'w', encoding='utf-8') as f:
    f.writelines(final_lines)

print('Done')
