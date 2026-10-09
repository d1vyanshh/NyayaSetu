import React, { useEffect, useMemo, useRef, useState } from 'react';
import './NyayaDraft.css';

const API_BASE = process.env.REACT_APP_API_BASE || '';

function NyayaDraft() {
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [templateText, setTemplateText] = useState('');
  const [placeholders, setPlaceholders] = useState([]);
  const [values, setValues] = useState({});
  const [showPreview, setShowPreview] = useState(false);
  const [status, setStatus] = useState('');
  const [busy, setBusy] = useState('');
  const fileInputRef = useRef(null);

  useEffect(() => {
    loadTemplates();
  }, []);

  useEffect(() => {
    if (selectedTemplate) {
      loadTemplate(selectedTemplate);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedTemplate]);

  const completed = placeholders.filter(name => values[name]?.trim()).length;
  const progress = placeholders.length ? Math.round((completed / placeholders.length) * 100) : 0;
  const previewText = useMemo(
    () => replacePlaceholders(templateText, values),
    [templateText, values]
  );
  const downloadName = selectedTemplate
    ? `${selectedTemplate.replace(/\.txt$/i, '')}_draft.docx`
    : 'nyayadraft_document.docx';

  const loadTemplates = async () => {
    setBusy('templates');
    setStatus('');
    try {
      const response = await fetch(`${API_BASE}/nyayadraft/templates`);
      const data = await readJsonResponse(response, 'Unable to load templates.');
      if (!response.ok) {
        throw new Error(data.error || 'Unable to load templates.');
      }
      setTemplates(data.templates || []);
      if (data.templates?.length) {
        setSelectedTemplate(data.templates[0].name);
      } else {
        setStatus('No templates found. Upload a PDF or run the ingestion pipeline first.');
      }
    } catch (error) {
      setStatus(error.message || 'Unable to load templates.');
    } finally {
      setBusy('');
    }
  };

  const loadTemplate = async (templateName) => {
    setBusy('template');
    setStatus('');
    try {
      const response = await fetch(`${API_BASE}/nyayadraft/templates/${encodeURIComponent(templateName)}`);
      const data = await readJsonResponse(response, 'Unable to load selected template.');
      if (!response.ok) {
        throw new Error(data.error || 'Unable to load selected template.');
      }
      applyTemplate(data.text || '', data.placeholders || [], templateName);
    } catch (error) {
      setStatus(error.message || 'Unable to load selected template.');
    } finally {
      setBusy('');
    }
  };

  const applyTemplate = (text, names, sourceName = selectedTemplate) => {
    const uniqueNames = names.length ? names : extractPlaceholders(text);
    setTemplateText(text);
    setPlaceholders(uniqueNames);
    setShowPreview(false);
    setValues(previous => {
      const next = {};
      uniqueNames.forEach(name => {
        next[name] = previous[name] || '';
      });
      return next;
    });
    if (sourceName) {
      setSelectedTemplate(sourceName);
    }
  };

  const updateValue = (key, value) => {
    setValues(previous => ({ ...previous, [key]: value }));
  };

  const fillDemoValues = () => {
    if (!placeholders.length) {
      setStatus('Select a template with placeholders before loading a demo.');
      return;
    }

    const demoValues = {};
    placeholders.forEach((name, index) => {
      demoValues[name] = demoValueFor(name, index);
    });
    setValues(demoValues);
    setShowPreview(false);
    setStatus('Demo details added. Click Preview to see the sample draft.');
  };

  const previewDocument = () => {
    if (!templateText.trim()) {
      setStatus('Select a template before previewing.');
      return;
    }
    setShowPreview(true);
    setStatus('Preview generated.');
  };

  const downloadDocx = async () => {
    if (!templateText.trim()) {
      setStatus('Select a template before downloading.');
      return;
    }

    setBusy('download');
    setStatus('');
    try {
      const response = await fetch(`${API_BASE}/nyayadraft/docx`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: selectedTemplate ? selectedTemplate.replace(/\.txt$/i, '').replace(/_/g, ' ') : 'NyayaDraft Document',
          text: previewText,
        }),
      });
      const blob = await response.blob();
      if (!response.ok) {
        const message = await blob.text();
        throw new Error(message || 'Unable to generate document.');
      }
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = downloadName;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      setStatus('Document downloaded.');
    } catch (error) {
      setStatus(error.message || 'Download failed.');
    } finally {
      setBusy('');
    }
  };

  const sanitizePdf = async (event) => {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) {
      return;
    }

    setBusy('sanitize');
    setStatus(`Sanitizing ${file.name}...`);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const response = await fetch(`${API_BASE}/nyayadraft/sanitize-pdf`, {
        method: 'POST',
        body: formData,
      });
      const data = await readJsonResponse(response, 'PDF sanitization failed.');
      if (!response.ok) {
        throw new Error(data.error || 'PDF sanitization failed.');
      }
      const virtualName = `${file.name.replace(/\.pdf$/i, '')}_uploaded.txt`;
      applyTemplate(data.sanitized_text || '', data.placeholders || [], virtualName);
      setStatus(`Sanitized ${data.filename}: ${data.placeholder_count} placeholders found.`);
    } catch (error) {
      setStatus(error.message || 'PDF sanitization failed.');
    } finally {
      setBusy('');
    }
  };

  return (
    <main className="draft-root">
      <section className="draft-shell">
        <aside className="draft-sidebar">
          <div className="draft-sidebar-top">
            <div>
              <span>NyayaDraft</span>
              <h1>Document drafting</h1>
            </div>
          </div>

          <div className="draft-template-picker">
            <div className="draft-intro">
              <strong>How NyayaDraft works</strong>
              <p>
                Choose a legal template, fill each placeholder with case or party details,
                preview the completed document, and download it as an editable DOCX draft.
              </p>
            </div>
            <label>
              <span>Template</span>
              <select
                value={selectedTemplate}
                onChange={(event) => setSelectedTemplate(event.target.value)}
                disabled={busy === 'templates' || !templates.length}
              >
                {templates.length ? (
                  templates.map(template => (
                    <option key={template.name} value={template.name}>
                      {template.title}
                    </option>
                  ))
                ) : (
                  <option value="">No templates available</option>
                )}
              </select>
            </label>
          </div>

          <div className="draft-sidebar-actions">
            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf,.pdf"
              className="draft-file-input"
              onChange={sanitizePdf}
            />
            <button
              type="button"
              className="draft-secondary"
              onClick={() => fileInputRef.current?.click()}
              disabled={busy === 'sanitize'}
            >
              {busy === 'sanitize' ? 'Sanitizing...' : 'Upload PDF'}
            </button>
            <button
              type="button"
              className="draft-secondary"
              onClick={fillDemoValues}
              disabled={!placeholders.length}
            >
              Demo
            </button>
            <button
              type="button"
              onClick={previewDocument}
              disabled={!templateText.trim()}
            >
              Preview
            </button>
            <button
              type="button"
              onClick={downloadDocx}
              disabled={busy === 'download' || !templateText.trim()}
            >
              {busy === 'download' ? 'Preparing...' : 'Download .docx'}
            </button>
          </div>

          <div className="draft-progress">
            <strong>{placeholders.length} fields</strong>
            <em>{progress}% completed</em>
            <div className="draft-progress-meter">
              <span style={{ width: `${progress}%` }} />
            </div>
          </div>

          <form className="draft-form">
            {placeholders.length ? (
              placeholders.map(name => (
                <label key={name}>
                  <span>{placeholderLabel(name)}</span>
                  <input
                    value={values[name] || ''}
                    onChange={(event) => updateValue(name, event.target.value)}
                    placeholder={`Enter ${placeholderLabel(name).toLowerCase()}`}
                  />
                </label>
              ))
            ) : (
              <div className="draft-empty-state">
                Select a template with placeholders or upload a PDF to create one.
              </div>
            )}
          </form>
        </aside>

        <section className="draft-preview-panel">
          <div className="draft-toolbar">
            <div>
              <span>Preview</span>
              <strong>{selectedTemplate ? selectedTemplate.replace(/\.txt$/i, '').replace(/_/g, ' ') : 'No template selected'}</strong>
            </div>
            <div className="draft-toolbar-actions">
              <button type="button" onClick={loadTemplates} disabled={Boolean(busy)}>
                Refresh templates
              </button>
            </div>
          </div>
          {status && <div className="draft-status">{status}</div>}
          <article className="draft-document">
            {showPreview && templateText.trim() ? renderPreview(previewText) : (
              <p className="draft-document-empty">
                Fill the required fields and click Preview to see the final document here.
              </p>
            )}
          </article>
        </section>
      </section>
    </main>
  );
}

