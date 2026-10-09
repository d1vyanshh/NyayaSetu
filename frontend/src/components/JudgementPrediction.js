import React, { useState } from 'react';
import './JudgementPrediction.css';

const SAMPLE_FACTS = [
  {
    label: 'Consumer warranty dispute',
    text: 'My refrigerator stopped working within 3 months of purchase. The company has ignored repeated service requests and refused refund or replacement despite warranty coverage.',
  },
  {
    label: 'Anticipatory bail',
    text: 'A false criminal complaint has been filed after a business dispute. Police may arrest me, but I have cooperated and there is no recovery or custodial interrogation needed.',
  },
  {
    label: 'Service termination',
    text: 'I was terminated from a government service post without proper notice or departmental enquiry, despite having completed several years of continuous work.',
  },
];

function outcomeClass(outcome) {
  return String(outcome || 'uncertain').toLowerCase();
}

function outcomeLabel(outcome) {
  const normalized = String(outcome || '').toUpperCase();
  if (normalized === 'ALLOWED') return 'Likely to succeed';
  if (normalized === 'PARTIAL') return 'May succeed partly';
  if (normalized === 'DISMISSED') return 'May be rejected';
  return 'Needs more information';
}

function estimateStrength(confidence) {
  const value = Number(confidence) || 0;
  if (value >= 80) return 'Strong match with past cases';
  if (value >= 60) return 'Good match with past cases';
  if (value >= 40) return 'Some matching past cases';
  return 'Limited matching past cases';
}

function verdictLabel(verdict) {
  return outcomeLabel(verdict);
}

function friendlyPlainEnglish(text) {
  return String(text || '')
    .replace(/\bALLOWED\b/g, 'likely to succeed')
    .replace(/\bPARTIAL\b/g, 'may succeed partly')
    .replace(/\bDISMISSED\b/g, 'may be rejected')
    .replace(/\bUNCERTAIN\b/g, 'needs more information')
    .replace(/\bcase_corpus\b/g, 'past case records')
    .replace(/\bconfidence\b/gi, 'estimate strength');
}

