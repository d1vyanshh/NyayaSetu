import React, { useMemo, useState } from 'react';
import './AdvancedLegalTools.css';

const TOOL_CONFIG = {
  fairness: {
    label: 'Fairness Check',
    endpoint: '/api/fairness-check',
    method: 'POST',
    body: value => ({ situation: value }),
    placeholder: "My employer didn't pay me overtime for 3 months",
  },
  rights: {
    label: 'Rights Card',
    endpoint: '/api/rights-card',
    method: 'POST',
    body: value => ({ rights_type: value }),
    placeholder: 'arrest_rights',
  },
  scenario: {
    label: 'Scenario Simulator',
    endpoint: '/api/simulate-scenario',
    method: 'POST',
    body: value => ({ scenario: value }),
    placeholder: 'I was fired without notice after 4 years at my company',
  },
  translator: {
    label: 'Legal Translator',
    endpoint: '/api/translate',
    method: 'POST',
    body: (value, direction) => ({ text: value, direction }),
    placeholder: 'They locked me up without telling me why',
  },
  compare: {
    label: 'Article Compare',
    endpoint: '/api/compare-articles',
    method: 'POST',
    body: value => {
      const [article_a, article_b] = value.split(',').map(x => x.trim());
      return { article_a, article_b };
    },
    placeholder: '14, 21',
  },
  amendments: {
    label: 'Amendments',
    endpoint: '/api/amendments',
    method: 'GET',
    body: () => null,
    placeholder: 'Optional article number, e.g. 21',
  },
};

function confidenceLabel(confidence = 0) {
  if (confidence >= 0.75) return ['High Confidence', 'high'];
  if (confidence >= 0.45) return ['Moderate Confidence', 'moderate'];
  return ['Low Confidence - verify with a lawyer', 'low'];
}

function AdvancedLegalTools() {
  const [tool, setTool] = useState('fairness');
  const [input, setInput] = useState('');
  const [direction, setDirection] = useState('to_legal');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const config = TOOL_CONFIG[tool];
  const [badgeText, badgeTone] = confidenceLabel(result?.confidence || 0);
  const sources = useMemo(() => result?.explainability?.sources || [], [result]);

  const submit = async () => {
    setError('');
    setResult(null);
    setLoading(true);
    try {
      const normalizedInput = tool === 'rights' ? (input || 'arrest_rights') : input.trim();
      const path = tool === 'amendments' && input.trim()
        ? `${config.endpoint}/${encodeURIComponent(input.trim())}`
        : config.endpoint;
      const options = { method: config.method, headers: { 'Content-Type': 'application/json' } };
      if (config.method !== 'GET') {
        options.body = JSON.stringify(config.body(normalizedInput, direction));
      }
      const response = await fetch(`http://127.0.0.1:5555${path}`, options);
      const data = await response.json();
      if (!response.ok && response.status !== 501) throw new Error(data?.warnings?.[0] || data?.error || 'Request failed');
      setResult(data);
    } catch (err) {
      setError(err.message || 'Cannot reach backend.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="advanced-tools-page">
      <section className="advanced-tools-header">
        <div>
          <span className="advanced-kicker">Grounded legal reasoning</span>
          <h1>AI Legal Tools</h1>
          <p>Run specialized workflows that retrieve source law first, generate second, and show confidence plus warnings.</p>
        </div>
        <div className="advanced-status-panel">
          <strong>RAG enforced</strong>
          <span>Every tool returns explainability and source chunks.</span>
        </div>
      </section>

      <section className="tool-workbench">
        <div className="tool-tabs" role="tablist" aria-label="Legal reasoning tools">
          {Object.entries(TOOL_CONFIG).map(([id, item]) => (
            <button key={id} type="button" className={tool === id ? 'active' : ''} onClick={() => { setTool(id); setResult(null); }}>
              {item.label}
            </button>
          ))}
        </div>

        <div className="tool-input-panel">
          <label htmlFor="advanced-tool-input">{config.label}</label>
          {tool === 'rights' ? (
            <select id="advanced-tool-input" value={input || 'arrest_rights'} onChange={e => setInput(e.target.value)}>
              <option value="arrest_rights">Arrest rights</option>
              <option value="employment_rights">Employment rights</option>
              <option value="consumer_rights">Consumer rights</option>
              <option value="tenant_rights">Tenant rights</option>
              <option value="education_rights">Education rights</option>
            </select>
          ) : (
            <textarea
              id="advanced-tool-input"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder={config.placeholder}
              rows={tool === 'amendments' ? 2 : 5}
            />
          )}
          {tool === 'translator' && (
            <div className="segmented-control" aria-label="Translation direction">
              <button className={direction === 'to_legal' ? 'active' : ''} onClick={() => setDirection('to_legal')} type="button">To Legal</button>
              <button className={direction === 'to_plain' ? 'active' : ''} onClick={() => setDirection('to_plain')} type="button">To Plain</button>
            </div>
          )}
          <button type="button" className="run-tool-btn" onClick={submit} disabled={loading || (tool !== 'amendments' && tool !== 'rights' && !input.trim())}>
            {loading ? 'Running...' : 'Run Tool'}
          </button>
          {error && <div className="advanced-error">{error}</div>}
        </div>
      </section>

      {result && (
        <section className="advanced-result">
          <div className="advanced-result-top">
            <div>
              <span className="advanced-kicker">{result.feature}</span>
              <h2>{result.status}</h2>
            </div>
            <span className={`confidence-badge ${badgeTone}`}>{badgeText}</span>
          </div>

          {result.warnings?.length > 0 && (
            <div className="warning-banner">
              {result.warnings.map((warning, idx) => <span key={`${warning}-${idx}`}>{warning}</span>)}
            </div>
          )}

          <div className="advanced-output-grid">
            <pre>{JSON.stringify(result.data, null, 2)}</pre>
            <aside>
              <h3>Explainability</h3>
              <div className="explain-row"><span>Domain</span><strong>{result.explainability?.domain_filter_applied || 'all'}</strong></div>
              <div className="explain-row"><span>Chunks</span><strong>{result.explainability?.retrieved_chunks?.length || 0}</strong></div>
              <div className="explain-row"><span>Confidence</span><strong>{Math.round((result.confidence || 0) * 100)}%</strong></div>
              <h4>Sources</h4>
              <div className="source-list">
                {sources.length > 0 ? sources.map(source => <span key={source}>{source}</span>) : <span>No sources returned.</span>}
              </div>
            </aside>
          </div>
        </section>
      )}
    </div>
  );
}

export default AdvancedLegalTools;