async function readJsonResponse(response, fallbackMessage) {
  const text = await response.text();
  try {
    return text ? JSON.parse(text) : {};
  } catch (error) {
    const cleanText = text.replace(/\s+/g, ' ').trim();
    throw new Error(cleanText || fallbackMessage);
  }
}

function extractPlaceholders(text) {
  const seen = new Set();
  const names = [];
  const pattern = /\{\{(.*?)\}\}/g;
  let match = pattern.exec(text);

  while (match) {
    const name = match[1].replace(/\s+/g, ' ').trim();
    if (name && !seen.has(name)) {
      seen.add(name);
      names.push(name);
    }
    match = pattern.exec(text);
  }

  return names;
}

function replacePlaceholders(text, values) {
  return text.replace(/\{\{(.*?)\}\}/g, (fullMatch, rawName) => {
    const name = rawName.replace(/\s+/g, ' ').trim();
    return values[name]?.trim() || fullMatch;
  });
}

function placeholderLabel(name) {
  const label = String(name || '').replace(/_/g, ' ').trim();
  return label.charAt(0).toUpperCase() + label.slice(1);
}

function demoValueFor(name, index) {
  const normalized = String(name || '').toLowerCase();
  const examples = [
    ['date', '18 May 2026'],
    ['day', 'Monday'],
    ['place', 'New Delhi'],
    ['city', 'New Delhi'],
    ['state', 'Delhi'],
    ['court', 'District Court, New Delhi'],
    ['name', 'Aarav Sharma'],
    ['party', 'Aarav Sharma'],
    ['client', 'Aarav Sharma'],
    ['applicant', 'Aarav Sharma'],
    ['respondent', 'Meera Kapoor'],
    ['address', '24, Civil Lines, New Delhi - 110054'],
    ['amount', 'Rs. 50,000'],
    ['rupee', 'Rs. 50,000'],
    ['company', 'NyayaSetu Legal Services Pvt. Ltd.'],
    ['firm', 'NyayaSetu Legal Services Pvt. Ltd.'],
    ['email', 'demo@nyayasetu.in'],
    ['phone', '+91 98765 43210'],
    ['mobile', '+91 98765 43210'],
    ['duration', '12 months'],
    ['term', '12 months'],
    ['rent', 'Rs. 25,000 per month'],
    ['salary', 'Rs. 6,00,000 per annum'],
    ['designation', 'Legal Associate'],
    ['witness', 'Rohan Mehta'],
  ];

  const match = examples.find(([keyword]) => normalized.includes(keyword));
  return match ? match[1] : `Sample detail ${index + 1}`;
}

function renderPreview(text) {
  return text.split(/\n+/).filter(Boolean).slice(0, 140).map((line, index) => {
    const cleanLine = line.trim();
    if (cleanLine.toUpperCase() === cleanLine && /[A-Z]/.test(cleanLine) && cleanLine.length < 140) {
      return <h2 key={index}>{cleanLine}</h2>;
    }
    const html = escapeHtml(cleanLine).replace(/\{\{(.*?)\}\}/g, '<span class="draft-placeholder">{{$1}}</span>');
    return <p key={index} dangerouslySetInnerHTML={{ __html: html }} />;
  });
}

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

export default NyayaDraft;