function JudgementPrediction() {
  const [facts, setFacts] = useState('');
  const [prediction, setPrediction] = useState(null);
  const [caseCount, setCaseCount] = useState(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const runPrediction = async (requestedCaseCount = caseCount) => {
    if (!facts.trim()) {
      setError('Describe the material facts before running prediction.');
      return;
    }
    const nextCaseCount = Math.max(5, Math.min(20, requestedCaseCount));
    setLoading(true);
    setError('');
    setPrediction(null);
    try {
      const response = await fetch('http://127.0.0.1:5555/judgement-prediction', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ facts, case_count: nextCaseCount }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || 'Prediction failed.');
      }
      setCaseCount(nextCaseCount);
      setPrediction(data);
    } catch (err) {
      setError(err.message || 'Cannot connect to judgement prediction backend.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="jp-root">
      <section className="jp-hero">
        <div className="jp-hero-copy">
          <span className="jp-kicker">Judgement Predictor Module</span>
          <h1>Compare your scenario with similar <span className="jp-highlight">court hearings</span></h1>
          <p>
            Share the facts and NyayaSetu surfaces comparable rulings and patterns to guide your next steps.
          </p>
        </div>
        <div className="jp-module-card">
          <span className="jp-section-label">What you get</span>
          {prediction && <strong>{`Outcome snapshot: ${prediction.predicted_outcome}`}</strong>}
          <p>
            {prediction
              ? `${prediction.success_probability}% likelihood based on similar hearings.`
              : 'Submit your facts to see outcome trends, risks, and next steps.'}
          </p>
          <ul className="jp-module-list">
            <li>Similar hearing highlights and outcomes</li>
            <li>Do / avoid guidance grounded in precedents</li>
            <li>Evidence checklist to strengthen your position</li>
          </ul>
        </div>
      </section>

      <section className="jp-workbench">
        <div className="jp-input-panel">
          <div className="jp-panel-head">
            <div>
              <span className="jp-section-label">Case Facts</span>
              <h2>Describe the dispute</h2>
            </div>
            <span className="jp-live-pill">Local precedents</span>
          </div>
          <textarea
            value={facts}
            onChange={(event) => setFacts(event.target.value)}
            placeholder="Example: I bought a washing machine under warranty. It failed within four months, the company ignored service requests, and I want refund or replacement..."
          />
          <div className="jp-actions">
            <button type="button" onClick={() => runPrediction(5)} disabled={loading}>
              {loading ? 'Predicting...' : 'Predict Judgement'}
            </button>
            <button type="button" className="jp-clear" onClick={() => { setFacts(''); setPrediction(null); setCaseCount(5); }}>
              Clear
            </button>
          </div>
          <div className="jp-samples">
            {SAMPLE_FACTS.map(sample => (
              <button key={sample.label} type="button" onClick={() => setFacts(sample.text)}>
                {sample.label}
              </button>
            ))}
          </div>
          {error && <div className="jp-error">{error}</div>}
        </div>

        <div className="jp-status-panel">
          {loading ? (
            <div className="jp-loader">
              <div className="jp-loader-ring" />
              <h3>Reading precedents</h3>
              <p>Retrieving similar hearings and comparing outcomes.</p>
              <p>Retrieving similar hearings and comparing outcomes.</p>
            </div>
          ) : prediction ? (
            <PredictionResult
              prediction={prediction}
              loading={loading}
              onShowMore={() => runPrediction((prediction.similar_cases?.length || caseCount) + 5)}
            />
          ) : (
            <div className="jp-empty">
              <span>01</span>
              <h3>Awaiting facts</h3>
              <p>The prediction will show a likely outcome, similar cases, practical steps, and points to be careful about.</p>
            </div>
          )}
        </div>
      </section>
    </main>
  );
}

function PredictionResult({ prediction, onShowMore, loading }) {
  const doItems = prediction.do_this?.length ? prediction.do_this : prediction.recommended_actions;
  const avoidItems = prediction.avoid_this?.length ? prediction.avoid_this : prediction.risk_factors;
  const retrieved = prediction.corpus_stats?.cases_retrieved || prediction.similar_cases?.length || 0;
  const loaded = prediction.corpus_stats?.cases_loaded || 0;
  const canShowMore = retrieved < Math.min(20, loaded || 20);

  return (
    <div className="jp-result">
      <div className={`jp-outcome ${outcomeClass(prediction.predicted_outcome)}`}>
        <span>Likely result</span>
        <strong>{outcomeLabel(prediction.predicted_outcome)}</strong>
        <p>{prediction.issue_identified}</p>
      </div>

      <div className="jp-metrics">
        <Metric label="Chance of a favourable result" value={`${prediction.success_probability}%`} />
        <Metric label="Strength of the estimate" value={estimateStrength(prediction.confidence)} />
        <Metric label="Past cases checked" value={prediction.corpus_stats?.cases_loaded || '0'} />
      </div>

      <section className="jp-note full">
        <span className="jp-section-label">Plain English</span>
        <p>{friendlyPlainEnglish(prediction.plain_english)}</p>
      </section>

      <SimilarCases cases={prediction.similar_cases || []} onShowMore={onShowMore} canShowMore={canShowMore} loading={loading} />

      <section className="jp-decision-grid full">
        <ListCard title="Do this" items={doItems} tone="green" />
        <ListCard title="Avoid this" items={avoidItems} tone="red" />
      </section>

      <Misconceptions items={prediction.misconceptions || []} />

      {prediction.ratio_analysis?.length > 0 && (
        <section className="jp-note full">
          <span className="jp-section-label">Ratio Comparison</span>
          <div className="jp-ratio-list">
            {prediction.ratio_analysis.map((item, index) => (
              <div key={`${item.source_file}-${index}`} className="jp-ratio-item">
                <div>
                  <strong>{item.source_file}</strong>
                  <span>{outcomeLabel(item.leans)}</span>
                </div>
                <p>{item.principle}</p>
                <small>{item.comparison}</small>
              </div>
            ))}
          </div>
        </section>
      )}

      <ListCard title="Evidence Needed" items={prediction.evidence_needed} tone="blue" />
      <StatsStrip prediction={prediction} />
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div className="jp-metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function ListCard({ title, items = [], tone }) {
  return (
    <section className={`jp-note jp-list-card ${tone || ''}`}>
      <span className="jp-section-label">{title}</span>
      <ul>
        {(items.length ? items : ['No items returned.']).map((item, index) => (
          <li key={`${item}-${index}`}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

function SimilarCases({ cases, onShowMore, canShowMore, loading }) {
  return (
    <section className="jp-note full">
      <span className="jp-section-label">Similar cases decided by courts</span>
      <div className="jp-cases">
        {cases.map((item, index) => {
          const percent = Math.round((item.similarity || 0) * 100);
          return (
            <article key={`${item.source_file}-${index}`} className="jp-case-card">
              <div className="jp-case-top">
                <span>{item.topic}</span>
                <strong>{percent}%</strong>
              </div>
              {item.case_verdict && (
                <div className={`jp-case-verdict ${String(item.case_verdict).toLowerCase()}`}>
                  Court result: {verdictLabel(item.case_verdict)}
                </div>
              )}
              <h4>{item.title}</h4>
              <p>{item.why_similar}</p>
              <div className="jp-match-track">
                <span style={{ width: `${Math.max(8, percent)}%` }} />
              </div>
              <small>{percent}% fact match with your situation</small>
            </article>
          );
        })}
      </div>
      {canShowMore && (
        <button type="button" className="jp-more-cases" onClick={onShowMore} disabled={loading}>
          {loading ? 'Finding more cases...' : `Show more similar cases`}
        </button>
      )}
    </section>
  );
}

function Misconceptions({ items }) {
  if (!items.length) {
    return null;
  }
  return (
    <section className="jp-note full">
      <span className="jp-section-label">Common misconceptions - click to reveal</span>
      <div className="jp-misconceptions">
        {items.map((item, index) => (
          <details key={`${item.statement}-${index}`} className="jp-misconception">
            <summary>
              <span>"{item.statement}"</span>
              <strong>{item.verdict}</strong>
            </summary>
            <p>Check this against the retrieved precedents and the applicable statute before acting.</p>
          </details>
        ))}
      </div>
    </section>
  );
}

function StatsStrip({ prediction }) {
  const stats = [
    ['Past cases shown', `${prediction.corpus_stats?.cases_retrieved || 0}`],
    ['Past cases available', `${prediction.corpus_stats?.cases_loaded || 0}`],
    ['Estimate strength', estimateStrength(prediction.confidence)],
    ['Time limit', prediction.limitation_period || 'Verify with a lawyer'],
  ];
  return (
    <section className="jp-stats-strip full">
      {stats.map(([label, value]) => (
        <div key={label}>
          <span>{label}</span>
          <strong>{value}</strong>
        </div>
      ))}
    </section>
  );
}

export default JudgementPrediction;
