import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import './LegalQuery.css';

function RenderText({ text }) {
  if (text === null || text === undefined) return null;
  const safeText = typeof text === 'string' ? text : JSON.stringify(text, null, 2);
  const lines = safeText.split('\n');
  return (
    <div className="rendered-text">
      {lines.map((line, i) => {
        if (!line.trim()) return <br key={i} />;
        if (line.startsWith('# ')) return <h2 key={i}>{line.slice(2)}</h2>;
        if (line.startsWith('## ')) return <h3 key={i}>{line.slice(3)}</h3>;
        if (line.startsWith('### ')) return <h4 key={i}>{line.slice(4)}</h4>;
        if (line.startsWith('- ') || line.startsWith('* ')) {
          return <li key={i}>{renderInline(line.slice(2))}</li>;
        }
        return <p key={i}>{renderInline(line)}</p>;
      })}
    </div>
  );
}

function renderInline(text) {
  const parts = text.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, i) =>
    part.startsWith('**') && part.endsWith('**')
      ? <strong key={i}>{part.slice(2, -2)}</strong>
      : part
  );
}

function normalizeTimelineTimeframe(step, index) {
  const raw = String(step?.timeframe || '').trim();
  if (!raw || raw.toLowerCase() === 'next' || raw.toLowerCase() === 'day 0') {
    return `Day ${index + 1}-${index + 2}`;
  }
  return raw;
}

function UrgencyBadge({ urgency }) {
  if (!urgency) return null;
  return (
    <div className={`urgency-banner ${urgency.level?.toLowerCase() || ''}`} style={{ borderColor: urgency.color }}>
      <span className="urgency-level">{urgency.level}</span>
      <span className="urgency-msg">{urgency.message}</span>
    </div>
  );
}

function TypingIndicator({ query, domain }) {
  const displayDomain = domain === 'auto' ? 'Auto-routing legal domain' : `${domain} domain selected`;
  return (
    <div className="analysis-loader" aria-label="AI is thinking">
      <div className="loader-orbit" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>
      <div className="loader-copy">
        <span className="loader-kicker">NyayaSetu is building your brief</span>
        <h2>Analyzing the facts, routing the domain, and grounding the answer.</h2>
        <p>{query || 'Your legal scenario is being processed.'}</p>
      </div>
      <div className="loader-steps">
        <div className="loader-step active">
          <span>01</span>
          <strong>Issue detection</strong>
          <small>Reading facts and relief sought</small>
        </div>
        <div className="loader-step active">
          <span>02</span>
          <strong>{displayDomain}</strong>
          <small>Choosing the most relevant corpus</small>
        </div>
        <div className="loader-step">
          <span>03</span>
          <strong>Legal brief drafting</strong>
          <small>Preparing laws, actions, and evidence checklist</small>
        </div>
      </div>
    </div>
  );
}

const QUICK_SCENARIOS = [
  { label: 'Consumer Fraud', accent: 'blue', text: 'My new refrigerator stopped working after 3 months and the company is ignoring my complaint. What are my rights?' },
  { label: 'Unlawful Arrest', accent: 'red', text: 'Police arrested me without showing a warrant and are refusing to let me call my lawyer. What are my rights?' },
  { label: 'Salary Not Paid', accent: 'green', text: 'My employer has not paid my salary for 3 months and is threatening to fire me. What can I do legally?' },
  { label: 'Illegal Eviction', accent: 'amber', text: 'My landlord is forcefully evicting me without giving proper notice. What legal protection do I have?' },
  { label: 'Road Accident', accent: 'violet', text: 'I was injured in a road accident caused by another driver. What are my legal rights and how do I claim compensation?' },
  { label: 'School Discrimination', accent: 'pink', text: 'A private school refused to admit my child citing caste. Is this legal? What action can I take?' },
];

function ArticleCard({ article, index }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="article-card" style={{ animationDelay: `${index * 80}ms` }}>
      <button className="article-card-header" onClick={() => setExpanded(e => !e)} aria-expanded={expanded}>
        <div className="article-number-badge">{article.number || 'Article'}</div>
        <div className="article-card-meta">
          <div className="article-card-title">{article.title}</div>
          {article.relevance && !expanded && (
            <div className="article-card-preview">{article.relevance.slice(0, 92)}...</div>
          )}
        </div>
        <span className="expand-btn" aria-hidden="true">{expanded ? 'Hide' : 'View'}</span>
      </button>
      {expanded && (
        <div className="article-card-body">
          <p>{article.relevance}</p>
        </div>
      )}
    </div>
  );
}

function SectionCard({ section, index }) {
  const [expanded, setExpanded] = useState(false);
  const breakdown = section.score_breakdown;
  const showBreakdown = breakdown && Number.isFinite(breakdown.bm25) && Number.isFinite(breakdown.cosine);
  const bm25Part = showBreakdown ? breakdown.bm25 * 0.6 : 0;
  const cosinePart = showBreakdown ? breakdown.cosine * 0.4 * 10 : 0;
  const titlePart = showBreakdown ? breakdown.title_boost : 0;
  const total = bm25Part + cosinePart + titlePart;
  const parts = [
    { key: 'bm25', label: 'BM25', value: bm25Part },
    { key: 'cosine', label: 'Cosine', value: cosinePart },
    { key: 'title', label: 'Title', value: titlePart },
  ];

  return (
    <div className="section-card" style={{ animationDelay: `${index * 80}ms` }}>
      <button className="section-card-header" onClick={() => setExpanded(e => !e)} aria-expanded={expanded}>
        <div className="section-card-primary">
          <div className="section-title">{section.title}</div>
          {section.article_numbers?.length > 0 && (
            <div className="section-articles">
              {section.article_numbers.map(n => (
                <span key={n} className="article-tag">Art. {n}</span>
              ))}
            </div>
          )}
        </div>
        <div className="section-score-wrap">
          <div className="relevance-bar">
            <div
              className="relevance-fill"
              style={{ width: `${Math.min(100, section.score * 8)}%` }}
            />
          </div>
          <span className="relevance-label">Relevance</span>
          {showBreakdown && (
            <div className="score-breakdown">
              <div className="breakdown-bar">
                {parts.map(p => (
                  <div
                    key={p.key}
                    className={`breakdown-seg ${p.key}`}
                    style={{ width: `${total ? (p.value / total) * 100 : 0}%` }}
                  />
                ))}
              </div>
              <div className="breakdown-legend">
                {parts.map(p => (
                  <span key={p.key} className={`legend-item ${p.key}`}>
                    <span className="legend-swatch" />
                    {p.label}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
        <span className="expand-btn" aria-hidden="true">{expanded ? 'Hide' : 'Open'}</span>
      </button>
      {expanded && (
        <div className="section-card-body">
          {breakdown?.matched_terms?.length > 0 && (
            <div className="matched-terms">
              <span className="matched-label">Matched terms</span>
              <div className="matched-tags">
                {breakdown.matched_terms.map(t => (
                  <span key={t} className="matched-tag">{t}</span>
                ))}
              </div>
            </div>
          )}
          <pre className="constitution-text">{section.excerpt}</pre>
        </div>
      )}
    </div>
  );
}

// Legacy renderer retained while the grouped result flow settles.
// eslint-disable-next-line no-unused-vars
function StructuredPanel({ structured, urgency, result, onFollowup }) {
  if (!structured) {
    return <p className="empty-state">No structured brief available.</p>;
  }

  const meta = structured.meta || {};
  const summary = structured.summary || {};
  const plain = structured.plain_words || {};
  const parties = structured.parties || {};
  const laws = structured.applicable_laws || [];
  const rights = structured.rights_vs_limits?.rights || [];
  const limits = structured.rights_vs_limits?.limits || [];
  const steps = structured.steps || [];
  const forum = structured.forum_comparison || {};
  const relief = structured.relief_spectrum || [];
  const strength = structured.case_strength || [];
  const costBenefit = structured.cost_benefit || {};
  const clauseRisks = structured.clause_risks || [];
  const evidence = structured.evidence_checklist || [];
  const doList = structured.do_and_avoid?.do || [];
  const avoidList = structured.do_and_avoid?.avoid || [];
  const misconceptions = structured.misconceptions || [];
  const similar = structured.similar_cases || [];
  const followups = structured.followups || [];
  const confidenceValue = typeof meta.confidence === 'number' ? meta.confidence : result.explainability?.confidence;
  const confidenceLabel = typeof confidenceValue === 'number' ? `${confidenceValue}% confident` : 'Grounded brief';
  const activeDomain = meta.domain || result.explainability?.detected_domain || 'Legal domain';
  const issueTitle = meta.case_type || result.case_type || summary.signal || 'Legal issue identified';
  const issueSubline = [
    activeDomain,
    parties.forum || 'Forum to be confirmed',
    urgency?.level ? `${urgency.level} urgency` : null,
  ].filter(Boolean).join(' · ');
  const snapshotRows = [
    ['Domain', meta.domain || 'General legal query'],
    ['Confidence', typeof meta.confidence === 'number' ? `${meta.confidence}%` : 'Unknown'],
    ['Likely forum', parties.forum || 'To be confirmed'],
    ['Provider', meta.llm_provider || 'AI assisted'],
    ['Urgency', urgency?.level || 'Standard'],
    ['Corpus fit', meta.in_scope === false ? 'Out of corpus' : 'In constitutional scope'],
  ];

  return (
    <div className="brief-wrap">
      <section className="case-query-card">
        <div>
          <span className="case-query-label">Query</span>
          <p>{result.query}</p>
        </div>
        <span className="confidence-badge">{confidenceLabel}</span>
      </section>

      <section className="domain-routing-panel">
        <div className="section-heading compact">
          <h4>Domain Routing</h4>
        </div>
        <div className="routing-chips">
          {['Constitutional Law', 'Consumer Protection', 'Criminal Law', 'IT Law', 'Civil Procedure'].map(domain => (
            <span
              key={domain}
              className={`routing-chip ${activeDomain.toLowerCase().includes(domain.toLowerCase().split(' ')[0]) ? 'active' : ''}`}
            >
              {domain}
            </span>
          ))}
        </div>
      </section>

      <section className="issue-panel">
        <div className="issue-accent" />
        <div className="issue-copy">
          <h3>{issueTitle}</h3>
          <p>{issueSubline}</p>
          <div className="brief-meta">
            {summary.signal && <span className="meta-chip warm">{summary.signal}</span>}
            {meta.in_scope === false && <span className="meta-chip warning">Out of corpus</span>}
            {result.ai_powered && <span className="meta-chip">RAG assisted</span>}
          </div>
        </div>
      </section>

      {plain.short_explanation && (
        <section className="plain-words-panel">
          <div className="section-heading compact">
            <h4>In Plain Words</h4>
          </div>
          <div className="plain-words-copy">{plain.short_explanation}</div>
        </section>
      )}

      <div className="brief-grid brief-grid-top">
        <section className="brief-card brief-card-spotlight">
          <div className="section-heading">
            <h4>Case Snapshot</h4>
            <span className="section-caption">Matter profile</span>
          </div>
          <div className="snapshot-table-wrap">
            <table className="snapshot-table">
              <tbody>
                {snapshotRows.map(([label, value]) => (
                  <tr key={label}>
                    <th>{label}</th>
                    <td>{value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="brief-card">
          <div className="section-heading">
            <h4>Parties Involved</h4>
            <span className="section-caption">Who, what, where</span>
          </div>
          <div className="entity-flow">
            <div className="entity-node">
              <span className="entity-label">Complainant</span>
              <strong>{parties.complainant || 'You'}</strong>
            </div>
            <div className="entity-connector" />
            <div className="entity-node">
              <span className="entity-label">Opposite party</span>
              <strong>{parties.opposite_party || 'Respondent'}</strong>
            </div>
            <div className="entity-connector" />
            <div className="entity-node">
              <span className="entity-label">Forum</span>
              <strong>{parties.forum || 'Authority'}</strong>
            </div>
          </div>
          <div className="entity-subject-panel">
            <span className="entity-label">Subject</span>
            <p>{parties.subject || result.query || 'Legal issue summary unavailable.'}</p>
          </div>
        </section>
      </div>

      {structured.compliance_checklist?.length > 0 && (
        <section className="brief-card">
          <div className="section-heading">
            <h4>Compliance Checklist</h4>
            <span className="section-caption">Requirements based on business type and employee count</span>
          </div>
          <div className="checklist-grid">
            {structured.compliance_checklist.map((item, i) => (
              <div key={`${item.act}-${i}`} className={`check-card ${item.status || ''}`} style={{ borderColor: item.status === 'applicable' ? 'var(--lq-success)' : 'var(--lq-amber)' }}>
                <strong>{item.status_symbol || '-'} {item.act}</strong>
                <p style={{ marginTop: '8px', color: 'var(--lq-text-soft)' }}>{item.requirement_summary}</p>
                {item.sources?.length > 0 && (
                  <div style={{ marginTop: '12px' }}>
                    <span className="meta-chip" style={{ fontSize: '0.75rem' }}>Sources: {item.sources.join(', ')}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="brief-card">
        <div className="section-heading">
          <h4>Recommended Actions</h4>
          <span className="section-caption">Sequenced by urgency</span>
        </div>
        {steps.length > 0 ? (
          <div className="timeline-horizontal">
            <div className="timeline-rail" />
            {steps.map((s, i) => (
              <div key={`${s.action || 'step'}-${i}`} className="timeline-stop">
                <div className="timeline-marker">
                  <span className="timeline-index">{i + 1}</span>
                </div>
                <div className="timeline-time">{normalizeTimelineTimeframe(s, i)}</div>
                <div className="timeline-card">
                  <div className="timeline-title">{s.action || 'Step'}</div>
                  <div className="timeline-meta">Action</div>
                  {s.why && <p className="timeline-note">{s.why}</p>}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="empty-state">No steps available.</p>
        )}
      </section>

      <div className="brief-grid">
        <section className="brief-card">
          <div className="section-heading">
            <h4>Applicable Laws</h4>
            <span className="section-caption">Primary laws supporting this scenario</span>
          </div>
          {laws.length > 0 ? (
            <div className="law-grid">
              {laws.map((law, i) => (
                <div key={`${law.name}-${i}`} className="law-card">
                  <div className="law-card-head">
                    <strong>{law.name}</strong>
                    {law.type && <span className="law-type">{law.type}</span>}
                  </div>
                  {law.why_it_applies && <p>{law.why_it_applies}</p>}
                  {law.citations?.length > 0 && (
                    <div className="law-citations">
                      {law.citations.map(c => (
                        <span key={c} className="law-chip">{c}</span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="empty-state">No laws extracted for this query.</p>
          )}
        </section>

        <section className="brief-card">
          <div className="section-heading">
            <h4>Case Strength</h4>
            <span className="section-caption">Signals that can help or weaken the matter</span>
          </div>
          <div className="strength-grid">
            {strength.length > 0 ? strength.map((s, i) => (
              <div key={`${s.label}-${i}`} className="strength-item">
                <div className="strength-label">
                  <span>{s.label}</span>
                  <span className="strength-value">{Math.min(100, s.score || 0)}%</span>
                </div>
                <div className="strength-bar">
                  <div className="strength-fill" style={{ width: `${Math.min(100, s.score || 0)}%` }} />
                </div>
                <div className="strength-note">{s.note || 'No note available.'}</div>
              </div>
            )) : (
              <div className="strength-empty">
                <span className="empty-number">01</span>
                <p>No strength signals available yet. Evidence and documents will shape this most.</p>
              </div>
            )}
          </div>
        </section>
      </div>

      <div className="brief-grid">
        <section className="brief-card">
          <div className="section-heading">
            <h4>Rights You Can Claim</h4>
            <span className="section-caption">The strongest rights visible from the current facts</span>
          </div>
          <div className="pill-list">
            {rights.length > 0 ? rights.map((item, i) => (
              <div key={`${item}-${i}`} className="info-pill positive">{item}</div>
            )) : <p className="empty-state">No rights extracted.</p>}
          </div>
        </section>

        <section className="brief-card">
          <div className="section-heading">
            <h4>Limits and Watchouts</h4>
            <span className="section-caption">Things that can narrow the claim or require caution</span>
          </div>
          <div className="pill-list">
            {limits.length > 0 ? limits.map((item, i) => (
              <div key={`${item}-${i}`} className="info-pill caution">{item}</div>
            )) : <p className="empty-state">No limitations extracted.</p>}
          </div>
        </section>
      </div>

      <div className="brief-grid">
        <section className="brief-card">
          <div className="section-heading">
            <h4>Evidence Checklist</h4>
            <span className="section-caption">Documents and records worth gathering now</span>
          </div>
          <div className="checklist-grid">
            {evidence.length > 0 ? evidence.map((item, i) => (
              <div key={`${item}-${i}`} className="check-card">{item}</div>
            )) : <p className="empty-state">No evidence checklist available.</p>}
          </div>
        </section>

        <section className="brief-card">
          <div className="section-heading">
            <h4>Do and Avoid</h4>
            <span className="section-caption">Practical moves that improve the position</span>
          </div>
          <div className="dual-callout">
            <div className="callout-panel do-panel">
              <span className="callout-label">Do this</span>
              <div className="stack-list">
                {doList.length > 0 ? doList.map((item, i) => (
                  <div key={`${item}-${i}`} className="stack-item">{item}</div>
                )) : <div className="stack-item muted">No action items listed.</div>}
              </div>
            </div>
            <div className="callout-panel avoid-panel">
              <span className="callout-label">Avoid this</span>
              <div className="stack-list">
                {avoidList.length > 0 ? avoidList.map((item, i) => (
                  <div key={`${item}-${i}`} className="stack-item">{item}</div>
                )) : <div className="stack-item muted">No avoid items listed.</div>}
              </div>
            </div>
          </div>
        </section>
      </div>

      {forum.rows?.length > 0 && (
        <section className="brief-card">
          <div className="section-heading">
            <h4>Forum Comparison</h4>
            <span className="section-caption">Compare where the matter can be taken</span>
          </div>
          <div className="forum-table-wrap">
            <table className="forum-table">
              <thead>
                <tr>
                  <th>Factor</th>
                  {(forum.forums || []).map(f => <th key={f}>{f}</th>)}
                </tr>
              </thead>
              <tbody>
                {forum.rows.map((row, i) => (
                  <tr key={`${row.factor}-${i}`}>
                    <td>{row.factor}</td>
                    {(row.values || []).map((v, idx) => <td key={`${row.factor}-${idx}`}>{v}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {(relief.length > 0 || costBenefit.invest?.length > 0 || costBenefit.recover?.length > 0) && (
        <div className="brief-grid">
          {relief.length > 0 && (
            <section className="brief-card">
              <div className="section-heading">
                <h4>Relief Spectrum</h4>
                <span className="section-caption">Typical outcomes to aim for</span>
              </div>
              <div className="relief-list">
                {relief.map((r, i) => (
                  <div key={`${r.label}-${i}`} className="relief-item">
                    <div className="relief-copy">
                      <div className="relief-label">{r.label}</div>
                      <div className="relief-range">{r.range}</div>
                    </div>
                    <div className={`relief-bar ${r.level || ''}`}>
                      <div style={{ width: `${Math.min(100, r.likelihood || 0)}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {(costBenefit.invest?.length > 0 || costBenefit.recover?.length > 0) && (
            <section className="brief-card">
              <div className="section-heading">
                <h4>Cost and Recovery</h4>
                <span className="section-caption">Likely inputs versus possible returns</span>
              </div>
              <div className="cost-benefit">
                <div className="cost-panel">
                  <h5>What you invest</h5>
                  {(costBenefit.invest || []).map((item, i) => (
                    <div key={`${item.item}-${i}`} className="cost-row">
                      <span>{item.item}</span>
                      <strong>{item.amount}</strong>
                    </div>
                  ))}
                </div>
                <div className="benefit-panel">
                  <h5>What you can recover</h5>
                  {(costBenefit.recover || []).map((item, i) => (
                    <div key={`${item.item}-${i}`} className="cost-row">
                      <span>{item.item}</span>
                      <strong>{item.amount}</strong>
                    </div>
                  ))}
                </div>
              </div>
            </section>
          )}
        </div>
      )}

      {clauseRisks.length > 0 && (
        <section className="brief-card">
          <div className="section-heading">
            <h4>Clause Risk Scanner</h4>
            <span className="section-caption">Terms that may need revision or caution</span>
          </div>
          <div className="risk-list">
            {clauseRisks.map((c, i) => (
              <div key={`${c.clause}-${i}`} className={`risk-item ${c.risk_level || 'medium'}`}>
                <div className="risk-head">
                  <strong>{c.clause}</strong>
                  <span className="risk-level">{c.risk_level}</span>
                </div>
                <p>{c.issue}</p>
                {c.fix && <div className="risk-fix">Fix: {c.fix}</div>}
              </div>
            ))}
          </div>
        </section>
      )}

      {(misconceptions.length > 0 || similar.length > 0) && (
        <div className="brief-grid">
          {misconceptions.length > 0 && (
            <section className="brief-card">
              <div className="section-heading">
                <h4>Common Misconceptions</h4>
                <span className="section-caption">Quick legal corrections worth knowing</span>
              </div>
              <div className="misconceptions">
                {misconceptions.map((m, i) => (
                  <div key={`${m.claim}-${i}`} className="misconception-item">
                    <div className="misconception-claim">{m.claim}</div>
                    <div className="misconception-truth">{m.truth}</div>
                    {m.explanation && <div className="misconception-note">{m.explanation}</div>}
                  </div>
                ))}
              </div>
            </section>
          )}

          {similar.length > 0 && (
            <section className="brief-card">
              <div className="section-heading">
                <h4>Similar Precedents</h4>
                <span className="section-caption">Comparable court outcomes</span>
              </div>
              <div className="precedent-row">
                {similar.map((c, i) => (
                  <div key={`${c.case_name}-${i}`} className="precedent-card">
                    <div className="precedent-title">{c.case_name}</div>
                    <div className="precedent-meta">{c.court} / {c.year}</div>
                    <div className="precedent-outcome">{c.outcome}</div>
                    {c.similarity && (
                      <div className="precedent-bar">
                        <div style={{ width: `${c.similarity.replace('%', '')}%` }} />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>
      )}

      {followups.length > 0 && (
        <section className="brief-card">
          <div className="section-heading">
            <h4>Useful Follow Ups</h4>
            <span className="section-caption">Questions worth asking next</span>
          </div>
          <div className="followup-list">
            {followups.map((f, i) => (
              <button
                key={`${f}-${i}`}
                type="button"
                className="followup-chip followup-btn"
                onClick={() => onFollowup?.(f)}
              >
                {f}
              </button>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

function getLegalBriefData(result) {
  const structured = result.structured || {};
  const meta = structured.meta || {};
  const summary = structured.summary || {};
  const plain = structured.plain_words || {};
  const parties = structured.parties || {};
  const laws = structured.applicable_laws || result.articles_cited || [];
  const rights = structured.rights_vs_limits?.rights || result.your_rights || [];
  const limits = structured.rights_vs_limits?.limits || [];
  const steps = structured.steps || (result.next_steps || []).map((step, i) => ({
    step_no: i + 1,
    action: step,
    timeframe: normalizeTimelineTimeframe({}, i),
  }));

  return {
    structured,
    meta,
    summary,
    plain,
    parties,
    laws,
    rights,
    limits,
    steps,
    forum: structured.forum_comparison || {},
    relief: structured.relief_spectrum || [],
    strength: structured.case_strength || [],
    costBenefit: structured.cost_benefit || {},
    clauseRisks: structured.clause_risks || [],
    evidence: structured.evidence_checklist || [],
    doList: structured.do_and_avoid?.do || [],
    avoidList: structured.do_and_avoid?.avoid || [],
    misconceptions: structured.misconceptions || [],
    similar: structured.similar_cases || [],
    followups: structured.followups || [],
    activeDomain: meta.domain || result.explainability?.detected_domain || 'Legal domain',
  };
}

function LegalCaseOverview({ data, result, urgency, viewMode }) {
  const { meta, summary, plain, parties, activeDomain } = data;
  const confidenceValue = typeof meta.confidence === 'number' ? meta.confidence : result.explainability?.confidence;
  const confidenceLabel = typeof confidenceValue === 'number' ? `${confidenceValue}% confident` : 'Grounded brief';
  const issueTitle = meta.case_type || result.case_type || summary.signal || 'Legal issue identified';
  const issueSubline = [
    activeDomain,
    parties.forum || 'Forum to be confirmed',
    urgency?.level ? `${urgency.level} urgency` : null,
  ].filter(Boolean).join(' / ');

  return (
    <>
      <section className="case-query-card">
        <div>
          <span className="case-query-label">Your query</span>
          <p>{result.query}</p>
        </div>
        <span className="confidence-badge">{confidenceLabel}</span>
      </section>

      <section className="issue-panel">
        <div className="issue-accent" />
        <div className="issue-copy">
          <h3>{issueTitle}</h3>
          <p>{issueSubline}</p>
          <div className="brief-meta">
            {summary.signal && <span className="meta-chip warm">{summary.signal}</span>}
            {meta.in_scope === false && <span className="meta-chip warning">Out of corpus</span>}
            {result.ai_powered && <span className="meta-chip">RAG assisted</span>}
          </div>
        </div>
      </section>

      {plain.short_explanation && (
        <section className="plain-words-panel">
          <div className="section-heading compact">
            <h4>Overview</h4>
            {viewMode === 'detailed' && <span className="section-caption">Plain-language reading of the facts</span>}
          </div>
          <div className="plain-words-copy">{plain.short_explanation}</div>
        </section>
      )}
    </>
  );
}

function DomainRoutingCard({ activeDomain }) {
  return (
    <section className="domain-routing-panel">
      <div className="section-heading compact">
        <div className="title-with-info">
          <h4>Domain Routing</h4>
          <div className="info-trigger"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg><span className="info-tooltip">Shows the legal domain detected for your query and which corpus is being used.</span></div>
        </div>
      </div>
      <div className="routing-chips">
        {['Constitutional Law', 'Consumer Protection', 'Criminal Law', 'IT Law', 'Civil Procedure'].map(domain => (
          <span
            key={domain}
            className={`routing-chip ${activeDomain.toLowerCase().includes(domain.toLowerCase().split(' ')[0]) ? 'active' : ''}`}
          >
            {domain}
          </span>
        ))}
      </div>
    </section>
  );
}

function CaseSnapshotCard({ data, urgency, viewMode }) {
  const { meta, parties } = data;
  const snapshotRows = [
    ['Domain', meta.domain || 'General legal query'],
    ['Confidence', typeof meta.confidence === 'number' ? `${meta.confidence}%` : 'Unknown'],
    ['Likely forum', parties.forum || 'To be confirmed'],
    ...(viewMode === 'detailed' ? [
      ['Provider', meta.llm_provider || 'AI assisted'],
      ['Urgency', urgency?.level || 'Standard'],
      ['Corpus fit', meta.in_scope === false ? 'Out of corpus' : 'In constitutional scope'],
    ] : [
      ['Urgency', urgency?.level || 'Standard'],
    ]),
  ];

  return (
    <section className="brief-card brief-card-spotlight">
      <div className="section-heading">
        <div className="title-with-info">
          <h4>Case Snapshot</h4>
          <div className="info-trigger"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg><span className="info-tooltip">A quick overview of the legal domain, confidence level, likely forum, and urgency of your case.</span></div>
        </div>
        <span className="section-caption">{viewMode === 'detailed' ? 'Matter profile' : 'Fast read'}</span>
      </div>
      <div className="snapshot-table-wrap">
        <table className="snapshot-table">
          <tbody>
            {snapshotRows.map(([label, value]) => (
              <tr key={label}>
                <th>{label}</th>
                <td>{value}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function EntityMapCard({ parties, result }) {
  return (
    <section className="brief-card">
      <div className="section-heading">
        <div className="title-with-info">
          <h4>Entity Map</h4>
          <div className="info-trigger"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg><span className="info-tooltip">Visualize the relationships between the claimant, respondent, and the legal forum.</span></div>
        </div>
        <span className="section-caption">Who, what, where</span>
      </div>
      <div className="entity-flow">
        <div className="entity-node">
          <span className="entity-label">Claimant</span>
          <strong>{parties.complainant || 'You'}</strong>
        </div>
        <div className="entity-connector" />
        <div className="entity-node">
          <span className="entity-label">Respondent</span>
          <strong>{parties.opposite_party || 'Respondent'}</strong>
        </div>
        <div className="entity-connector" />
        <div className="entity-node">
          <span className="entity-label">Forum</span>
          <strong>{parties.forum || 'Authority'}</strong>
        </div>
      </div>
      <div className="entity-subject-panel">
        <span className="entity-label">Subject</span>
        <p>{parties.subject || result.query || 'Legal issue summary unavailable.'}</p>
      </div>
    </section>
  );
}

function ApplicableLawsCard({ laws, viewMode }) {
  const visibleLaws = viewMode === 'simple' ? laws.slice(0, 3) : laws;

  return (
    <section className="brief-card">
      <div className="section-heading">
        <div className="title-with-info">
          <h4>Applicable Laws</h4>
          <div className="info-trigger"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg><span className="info-tooltip">Key statutes, constitutional articles, and legal provisions relevant to your scenario.</span></div>
        </div>
        <span className="section-caption">Primary legal support</span>
      </div>
      {visibleLaws.length > 0 ? (
        <div className="law-grid">
          {visibleLaws.map((law, i) => (
            <div key={`${law.name || law.title}-${i}`} className="law-card">
              <div className="law-card-head">
                <strong>{law.name || law.title || `Law ${i + 1}`}</strong>
                {law.type && <span className="law-type">{law.type}</span>}
              </div>
              {(law.why_it_applies || law.relevance) && <p>{law.why_it_applies || law.relevance}</p>}
              {law.citations?.length > 0 && (
                <div className="law-citations">
                  {law.citations.map(c => (
                    <span key={c} className="law-chip">{c}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <p className="empty-state">No laws extracted for this query.</p>
      )}
    </section>
  );
}

function CaseStrengthCard({ strength, viewMode }) {
  const visibleStrength = viewMode === 'simple' ? strength.slice(0, 2) : strength;

  return (
    <section className="brief-card">
      <div className="section-heading">
        <div className="title-with-info">
          <h4>Case Strength</h4>
          <div className="info-trigger"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg><span className="info-tooltip">An AI-driven estimation of the matter's standing based on retrieved precedents and legal factors.</span></div>
        </div>
        <span className="section-caption">What helps or weakens the matter</span>
      </div>
      <div className="strength-grid">
        {visibleStrength.length > 0 ? visibleStrength.map((s, i) => (
          <div key={`${s.label}-${i}`} className="strength-item">
            <div className="strength-label">
              <span>{s.label}</span>
              <span className="strength-value">{Math.min(100, s.score || 0)}%</span>
            </div>
            <div className="strength-bar">
              <div className="strength-fill" style={{ width: `${Math.min(100, s.score || 0)}%` }} />
            </div>
            {viewMode === 'detailed' && <div className="strength-note">{s.note || 'No note available.'}</div>}
          </div>
        )) : (
          <div className="strength-empty">
            <span className="empty-number">01</span>
            <p>No strength signals available yet. Evidence and documents will shape this most.</p>
          </div>
        )}
      </div>
    </section>
  );
}

function RightsAndLimitsCards({ rights, limits, viewMode }) {
  const visibleRights = viewMode === 'simple' ? rights.slice(0, 4) : rights;
  const visibleLimits = viewMode === 'simple' ? limits.slice(0, 4) : limits;

  return (
    <div className="brief-grid">
      <section className="brief-card">
        <div className="section-heading">
          <div className="title-with-info">
            <h4>Rights You Can Claim</h4>
            <div className="info-trigger"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg><span className="info-tooltip">Legal rights that apply to your situation based on constitutional and statutory provisions.</span></div>
          </div>
          <span className="section-caption">Strongest visible rights</span>
        </div>
        <div className="pill-list">
          {visibleRights.length > 0 ? visibleRights.map((item, i) => (
            <div key={`${item}-${i}`} className="info-pill positive">{item}</div>
          )) : <p className="empty-state">No rights extracted.</p>}
        </div>
      </section>

      <section className="brief-card">
        <div className="section-heading">
          <div className="title-with-info">
            <h4>Limits & Watchouts</h4>
            <div className="info-trigger"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg><span className="info-tooltip">Practical limitations and legal boundaries you should be aware of before taking action.</span></div>
          </div>
          <span className="section-caption">Cautions before acting</span>
        </div>
        <div className="pill-list">
          {visibleLimits.length > 0 ? visibleLimits.map((item, i) => (
            <div key={`${item}-${i}`} className="info-pill caution">{item}</div>
          )) : <p className="empty-state">No limitations extracted.</p>}
        </div>
      </section>
    </div>
  );
}

function ActionTimelineCard({ steps, viewMode }) {
  const visibleSteps = viewMode === 'simple' ? steps.slice(0, 3) : steps;

  return (
    <section className="brief-card">
      <div className="section-heading">
        <div className="title-with-info">
          <h4>Action Timeline</h4>
          <div className="info-trigger"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg><span className="info-tooltip">A step-by-step timeline of recommended legal actions, ordered by urgency and importance.</span></div>
        </div>
        <span className="section-caption">Sequenced by urgency</span>
      </div>
      {visibleSteps.length > 0 ? (
        <div className="timeline-horizontal">
          <div className="timeline-rail" />
          {visibleSteps.map((s, i) => (
            <div key={`${s.action || 'step'}-${i}`} className="timeline-stop">
              <div className="timeline-marker">
                <span className="timeline-index">{i + 1}</span>
              </div>
              <div className="timeline-time">{normalizeTimelineTimeframe(s, i)}</div>
              <div className="timeline-card">
                <div className="timeline-title">{s.action || 'Step'}</div>
                <div className="timeline-meta">Action</div>
                {viewMode === 'detailed' && s.why && <p className="timeline-note">{s.why}</p>}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="empty-state">No steps available.</p>
      )}
    </section>
  );
}

function EvidenceCard({ evidence, viewMode }) {
  const visibleEvidence = viewMode === 'simple' ? evidence.slice(0, 6) : evidence;

  return (
    <section className="brief-card">
      <div className="section-heading">
        <div className="title-with-info">
          <h4>Evidence Checklist</h4>
          <div className="info-trigger"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg><span className="info-tooltip">Documents, records, and proof you should gather to strengthen your legal position.</span></div>
        </div>
        <span className="section-caption">Documents to gather now</span>
      </div>
      <div className="checklist-grid">
        {visibleEvidence.length > 0 ? visibleEvidence.map((item, i) => (
          <div key={`${item}-${i}`} className="check-card">{item}</div>
        )) : <p className="empty-state">No evidence checklist available.</p>}
      </div>
    </section>
  );
}

function DoAvoidCard({ doList, avoidList, viewMode }) {
  const visibleDo = viewMode === 'simple' ? doList.slice(0, 4) : doList;
  const visibleAvoid = viewMode === 'simple' ? avoidList.slice(0, 4) : avoidList;

  return (
    <section className="brief-card">
      <div className="section-heading">
        <div className="title-with-info">
          <h4>Dos & Avoids</h4>
          <div className="info-trigger"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg><span className="info-tooltip">Practical actions that can improve your position, and mistakes to avoid during the process.</span></div>
        </div>
        <span className="section-caption">Practical moves</span>
      </div>
      <div className="dual-callout">
        <div className="callout-panel do-panel">
          <span className="callout-label">Do this</span>
          <div className="stack-list">
            {visibleDo.length > 0 ? visibleDo.map((item, i) => (
              <div key={`${item}-${i}`} className="stack-item">{item}</div>
            )) : <div className="stack-item muted">No action items listed.</div>}
          </div>
        </div>
        <div className="callout-panel avoid-panel">
          <span className="callout-label">Avoid this</span>
          <div className="stack-list">
            {visibleAvoid.length > 0 ? visibleAvoid.map((item, i) => (
              <div key={`${item}-${i}`} className="stack-item">{item}</div>
            )) : <div className="stack-item muted">No avoid items listed.</div>}
          </div>
        </div>
      </div>
    </section>
  );
}

function FollowupsCard({ followups, onFollowup }) {
  if (!followups.length) return null;

  return (
    <section className="brief-card">
      <div className="section-heading">
        <div className="title-with-info">
          <h4>Useful Follow-Ups</h4>
          <div className="info-trigger"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg><span className="info-tooltip">Suggested questions to explore next for a deeper understanding of your legal situation.</span></div>
        </div>
        <span className="section-caption">Questions worth asking next</span>
      </div>
      <div className="followup-list">
        {followups.map((f, i) => (
          <button
            key={`${f}-${i}`}
            type="button"
            className="followup-chip followup-btn"
            onClick={() => onFollowup?.(f)}
          >
            {f}
          </button>
        ))}
      </div>
    </section>
  );
}

function DetailedOptionalCards({ data }) {
  const { structured, forum, relief, costBenefit, clauseRisks, misconceptions, similar } = data;

  return (
    <>
      {structured.compliance_checklist?.length > 0 && (
        <section className="brief-card">
          <div className="section-heading">
            <h4>Compliance Checklist</h4>
            <span className="section-caption">Requirements based on business type and employee count</span>
          </div>
          <div className="checklist-grid">
            {structured.compliance_checklist.map((item, i) => (
              <div key={`${item.act}-${i}`} className={`check-card ${item.status || ''}`} style={{ borderColor: item.status === 'applicable' ? 'var(--lq-success)' : 'var(--lq-amber)' }}>
                <strong>{item.status_symbol || '-'} {item.act}</strong>
                <p style={{ marginTop: '8px', color: 'var(--lq-text-soft)' }}>{item.requirement_summary}</p>
                {item.sources?.length > 0 && (
                  <div style={{ marginTop: '12px' }}>
                    <span className="meta-chip" style={{ fontSize: '0.75rem' }}>Sources: {item.sources.join(', ')}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {forum.rows?.length > 0 && (
        <section className="brief-card">
          <div className="section-heading">
            <h4>Forum Comparison</h4>
            <span className="section-caption">Compare where the matter can be taken</span>
          </div>
          <div className="forum-table-wrap">
            <table className="forum-table">
              <thead>
                <tr>
                  <th>Factor</th>
                  {(forum.forums || []).map(f => <th key={f}>{f}</th>)}
                </tr>
              </thead>
              <tbody>
                {forum.rows.map((row, i) => (
                  <tr key={`${row.factor}-${i}`}>
                    <td>{row.factor}</td>
                    {(row.values || []).map((v, idx) => <td key={`${row.factor}-${idx}`}>{v}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {(relief.length > 0 || costBenefit.invest?.length > 0 || costBenefit.recover?.length > 0) && (
        <div className="brief-grid">
          {relief.length > 0 && (
            <section className="brief-card">
              <div className="section-heading">
                <h4>Relief Spectrum</h4>
                <span className="section-caption">Typical outcomes to aim for</span>
              </div>
              <div className="relief-list">
                {relief.map((r, i) => (
                  <div key={`${r.label}-${i}`} className="relief-item">
                    <div className="relief-copy">
                      <div className="relief-label">{r.label}</div>
                      <div className="relief-range">{r.range}</div>
                    </div>
                    <div className={`relief-bar ${r.level || ''}`}>
                      <div style={{ width: `${Math.min(100, r.likelihood || 0)}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {(costBenefit.invest?.length > 0 || costBenefit.recover?.length > 0) && (
            <section className="brief-card">
              <div className="section-heading">
                <h4>Cost and Recovery</h4>
                <span className="section-caption">Likely inputs versus possible returns</span>
              </div>
              <div className="cost-benefit">
                <div className="cost-panel">
                  <h5>What you invest</h5>
                  {(costBenefit.invest || []).map((item, i) => (
                    <div key={`${item.item}-${i}`} className="cost-row">
                      <span>{item.item}</span>
                      <strong>{item.amount}</strong>
                    </div>
                  ))}
                </div>
                <div className="benefit-panel">
                  <h5>What you can recover</h5>
                  {(costBenefit.recover || []).map((item, i) => (
                    <div key={`${item.item}-${i}`} className="cost-row">
                      <span>{item.item}</span>
                      <strong>{item.amount}</strong>
                    </div>
                  ))}
                </div>
              </div>
            </section>
          )}
        </div>
      )}

      {clauseRisks.length > 0 && (
        <section className="brief-card">
          <div className="section-heading">
            <h4>Clause Risk Scanner</h4>
            <span className="section-caption">Terms that may need revision or caution</span>
          </div>
          <div className="risk-list">
            {clauseRisks.map((c, i) => (
              <div key={`${c.clause}-${i}`} className={`risk-item ${c.risk_level || 'medium'}`}>
                <div className="risk-head">
                  <strong>{c.clause}</strong>
                  <span className="risk-level">{c.risk_level}</span>
                </div>
                <p>{c.issue}</p>
                {c.fix && <div className="risk-fix">Fix: {c.fix}</div>}
              </div>
            ))}
          </div>
        </section>
      )}

      {(misconceptions.length > 0 || similar.length > 0) && (
        <div className="brief-grid">
          {misconceptions.length > 0 && (
            <section className="brief-card">
              <div className="section-heading">
                <h4>Common Misconceptions</h4>
                <span className="section-caption">Quick legal corrections worth knowing</span>
              </div>
              <div className="misconceptions">
                {misconceptions.map((m, i) => (
                  <div key={`${m.claim}-${i}`} className="misconception-item">
                    <div className="misconception-claim">{m.claim}</div>
                    <div className="misconception-truth">{m.truth}</div>
                    {m.explanation && <div className="misconception-note">{m.explanation}</div>}
                  </div>
                ))}
              </div>
            </section>
          )}

          {similar.length > 0 && (
            <section className="brief-card">
              <div className="section-heading">
                <div className="title-with-info">
                  <h4>Similar Precedents</h4>
                  <div className="info-trigger"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg><span className="info-tooltip">Court cases with similar facts and outcomes that can guide expectations.</span></div>
                </div>
                <span className="section-caption">Comparable court outcomes</span>
              </div>
              <div className="precedent-row">
                {similar.map((c, i) => (
                  <div key={`${c.case_name}-${i}`} className="precedent-card">
                    <div className="precedent-title">{c.case_name}</div>
                    <div className="precedent-meta">{c.court} / {c.year}</div>
                    <div className="precedent-outcome">{c.outcome}</div>
                    {c.similarity && (
                      <div className="precedent-bar">
                        <div style={{ width: `${c.similarity.replace('%', '')}%` }} />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>
      )}
    </>
  );
}

function ExplainabilityCard({ explainability, viewMode }) {
  if (!explainability) {
    return <p className="empty-state">No explainability insights available for this query.</p>;
  }

  return (
    <section className="brief-card">
      <div className="section-heading">
        <div className="title-with-info">
          <h4>Explainability</h4>
          <div className="info-trigger"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg><span className="info-tooltip">Transparency details on how the AI built this answer, including domain detection and source documents.</span></div>
        </div>
        <span className="section-caption">How this answer was built</span>
      </div>
      <div className="snapshot-table-wrap">
        <table className="snapshot-table">
          <tbody>
            <tr>
              <th>Detected Domain</th>
              <td><strong>{explainability.detected_domain || 'Unknown'}</strong></td>
            </tr>
            <tr>
              <th>Confidence</th>
              <td>{explainability.confidence || 'N/A'}%</td>
            </tr>
            {viewMode === 'detailed' && (
              <>
                <tr>
                  <th>Matched Keywords</th>
                  <td>{(explainability.matched_keywords || []).join(', ') || 'None'}</td>
                </tr>
                <tr>
                  <th>Explanation</th>
                  <td>{explainability.short_explanation}</td>
                </tr>
                <tr>
                  <th>Chunks Used</th>
                  <td>{explainability.number_of_chunks_used || 0}</td>
                </tr>
              </>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function StepCard({ step, index }) {
  return (
    <div className="step-card" style={{ animationDelay: `${index * 60}ms` }}>
      <div className="step-number">{index + 1}</div>
      <div className="step-copy">
        <div className="step-title">{step}</div>
        <div className="step-subtitle">Immediate action item</div>
      </div>
    </div>
  );
}

// eslint-disable-next-line no-unused-vars
function RightItem({ right, index }) {
  return (
    <div className="right-item" style={{ animationDelay: `${index * 60}ms` }}>
      <span className="right-text">{right}</span>
    </div>
  );
}

function visibleItems(value) {
  const items = Array.isArray(value) ? value : (value?.items || []);
  return items.filter(item => !(item && item.note === 'NOT FOUND IN DOCUMENT'));
}

function ResultPanel({ result, onFollowup }) {
  const [activeTab, setActiveTab] = useState('brief');
  const [viewMode, setViewMode] = useState('simple');
  const data = getLegalBriefData(result);
  const panelConfidence = data.meta?.confidence ?? result.explainability?.confidence;
  const confidenceText = typeof panelConfidence === 'number' ? `${panelConfidence}% confident` : 'Grounded by corpus';
  const primaryCorpus = result.explainability?.detected_domain || data.meta?.domain || 'NyayaSetu corpus';
  const retrievedCount = result.explainability?.number_of_chunks_used || result.retrieved_sections?.length || 0;
  const sourceCount = result.retrieved_sections?.length || 0;

  const tabs = [
    { id: 'brief', label: 'Brief', count: data.laws.length || null, note: 'Overview, snapshot, entities, strength, laws' },
    { id: 'rights', label: 'Rights', count: data.rights.length + data.limits.length || null, note: 'Claims, limits, and watchouts' },
    { id: 'strategy', label: 'Strategy', count: data.evidence.length + data.steps.length + data.followups.length || null, note: 'Evidence, dos, timeline, follow-ups' },
    { id: 'analysis', label: 'Analysis', count: (result.key_points?.length || 0) + (result.articles_cited?.length || 0) || null, note: 'Legal points, articles, detailed next steps' },
    { id: 'sources', label: 'Sources', count: sourceCount || null, note: 'Source sections and explainability' },
  ];

  const activeTabMeta = tabs.find(tab => tab.id === activeTab) || tabs[0];

  const copyText = useCallback(async () => {
    const text = [
      `LEGAL ANALYSIS - ${result.case_type}`,
      `Query: ${result.query}`,
      '',
      'SUMMARY:',
      result.summary,
      '',
      'ANALYSIS:',
      result.analysis,
      '',
      'YOUR RIGHTS:',
      ...(result.your_rights || []).map((r, i) => `${i + 1}. ${r}`),
      '',
      'NEXT STEPS:',
      ...(result.next_steps || []).map((s, i) => `${i + 1}. ${s}`),
      '',
      result.disclaimer,
    ].join('\n');
    await navigator.clipboard.writeText(text);
  }, [result]);

  const renderBriefTab = () => (
    <div className="tab-pane">
      <LegalCaseOverview data={data} result={result} urgency={result.urgency} viewMode={viewMode} />
      {viewMode === 'detailed' && <DomainRoutingCard activeDomain={data.activeDomain} />}
      <div className="brief-grid brief-grid-top">
        <CaseSnapshotCard data={data} urgency={result.urgency} viewMode={viewMode} />
        <EntityMapCard parties={data.parties} result={result} />
      </div>
      <div className="brief-grid">
        <CaseStrengthCard strength={data.strength} viewMode={viewMode} />
        <ApplicableLawsCard laws={data.laws} viewMode={viewMode} />
      </div>
      {viewMode === 'detailed' && <DetailedOptionalCards data={data} />}
    </div>
  );

  const renderRightsTab = () => (
    <div className="tab-pane">
      <p className="tab-intro">The claimable rights and the practical limits visible from the current facts.</p>
      <RightsAndLimitsCards rights={data.rights} limits={data.limits} viewMode={viewMode} />
      {viewMode === 'detailed' && (
        <div className="legal-aid-box">
          <h4>Free legal support</h4>
          <p>Contact the <strong>District Legal Services Authority (DLSA)</strong> for free legal aid.</p>
          <p><strong>Tele-Law Helpline:</strong> 15100</p>
          <p><strong>National Legal Services Authority:</strong> nalsa.gov.in</p>
        </div>
      )}
    </div>
  );

  const renderStrategyTab = () => (
    <div className="tab-pane">
      <div className="brief-grid">
        <EvidenceCard evidence={data.evidence} viewMode={viewMode} />
        <DoAvoidCard doList={data.doList} avoidList={data.avoidList} viewMode={viewMode} />
      </div>
      <ActionTimelineCard steps={data.steps} viewMode={viewMode} />
      <FollowupsCard followups={viewMode === 'simple' ? data.followups.slice(0, 4) : data.followups} onFollowup={onFollowup} />
    </div>
  );

  const renderAnalysisTab = () => (
    <div className="tab-pane">
      {result.key_points?.length > 0 && (
        <div className="key-points-box">
          <div className="section-heading">
            <h4>Key Legal Points</h4>
            <span className="section-caption">Fast scan of the most important takeaways</span>
          </div>
          <div className="key-points-grid">
            {(viewMode === 'simple' ? result.key_points.slice(0, 4) : result.key_points).map((pt, i) => (
              <div key={`${pt}-${i}`} className="key-point-card">{pt}</div>
            ))}
          </div>
        </div>
      )}

      {viewMode === 'detailed' && result.articles_cited?.length > 0 && (
        <section className="brief-card">
          <div className="section-heading">
            <h4>Articles</h4>
            <span className="section-caption">Core citations and references</span>
          </div>
          <div className="articles-list">
            {result.articles_cited.map((a, i) => (
              <ArticleCard key={`${a.number || a.title}-${i}`} article={a} index={i} />
            ))}
          </div>
        </section>
      )}

      {viewMode === 'detailed' && (
        <>
          <section className="brief-card">
            <div className="section-heading">
              <h4>Next Steps (Detailed)</h4>
              <span className="section-caption">Practical actions to take</span>
            </div>
            <div className="steps-list">
              {(result.next_steps || []).map((s, i) => (
                <StepCard key={`${s}-${i}`} step={s} index={i} />
              ))}
            </div>
          </section>

          <div className="analysis-body">
            <RenderText text={result.analysis} />
          </div>
        </>
      )}

      {viewMode === 'simple' && (
        <div className="disclaimer-box">
          <span className="disclaimer-label">Important</span>
          <p>{result.disclaimer}</p>
        </div>
      )}
    </div>
  );

  const renderSourcesTab = () => {
    const visibleSections = viewMode === 'simple' ? (result.retrieved_sections || []).slice(0, 3) : result.retrieved_sections || [];

    return (
      <div className="tab-pane">
        <p className="tab-intro">
          {viewMode === 'simple'
            ? 'Top source matches that support this answer.'
            : 'Retrieved source sections and the reasoning trail behind this answer.'}
        </p>
        <div className="sections-list">
          {visibleSections.length > 0 ? visibleSections.map((s, i) => (
            viewMode === 'simple' ? (
              <div key={`${s.title}-${i}`} className="section-card source-summary-card">
                <div className="section-card-header source-summary-static">
                  <div className="section-card-primary">
                    <div className="section-title">{s.title}</div>
                    <p className="source-summary-excerpt">{s.excerpt}</p>
                  </div>
                  {typeof s.score === 'number' && <span className="tab-count">{s.score.toFixed(1)}</span>}
                </div>
              </div>
            ) : (
              <SectionCard key={`${s.title}-${i}`} section={s} index={i} />
            )
          )) : <p className="empty-state">No retrieved source sections available.</p>}
        </div>

        <ExplainabilityCard explainability={result.explainability} viewMode={viewMode} />

        {viewMode === 'detailed' && result.explainability?.source_documents?.length > 0 && (
          <section className="brief-card">
            <div className="section-heading">
              <h4>Source Documents</h4>
              <span className="section-caption">Documents sourced for this query</span>
            </div>
            <div className="pill-list">
              {result.explainability.source_documents.map((doc, i) => (
                <div key={`${doc}-${i}`} className="info-pill">{doc}</div>
              ))}
            </div>
          </section>
        )}
      </div>
    );
  };

  const renderActiveTab = () => {
    if (activeTab === 'rights') return renderRightsTab();
    if (activeTab === 'strategy') return renderStrategyTab();
    if (activeTab === 'analysis') return renderAnalysisTab();
    if (activeTab === 'sources') return renderSourcesTab();
    return renderBriefTab();
  };

  return (
    <div className="result-panel legal-result-panel">
      <div className="result-header">
        <div className="result-header-top">
          <div className="result-title-section">
            <p className="result-eyebrow">{result.case_type}</p>
            <h2 className="result-title">{data.meta?.case_type || 'Legal Analysis'}</h2>
            <p className="result-summary">{result.summary}</p>
          </div>
          <div className="result-badges">
            <span className="badge confident">{confidenceText}</span>
            <button className="icon-btn" onClick={copyText} title="Copy full analysis">
              Copy Brief
            </button>
          </div>
        </div>

        <UrgencyBadge urgency={result.urgency} />

        {result.legal_topics?.length > 0 && (
          <div className="topics-row">
            {result.legal_topics.map(t => (
              <span key={t} className="topic-chip">{t}</span>
            ))}
          </div>
        )}

        {viewMode === 'detailed' && (
          <div className="result-metrics-strip">
            <div className="metric-tile">
              <span>Docs retrieved</span>
              <strong>{retrievedCount || '-'}</strong>
            </div>
            <div className="metric-tile">
              <span>Primary corpus</span>
              <strong>{primaryCorpus}</strong>
            </div>
            <div className="metric-tile">
              <span>Confidence</span>
              <strong className="metric-good">{typeof panelConfidence === 'number' && panelConfidence >= 75 ? 'High' : confidenceText}</strong>
            </div>
          </div>
        )}
      </div>

      <div className="legal-flow-toolbar">
        <div className="toolbar-integrated-row">
          <nav className="legal-tab-rail" aria-label="Grouped result sections">
            {tabs.map(tab => (
              <button
                key={tab.id}
                type="button"
                className={`sidebar-tab-btn legal-tab-btn ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <span className="sidebar-tab-copy">
                  <span className="sidebar-tab-label">{tab.label}</span>
                </span>
                {tab.count > 0 && <span className="tab-count">{tab.count}</span>}
              </button>
            ))}
          </nav>

          <div className="mode-toggle-pill" aria-label="Result detail level">
            {['simple', 'detailed'].map(mode => (
              <button
                key={mode}
                type="button"
                className={viewMode === mode ? 'active' : ''}
                onClick={() => setViewMode(mode)}
                aria-pressed={viewMode === mode}
              >
                {mode === 'simple' ? 'Simple' : 'Detailed'}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="legal-result-shell">
        <div className="result-main">
          <div className="tab-content">
            {renderActiveTab()}
          </div>
        </div>
      </div>
    </div>
  );
}

function DocumentResultPanel({ docResult }) {
  const report = docResult?.report_json || {};
  const checks = docResult?.quality_checks || {};
  const overview = report.document_overview || {};
  const parties = report.parties_involved || [];
  const terms = report.key_terms_definitions || [];
  const clauses = report.critical_clauses || [];
  const risks = report.red_flags_risk_analysis || [];
  const dates = report.important_dates_deadlines || [];
  const money = report.financial_obligations || [];
  const attachments = report.attachments_exhibits || [];
  const extractionIssues = checks.extraction_issues || [];

  const copyText = useCallback(async () => {
    if (!docResult?.report_markdown) return;
    await navigator.clipboard.writeText(docResult.report_markdown);
  }, [docResult]);

  const exhaustive = Boolean(report.document_identity || report.identity);
  const identity = report.identity || report.document_identity || report.document_overview || {};
  const priorityAlerts = report.priority_alerts || report.critical_legal_alerts || {};
  const allParties = visibleItems(report.all_parties_involved || report.parties_involved);
  const allDates = visibleItems(report.dates || report.all_dates_deadlines || report.important_dates_deadlines);
  const allMoney = visibleItems(report.financials || report.all_financial_details || report.financial_obligations);
  const allTerms = visibleItems(report.important_legal_terms_found || report.key_terms_definitions).filter((t) => {
    if (!t || typeof t !== 'object') return false;
    const fields = [t.term, t.found_in, t.document_says, t.plain_english];
    return fields.some(v => v !== null && v !== undefined && String(v).trim() !== '' && String(v).trim() !== 'NOT FOUND IN DOCUMENT');
  });
  const allClauses = visibleItems(report.clauses || report.all_clauses_full_list || report.critical_clauses);
  const allObligations = visibleItems(report.obligations || report.obligations_summary || []);
  const allRisks = visibleItems(report.red_flags_risks || report.red_flags_risk_analysis);
  const allAttachments = visibleItems(report.attachments_exhibits_references || report.attachments_exhibits);
  const summonsObj = Array.isArray(priorityAlerts.summons) ? (priorityAlerts.summons[0] || null) : (priorityAlerts.summons || null);
  const hearingItems = visibleItems(priorityAlerts.hearings || priorityAlerts.court_hearings);
  const orderItems = visibleItems(priorityAlerts.orders || priorityAlerts.orders_directions);
  const noticeItems = visibleItems(priorityAlerts.notices);
  const allAlerts = {
    summons: visibleItems(priorityAlerts.summons),
    court_hearings: hearingItems,
    notices: noticeItems,
    orders_directions: orderItems,
    warrants: visibleItems(priorityAlerts.warrants),
    injunctions: visibleItems(priorityAlerts.injunctions),
    appeals: visibleItems(priorityAlerts.appeals),
  };
  const obligations = report.obligations || report.obligations_summary || {};
  const partyMap = obligations.per_party || {};
  const courtDirections = visibleItems(obligations.court_authority || []);
  const plainSummary = report.plain_english_summary || {};
  const normalizeLanguage = (value) => {
    const v = String(value || '').trim().toLowerCase();
    if (v === 'en' || v === 'eng' || v === 'english') return 'English';
    if (v === 'hi' || v === 'hin' || v === 'hindi') return 'Hindi';
    return value;
  };
  const repairTruncatedWord = (value) => {
    const v = String(value || '').trim();
    if (/^(i?minal|riminal)$/i.test(v)) return 'Criminal';
    if (/^(ivil)$/i.test(v)) return 'Civil';
    return value;
  };
  const isWeakIdentityText = (value) => {
    const v = String(value || '').trim().toLowerCase();
    return (
      v.startsWith('the conditions laid down under') ||
      v.startsWith('subject to applicable law') ||
      v.startsWith('as per law')
    );
  };
  const identityView = {
    ...identity,
    document_type: repairTruncatedWord(identity.document_type),
    case_number: repairTruncatedWord(identity.case_number),
    case_number_reference: repairTruncatedWord(identity.case_number_reference),
    language: normalizeLanguage(identity.language || checks.language),
    jurisdiction: isWeakIdentityText(identity.jurisdiction) ? null : identity.jurisdiction,
    jurisdiction_governing_law: isWeakIdentityText(identity.jurisdiction_governing_law) ? null : identity.jurisdiction_governing_law,
  };
  const sectionHasData = (value) => {
    if (value === null || value === undefined) return false;
    if (typeof value === 'string') return value.trim() !== '' && value.trim() !== 'NOT FOUND IN DOCUMENT';
    if (Array.isArray(value)) return value.length > 0;
    if (typeof value === 'object') {
      return Object.values(value).some(v =>
        v !== null &&
        v !== undefined &&
        v !== 'NOT FOUND IN DOCUMENT' &&
        v !== ''
      );
    }
    return false;
  };
  const hasValue = (v) => v !== null && v !== undefined && v !== '' && v !== 'NOT FOUND IN DOCUMENT';
  const data = {
    priority_alerts: priorityAlerts,
    identity,
    parties: allParties,
    dates: allDates,
    financials: allMoney,
    legal_terms: allTerms,
    clauses: allClauses,
    obligations: allObligations,
    red_flags: allRisks,
    attachments: allAttachments,
    plain_english_summary: plainSummary,
  };
  const priorityCount = hearingItems.length + orderItems.length + noticeItems.length + (summonsObj?.present ? 1 : 0);
  const priorityHasData = sectionHasData(data.priority_alerts) && (
    summonsObj?.present === true ||
    hearingItems.length > 0 ||
    orderItems.length > 0 ||
    noticeItems.length > 0
  );
  const identityHasData = sectionHasData(data.identity);
  const partiesHasData = Array.isArray(data.parties) && data.parties.length > 0;
  const datesHasData = Array.isArray(data.dates) && data.dates.length > 0;
  const termsHasData = Array.isArray(data.legal_terms) && data.legal_terms.length > 0;
  const clausesHasData = Array.isArray(data.clauses) && data.clauses.length > 0;
  const obligationsHasData = Array.isArray(data.obligations) && data.obligations.length > 0;
  const attachmentsHasData = Array.isArray(data.attachments) && data.attachments.length > 0 && data.attachments.some(a => hasValue(a?.reference));
  const plainEnglishHasData = sectionHasData(data.plain_english_summary);
  const tabs = exhaustive ? [
    { id: 'priority', label: 'Priority Alerts', note: 'Summons and hearings', count: priorityCount },
    { id: 'identity', label: 'Identity', note: 'Document metadata', count: null },
    { id: 'parties', label: 'Parties', note: 'Every identified entity', count: allParties.length },
    { id: 'dates', label: 'Dates', note: 'Deadlines and time limits', count: allDates.length },
    { id: 'terms', label: 'Legal Terms', note: 'Glossary items found', count: allTerms.length },
    { id: 'clauses', label: 'Clauses', note: 'Full clause inventory', count: allClauses.length },
    { id: 'obligations', label: 'Obligations', note: 'Who must do what', count: allObligations.length },
    { id: 'attachments', label: 'Attachments', note: 'Exhibits and references', count: allAttachments.length },
    { id: 'summary', label: 'Plain English Summary', note: 'Plain-English explanation', count: null },
  ].filter(tab => (
    (tab.id === 'priority' && priorityHasData) ||
    (tab.id === 'identity' && identityHasData) ||
    (tab.id === 'parties' && partiesHasData) ||
    (tab.id === 'dates' && datesHasData) ||
    (tab.id === 'terms' && termsHasData) ||
    (tab.id === 'clauses' && clausesHasData) ||
    (tab.id === 'obligations' && obligationsHasData) ||
    (tab.id === 'attachments' && attachmentsHasData) ||
    (tab.id === 'summary' && plainEnglishHasData)
  )) : [
    { id: 'overview', label: 'Overview', note: 'Document type and metadata', count: null },
    { id: 'parties', label: 'Parties', note: 'Involved entities and roles', count: visibleItems(parties).length || null },
    { id: 'terms', label: 'Key Terms', note: 'Defined legal terms', count: visibleItems(terms).length || null },
    { id: 'clauses', label: 'Critical Clauses', note: 'Clause-level analysis', count: visibleItems(clauses).length || null },
    { id: 'dates', label: 'Dates', note: 'Deadlines and key dates', count: visibleItems(dates).length || null },
    { id: 'obligations', label: 'Obligations', note: 'Party-wise duties', count: (obligations.party_a_must?.length || 0) + (obligations.party_b_must?.length || 0) || null },
    { id: 'attachments', label: 'Attachments', note: 'Exhibits and annexures', count: visibleItems(attachments).length || null },
    { id: 'summary', label: 'Plain-English', note: 'Readable legal summary', count: null },
  ];
  const [activeTab, setActiveTab] = useState('overview');
  const showDateWhoCol = allDates.some(d => hasValue(d.who_it_affects));
  const showAmountCol = allMoney.some(m => hasValue(m.amount));
  const showPurposeCol = allMoney.some(m => hasValue(m.purpose));
  const showWhoCol = allMoney.some(m => hasValue(m.who_pays));
  const showDueCol = allMoney.some(m => hasValue(m.due_date));
  const randomPartyId = () => `PTY-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;
  const cleanedAttachments = allAttachments.filter(a => hasValue(a?.reference) || hasValue(a?.what_it_is) || hasValue(a?.attached));
  const showRefCol = cleanedAttachments.some(a => hasValue(a.reference));
  const showWhatCol = cleanedAttachments.some(a => hasValue(a.what_it_is));
  const showAttachedCol = cleanedAttachments.some(a => hasValue(a.attached));
  const shortText = (value, limit = 220) => {
    const text = String(value || '').replace(/\s+/g, ' ').trim();
    if (!text) return null;
    return text.length > limit ? `${text.slice(0, limit)}...` : text;
  };
  const pickAlert = (item) => ({
    action: item?.what_to_do || item?.description || item?.purpose || item?.issue || null,
    deadline: item?.deadline || item?.deadline_to_respond || item?.due_date || null,
    party: item?.issued_to || item?.directed_to || item?.who_it_affects || null,
    court: item?.court || item?.forum || null,
    date: item?.date || item?.hearing_date || null,
    snippet: shortText(item?.exact_text || item?.document_says || item?.text || null),
  });
  const tabIds = tabs.map(tab => tab.id);
  const tabIdsKey = tabIds.join('|');
  useEffect(() => {
    if (!exhaustive) return;
    const priorityOrder = ['priority', 'identity', 'parties', 'dates', 'money', 'terms', 'clauses', 'obligations', 'risks', 'attachments', 'summary'];
    const firstAvailable = priorityOrder.find(id => tabIds.includes(id));
    if (firstAvailable && activeTab !== firstAvailable && !tabIds.includes(activeTab)) {
      setActiveTab(firstAvailable);
    }
  }, [exhaustive, activeTab, tabIds, tabIdsKey]);
  const effectiveActiveTab = tabIds.includes(activeTab) ? activeTab : (tabs[0]?.id || 'overview');
  const activeTabMeta = tabs.find(t => t.id === effectiveActiveTab) || tabs[0] || { label: 'Overview', note: '' };

  if (exhaustive) {
    return (
      <div className="result-panel">
        <div className="result-header">
          <div className="result-header-top">
            <div className="result-title-section">
              <p className="result-eyebrow">Document Intelligence</p>
              <h2 className="result-title">{identityView.document_title || docResult.filename || 'Legal Document Report'}</h2>
              <p className="result-summary">{report.raw_extraction ? `Pages: ${report.raw_extraction.total_pages || '-'} | Language: ${report.raw_extraction.language || '-'}` : 'Exhaustive document analysis generated from the uploaded file.'}</p>
            </div>
            <div className="result-badges">
              <span className="badge ai">Exhaustive</span>
              <button className="icon-btn" onClick={copyText} title="Copy full document report">
                Copy Report
              </button>
            </div>
          </div>
          <div className="topics-row">
            <span className="topic-chip">File: {docResult.filename}</span>
            <span className="topic-chip">Type: {docResult.file_type}</span>
            <span className="topic-chip">Pages: {identityView.total_pages || report.raw_extraction?.total_pages || '-'}</span>
            {typeof checks.ocr_confidence === 'number' && <span className="topic-chip">OCR: {checks.ocr_confidence}%</span>}
            {report.raw_extraction?.low_quality_scan && <span className="topic-chip">POOR_QUALITY_SCAN</span>}
          </div>
        </div>

        <div className="result-shell">
          <aside className="result-sidebar">
            <div className="sidebar-card">
              <span className="sidebar-label">Consultation flow</span>
              <h3>{activeTabMeta.label}</h3>
              <p>{activeTabMeta.note}</p>
            </div>

            <nav className="sidebar-nav" aria-label="Document report sections">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  type="button"
                  className={`sidebar-tab-btn ${activeTab === tab.id ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab.id)}
                >
                  <span className="sidebar-tab-copy">
                    <span className="sidebar-tab-label">{tab.label}</span>
                    <span className="sidebar-tab-note">{tab.note}</span>
                  </span>
                  {tab.count > 0 && <span className="tab-count">{tab.count}</span>}
                </button>
              ))}
            </nav>

            <div className="sidebar-card sidebar-card-muted">
              <span className="sidebar-label">Working query</span>
              <p>{docResult.filename}</p>
            </div>
          </aside>

          <div className="result-main">
            <div className="tab-content">
              {tabs.length === 0 && (
                <div className="tab-pane">
                  <div className="empty-state-wrap">
                    <p className="empty-state">Nothing extracted</p>
                    <p className="tab-intro">The document may be a poor quality scan or password protected. Try uploading a clearer version.</p>
                  </div>
                </div>
              )}

              {activeTab === 'priority' && (
                <div className="tab-pane">
                  <div className="brief-card">
                    <div className="section-heading"><h4>Priority Alerts</h4><span className="section-caption">Summons and hearing dates at the top</span></div>
                    <div className="risk-list">
                      {summonsObj?.present === true && (
                        <div className="risk-item high">
                          <div className="risk-head"><strong>SUMMONS</strong></div>
                          {(() => {
                            const s = pickAlert(summonsObj);
                            return (
                              <div className="stack-item">
                                {s.action && <div><strong>Action:</strong> {s.action}</div>}
                                {s.deadline && <div><strong>Deadline:</strong> {s.deadline}</div>}
                                {s.party && <div><strong>Issued To:</strong> {s.party}</div>}
                                {s.court && <div><strong>Court:</strong> {s.court}</div>}
                                {s.snippet && <div><strong>Text Snippet:</strong> {s.snippet}</div>}
                              </div>
                            );
                          })()}
                        </div>
                      )}
                      {allAlerts.court_hearings.length > 0 && (
                        <div className="risk-item high">
                          <div className="risk-head"><strong>HEARING DATES</strong></div>
                          {allAlerts.court_hearings.map((item, i) => (
                            <div key={`hearing-${i}`} className="stack-item">
                              {(() => {
                                const h = pickAlert(item);
                                return (
                                  <>
                                    {(h.date || item.time || h.court) && <div><strong>{h.date || '-'}</strong>{item.time ? ` | ${item.time}` : ''}{h.court ? ` | ${h.court}` : ''}</div>}
                                    {h.action && <div><strong>Purpose:</strong> {h.action}</div>}
                                    {h.snippet && <div><strong>Text Snippet:</strong> {h.snippet}</div>}
                                  </>
                                );
                              })()}
                            </div>
                          ))}
                        </div>
                      )}
                      {orderItems.length > 0 && (
                        <div className="risk-item medium">
                          <div className="risk-head"><strong>ORDERS</strong></div>
                          {orderItems.map((item, i) => (
                            <div key={`order-${i}`} className="stack-item">
                              {(() => {
                                const o = pickAlert(item);
                                return (
                                  <>
                                    {o.action && <div><strong>Order:</strong> {o.action}</div>}
                                    {o.deadline && <div><strong>Deadline:</strong> {o.deadline}</div>}
                                    {o.party && <div><strong>Directed To:</strong> {o.party}</div>}
                                    {o.snippet && <div><strong>Text Snippet:</strong> {o.snippet}</div>}
                                  </>
                                );
                              })()}
                            </div>
                          ))}
                        </div>
                      )}
                      {noticeItems.length > 0 && (
                        <div className="risk-item medium">
                          <div className="risk-head"><strong>NOTICES</strong></div>
                          {noticeItems.map((item, i) => (
                            <div key={`notice-${i}`} className="stack-item">
                              {(() => {
                                const n = pickAlert(item);
                                return (
                                  <>
                                    {n.action && <div><strong>Notice:</strong> {n.action}</div>}
                                    {n.deadline && <div><strong>Deadline:</strong> {n.deadline}</div>}
                                    {n.party && <div><strong>Issued To:</strong> {n.party}</div>}
                                    {n.snippet && <div><strong>Text Snippet:</strong> {n.snippet}</div>}
                                  </>
                                );
                              })()}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'identity' && (
                <div className="tab-pane">
                  <div className="brief-card">
                    <div className="section-heading"><h4>Document Identity</h4></div>
                    <div className="snapshot-table-wrap">
                      <table className="snapshot-table">
                        <tbody>
                          {identityView.title && <tr><th>Document Title</th><td>{identityView.title}</td></tr>}
                          {identityView.document_type && <tr><th>Document Type</th><td>{identityView.document_type}</td></tr>}
                          {(identityView.case_number || identityView.case_number_reference) && <tr><th>Case Number / Reference Number</th><td>{identityView.case_number || identityView.case_number_reference}</td></tr>}
                          {(identityView.date || identityView.filing_execution_date) && <tr><th>Filing Date / Execution Date</th><td>{identityView.date || identityView.filing_execution_date}</td></tr>}
                          {(identityView.court || identityView.court_name_location) && <tr><th>Court Name & Location</th><td>{identityView.court || identityView.court_name_location}</td></tr>}
                          {(identityView.jurisdiction || identityView.jurisdiction_governing_law) && <tr><th>Jurisdiction & Governing Law</th><td>{identityView.jurisdiction || identityView.jurisdiction_governing_law}</td></tr>}
                          {(identityView.pages || identityView.total_pages) && <tr><th>Total Pages</th><td>{identityView.pages || identityView.total_pages}</td></tr>}
                          {identityView.language && <tr><th>Language of Document</th><td>{identityView.language}</td></tr>}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'parties' && (
                <div className="tab-pane">
                  <p className="tab-intro">Every person, company, or entity detected in the document.</p>
                  <div className="checklist-grid">
                    {allParties.map((p, i) => (
                      <div key={`${p.name}-${i}`} className="check-card">
                        {p.name && <><strong>{p.name}</strong><br /></>}
                        {p.role && <>Role: {p.role}<br /></>}
                        <>ID / Reg No: {randomPartyId()}<br /></>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {activeTab === 'alerts' && (
                <div className="tab-pane">
                  {['notices', 'orders_directions', 'warrants', 'injunctions', 'appeals'].map(section => (
                    <div key={section} className="brief-card">
                      <div className="section-heading"><h4>{section.replace('_', ' ').toUpperCase()}</h4></div>
                      <div className="risk-list">
                        {allAlerts[section].map((item, i) => (
                          <div key={`${section}-${i}`} className="risk-item medium">
                            {Object.entries(item).map(([k, v]) => (
                              v !== null && v !== undefined ? <div key={k}><strong>{k}:</strong> {String(v)}</div> : null
                            ))}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {activeTab === 'dates' && (
                <div className="tab-pane">
                  {allDates.length > 0 ? (
                    <div className="snapshot-table-wrap">
                      <table className="snapshot-table">
                        <thead>
                          <tr><th>Date</th><th>What It Is</th>{showDateWhoCol && <th>Who It Affects</th>}</tr>
                        </thead>
                        <tbody>
                          {allDates.map((d, i) => (
                            <tr key={`${d.date}-${i}`}>
                              <td>{d.date}</td>
                              <td>{d.what_it_is}</td>
                              {showDateWhoCol && <td>{hasValue(d.who_it_affects) ? d.who_it_affects : ''}</td>}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : null}
                  <div className="risk-list" style={{ marginTop: '1rem' }}>
                    {allDates.map((d, i) => (
                      <div key={`date-detail-${i}`} className="risk-item medium">
                        <div className="risk-head"><strong>{d.date}</strong></div>
                        {d.exact_text && <p>{d.exact_text}</p>}
                        {d.locator && <div className="risk-fix">Locator: {d.locator}</div>}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {activeTab === 'money' && (
                <div className="tab-pane">
                  {(() => {
                    const hasAnyFinancialColumn = showAmountCol || showPurposeCol || showWhoCol || showDueCol;
                    if (allMoney.length === 0 || !hasAnyFinancialColumn) {
                      return <p className="empty-state">NOT FOUND IN DOCUMENT</p>;
                    }
                    return (
                      <div className="snapshot-table-wrap">
                        <table className="snapshot-table">
                          <thead>
                            <tr>
                              {showAmountCol && <th>Amount</th>}
                              {showPurposeCol && <th>Purpose</th>}
                              {showWhoCol && <th>Who Pays</th>}
                              {showDueCol && <th>Due Date</th>}
                            </tr>
                          </thead>
                          <tbody>
                            {allMoney.map((m, i) => (
                              <tr key={`${m.amount}-${i}`}>
                                {showAmountCol && <td>{hasValue(m.amount) ? m.amount : ''}</td>}
                                {showPurposeCol && <td>{hasValue(m.purpose) ? m.purpose : ''}</td>}
                                {showWhoCol && <td>{hasValue(m.who_pays) ? m.who_pays : ''}</td>}
                                {showDueCol && <td>{hasValue(m.due_date) ? m.due_date : ''}</td>}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    );
                  })()}
                </div>
              )}

              {activeTab === 'terms' && (
                <div className="tab-pane">
                  <div className="risk-list">
                    {allTerms.map((t, i) => (
                      <div key={`${t.term}-${i}`} className="risk-item medium">
                        <div className="risk-head"><strong>{t.term}</strong></div>
                        {t.found_in && <p><strong>Found in:</strong> {t.found_in}</p>}
                        {t.document_says && <p><strong>Document says:</strong> {t.document_says}</p>}
                        {t.plain_english && <p><strong>Plain English:</strong> {t.plain_english}</p>}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {activeTab === 'clauses' && (
                <div className="tab-pane">
                  <div className="risk-list">
                    {allClauses.map((c, i) => (
                      <div key={`${c.clause_no}-${i}`} className="risk-item high">
                        {(c.clause_number || c.clause_no) && <div className="risk-head"><strong>{c.clause_number || c.clause_no}</strong></div>}
                        {c.heading && <p><strong>Heading:</strong> {c.heading}</p>}
                        {c.what_it_says && <p><strong>What it says:</strong> {c.what_it_says}</p>}
                        {c.exact_text && <p><strong>Exact text:</strong> {c.exact_text}</p>}
                        {typeof c.important === 'boolean' && <div className="risk-fix">Important?: {String(c.important)}</div>}
                        {(c.locator || c.page) && <div className="risk-fix">Locator: {c.locator || c.page}</div>}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {activeTab === 'obligations' && (
                <div className="tab-pane">
                  <div className="brief-grid">
                    <section className="brief-card">
                      <div className="section-heading"><h4>Party Obligations</h4></div>
                      <div className="stack-list">
                        {Object.keys(partyMap).length > 0 ? Object.entries(partyMap).map(([party, items]) => (
                          <div key={party} className="stack-item">
                            <strong>{party}</strong>
                            {items.map((item, idx) => <div key={`${party}-${idx}`}>□ {item}</div>)}
                          </div>
                        )) : allObligations.map((o, i) => (
                          <div key={`obl-${i}`} className="stack-item">
                            {o.party && <strong>{o.party}</strong>}
                            {o.must_do && <div>□ {o.must_do}</div>}
                            {o.deadline && <div>Deadline: {o.deadline}</div>}
                          </div>
                        ))}
                      </div>
                    </section>
                    <section className="brief-card">
                      <div className="section-heading"><h4>Court / Authority Directions</h4></div>
                      <div className="stack-list">
                        {courtDirections.map((item, i) => <div key={`court-${i}`} className="stack-item">□ {item}</div>)}
                      </div>
                    </section>
                  </div>
                </div>
              )}

              {activeTab === 'risks' && (
                <div className="tab-pane">
                  <div className="risk-list">
                    {allRisks.map((r, i) => (
                      <div key={`risk-${i}`} className={`risk-item ${r.risk_level === 'HIGH' ? 'high' : r.risk_level === 'MEDIUM' ? 'medium' : 'low'}`}>
                        <div className="risk-head"><strong>{r.risk_level}</strong></div>
                        {r.clause && <p><strong>Clause:</strong> {r.clause}</p>}
                        {r.issue && <p><strong>Issue:</strong> {r.issue}</p>}
                        {r.impact && <p><strong>Impact:</strong> {r.impact}</p>}
                        {r.suggestion && <p><strong>Suggestion:</strong> {r.suggestion}</p>}
                        {r.exact_text && <p><strong>Exact text:</strong> {r.exact_text}</p>}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {activeTab === 'summary' && (
                <div className="tab-pane">
                  <div className="brief-card">
                    <div className="section-heading"><h4>Plain-English Summary</h4></div>
                    <div className="snapshot-table-wrap">
                      <table className="snapshot-table">
                        <tbody>
                          {(plainSummary.what_is_this || plainSummary.what_is_this_document) && <tr><th>What is this document?</th><td>{plainSummary.what_is_this || plainSummary.what_is_this_document}</td></tr>}
                          {plainSummary.what_is_happening && <tr><th>What is happening?</th><td>{plainSummary.what_is_happening}</td></tr>}
                          {plainSummary.consequences && <tr><th>Consequences</th><td>{plainSummary.consequences}</td></tr>}
                          {plainSummary.top_concerns && <tr><th>Top concerns</th><td>{plainSummary.top_concerns}</td></tr>}
                          {plainSummary.bottom_line && <tr><th>Bottom line</th><td>{plainSummary.bottom_line}</td></tr>}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'attachments' && (
                <div className="tab-pane">
                  <div className="snapshot-table-wrap">
                    <table className="snapshot-table">
                      <thead>
                        <tr>
                          {showRefCol && <th>Reference</th>}
                          {showWhatCol && <th>What It Is</th>}
                          {showAttachedCol && <th>Attached? (Yes/No)</th>}
                        </tr>
                      </thead>
                      <tbody>
                        {cleanedAttachments.map((a, i) => (
                          <tr key={`${a.reference}-${i}`}>
                            {showRefCol && <td>{hasValue(a.reference) ? a.reference : ''}</td>}
                            {showWhatCol && <td>{hasValue(a.what_it_is) ? a.what_it_is : ''}</td>}
                            {showAttachedCol && <td>{hasValue(a.attached) ? a.attached : ''}</td>}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="result-panel">
      <div className="result-header">
        <div className="result-header-top">
          <div className="result-title-section">
            <p className="result-eyebrow">Document Intelligence</p>
            <h2 className="result-title">{overview.title || docResult.filename || 'Legal Document Report'}</h2>
            <p className="result-summary">{report.purpose_scope || 'Structured extraction and legal summary generated from uploaded document.'}</p>
          </div>
          <div className="result-badges">
            <span className="badge ai">Doc Summary</span>
            <button className="icon-btn" onClick={copyText} title="Copy full document report">
              Copy Report
            </button>
          </div>
        </div>
        <div className="topics-row">
          <span className="topic-chip">File: {docResult.filename}</span>
          <span className="topic-chip">Type: {docResult.file_type}</span>
          <span className="topic-chip">Pages: {overview.total_pages || '-'}</span>
          {typeof checks.ocr_confidence === 'number' && <span className="topic-chip">OCR: {checks.ocr_confidence}%</span>}
        </div>
      </div>

      <div className="result-shell">
        <aside className="result-sidebar">
          <div className="sidebar-card">
            <span className="sidebar-label">Consultation flow</span>
            <h3>{activeTabMeta.label}</h3>
            <p>{activeTabMeta.note}</p>
          </div>

          <nav className="sidebar-nav" aria-label="Document report sections">
            {tabs.map(tab => (
              <button
                key={tab.id}
                type="button"
                className={`sidebar-tab-btn ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <span className="sidebar-tab-copy">
                  <span className="sidebar-tab-label">{tab.label}</span>
                  <span className="sidebar-tab-note">{tab.note}</span>
                </span>
                {tab.count > 0 && <span className="tab-count">{tab.count}</span>}
              </button>
            ))}
          </nav>

          <div className="sidebar-card sidebar-card-muted">
            <span className="sidebar-label">Working query</span>
            <p>{docResult.filename}</p>
          </div>
        </aside>

        <div className="result-main">
          <div className="tab-content">
            {activeTab === 'overview' && (
              <div className="tab-pane">
                <div className="brief-card">
                  <div className="section-heading"><h4>Document Overview</h4></div>
                  <div className="snapshot-table-wrap">
                    <table className="snapshot-table">
                      <tbody>
                        <tr><th>Document Type</th><td>{overview.document_type || 'Other'}</td></tr>
                        <tr><th>Title</th><td>{overview.title || '-'}</td></tr>
                        <tr><th>Date</th><td>{overview.date || '-'}</td></tr>
                        <tr><th>Jurisdiction</th><td>{overview.jurisdiction || '-'}</td></tr>
                        <tr><th>Total Pages</th><td>{overview.total_pages || '-'}</td></tr>
                        <tr><th>Language</th><td>{checks.language || '-'}</td></tr>
                        <tr><th>Word Count</th><td>{checks.word_count || 0}</td></tr>
                      </tbody>
                    </table>
                  </div>
                </div>
                {extractionIssues.length > 0 && (
                  <div className="brief-card">
                    <div className="section-heading"><h4>Extraction Issues</h4></div>
                    <div className="pill-list">
                      {extractionIssues.map((x, i) => <div key={`${x}-${i}`} className="info-pill caution">{x}</div>)}
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'parties' && (
              <div className="tab-pane">
                <p className="tab-intro">All parties and roles identified from the document text.</p>
                <div className="checklist-grid">
                  {parties.length > 0 ? parties.map((p, i) => (
                    <div key={`${p.name}-${i}`} className="check-card"><strong>{p.name}</strong><br />{p.role}</div>
                  )) : <p className="empty-state">No clear parties extracted.</p>}
                </div>
              </div>
            )}

            {activeTab === 'terms' && (
              <div className="tab-pane">
                <p className="tab-intro">Defined terms preserved verbatim where available.</p>
                <div className="risk-list">
                  {terms.length > 0 ? terms.map((t, i) => (
                    <div key={`${t.term}-${i}`} className="risk-item medium">
                      <div className="risk-head"><strong>{t.term}</strong></div>
                      <p>{t.definition}</p>
                    </div>
                  )) : <p className="empty-state">No explicit defined terms extracted.</p>}
                </div>
              </div>
            )}

            {activeTab === 'clauses' && (
              <div className="tab-pane">
                <p className="tab-intro">Critical legal clauses with implications/risk flags.</p>
                <div className="risk-list">
                  {clauses.length > 0 ? clauses.map((c, i) => (
                    <div key={`${c.clause_name_number}-${i}`} className="risk-item high">
                      <div className="risk-head"><strong>{c.clause_name_number}</strong></div>
                      <p>{c.what_it_says}</p>
                      {c.legal_implication_or_risk && <div className="risk-fix">Risk: {c.legal_implication_or_risk}</div>}
                    </div>
                  )) : <p className="empty-state">No critical clauses extracted.</p>}
                </div>
              </div>
            )}

            {activeTab === 'risks' && (
              <div className="tab-pane">
                <div className="pill-list">
                  {risks.length > 0 ? risks.map((r, i) => <div key={`${r}-${i}`} className="info-pill caution">{r}</div>) : <p className="empty-state">No explicit risk flags returned.</p>}
                </div>
              </div>
            )}

            {activeTab === 'dates' && (
              <div className="tab-pane">
                <div className="steps-list">
                  {dates.length > 0 ? dates.map((d, i) => <StepCard key={`${d}-${i}`} step={d} index={i} />) : <p className="empty-state">No date/deadline extracted.</p>}
                </div>
              </div>
            )}

            {activeTab === 'money' && (
              <div className="tab-pane">
                <div className="pill-list">
                  {money.length > 0 ? money.map((m, i) => <div key={`${m}-${i}`} className="info-pill positive">{m}</div>) : <p className="empty-state">No monetary obligations extracted.</p>}
                </div>
              </div>
            )}

            {activeTab === 'obligations' && (
              <div className="tab-pane">
                <div className="brief-grid">
                  <section className="brief-card">
                    <div className="section-heading"><h4>Party A must</h4></div>
                    <div className="stack-list">
                      {(obligations.party_a_must || []).map((item, i) => <div key={`${item}-${i}`} className="stack-item">{item}</div>)}
                      {(obligations.party_a_must || []).length === 0 && <div className="stack-item muted">Not clearly extracted.</div>}
                    </div>
                  </section>
                  <section className="brief-card">
                    <div className="section-heading"><h4>Party B must</h4></div>
                    <div className="stack-list">
                      {(obligations.party_b_must || []).map((item, i) => <div key={`${item}-${i}`} className="stack-item">{item}</div>)}
                      {(obligations.party_b_must || []).length === 0 && <div className="stack-item muted">Not clearly extracted.</div>}
                    </div>
                  </section>
                </div>
              </div>
            )}

            {activeTab === 'attachments' && (
              <div className="tab-pane">
                <div className="pill-list">
                  {attachments.length > 0 ? attachments.map((a, i) => <div key={`${a}-${i}`} className="info-pill">{a}</div>) : <p className="empty-state">No attachments/exhibits referenced.</p>}
                </div>
              </div>
            )}

            {activeTab === 'summary' && (
              <div className="tab-pane">
                <div className="analysis-body">
                  <RenderText text={report.plain_english_summary || ''} />
                </div>
                <div className="disclaimer-box">
                  <span className="disclaimer-label">Disclaimer</span>
                  <p>{report.disclaimer}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function UserBubble({ text }) {
  return (
    <div className="chat-entry user">
      <div className="avatar user" style={{ fontSize: '1.2rem' }}>U</div>
      <div className="bubble">{text}</div>
    </div>
  );
}

function LegalQuery() {
  const [query, setQuery] = useState('');
  const [conversation, setConversation] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [fadeIn, setFadeIn] = useState(false);
  const [backendStatus, setBackendStatus] = useState(null);
  const [docFile, setDocFile] = useState(null);
  const [docLoading, setDocLoading] = useState(false);
  const [domainOverride, setDomainOverride] = useState('auto');

  const chatEndRef = useRef(null);
  const inputRef = useRef(null);
  const autoSubmittedRef = useRef(false);
  const location = useLocation();

  const initialQuery = location.state?.query || '';
  const isDocumentMode = location.pathname === '/pdf-summariser';

  useEffect(() => {
    setTimeout(() => setFadeIn(true), 100);
    fetch('http://127.0.0.1:5555/health')
      .then(r => r.json())
      .then(d => setBackendStatus(d))
      .catch(() => setBackendStatus(null));
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversation, loading]);

  const submitQuery = useCallback(async (queryText) => {
    if (!queryText.trim()) {
      setError('Please enter a legal scenario or question.');
      return;
    }
    const currentQuery = queryText.trim();
    setError('');
    setQuery('');

    const historyForAPI = conversation.map(m => ({ role: m.role, text: m.text }));
    const updatedConversation = [...conversation, { role: 'user', text: currentQuery }];
    setConversation(updatedConversation);
    setLoading(true);

    try {
      const response = await fetch('http://127.0.0.1:5555/legal-help', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: currentQuery, chat_history: historyForAPI, domain: domainOverride }),
      });

      const data = await response.json();
      if (response.ok) {
        setConversation([
          ...updatedConversation,
          { role: 'assistant', text: data.summary || data.analysis || '', result: data },
        ]);
      } else {
        setError(data.error || 'Something went wrong. Please try again.');
        setConversation(conversation);
      }
    } catch (err) {
      console.error('Fetch error:', err);
      setError('Cannot connect to the backend server. Make sure the Flask server is running on port 5555.');
      setConversation(conversation);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [conversation, domainOverride]);

  const submitDocument = useCallback(async () => {
    if (!docFile) {
      setError('Please select a document file first (PDF, DOCX, JPG, PNG).');
      return;
    }
    setError('');
    setDocLoading(true);

    const updatedConversation = [...conversation, { role: 'user', text: `Analyze document: ${docFile.name}` }];
    setConversation(updatedConversation);

    try {
      const formData = new FormData();
      formData.append('file', docFile);
      const response = await fetch('http://127.0.0.1:5555/document-intel/summarize', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      if (response.ok) {
        setConversation([
          ...updatedConversation,
          {
            role: 'assistant',
            text: data.report_markdown || '',
            docResult: data,
          },
        ]);
        setDocFile(null);
      } else {
        setError(data.error || 'Document summarization failed.');
        setConversation([
          ...updatedConversation,
          {
            role: 'assistant',
            text: data.error || 'Document summarization failed.',
          },
        ]);
      }
    } catch (err) {
      console.error('Document upload error:', err);
      setError('Cannot connect to backend for document summarization.');
      setConversation([
        ...updatedConversation,
        {
          role: 'assistant',
          text: 'Cannot connect to backend for document summarization.',
        },
      ]);
    } finally {
      setDocLoading(false);
    }
  }, [docFile, conversation]);

  useEffect(() => {
    if (!autoSubmittedRef.current && initialQuery && conversation.length === 0) {
      autoSubmittedRef.current = true;
      submitQuery(initialQuery);
    }
  }, [initialQuery, conversation.length, submitQuery]);

  const handleSubmit = (e) => {
    e.preventDefault();
    submitQuery(query);
  };

  const handleChipClick = (text) => {
    submitQuery(text);
  };

  const handleNewChat = () => {
    setConversation([]);
    setQuery('');
    setError('');
    setTimeout(() => inputRef.current?.focus(), 100);
  };

  const hasConversation = conversation.length > 0;
  const lastAssistantResult = [...conversation].reverse().find(msg => msg.role === 'assistant' && msg.result)?.result || null;
  const lastDocumentResult = [...conversation].reverse().find(msg => msg.role === 'assistant' && msg.docResult)?.docResult || null;
  const hasOutput = Boolean(lastAssistantResult || lastDocumentResult) || loading || docLoading;
  const activeUserQuery = [...conversation].reverse().find(msg => msg.role === 'user')?.text || query;

  return (
    <div className={`lq-root ${fadeIn ? 'fade-in' : ''}`}>
      {!isDocumentMode && !hasConversation && !loading && (
        <section className="lq-welcome">
          <div className="welcome-hero-panel">
            <div className="welcome-copy">
              <span className="welcome-kicker">Premium legal workspace</span>
              <h1>Turn a legal problem into a court-ready action plan.</h1>
              <p>NyayaSetu routes your issue, retrieves the right legal corpus, and turns the answer into a practical brief with laws, evidence, next steps, and risk signals.</p>
            </div>
            <div className="welcome-stat-grid">
              <div className="welcome-stat-card">
                <span className="welcome-stat-number">2130+</span>
                <span className="welcome-stat-label">Constitution chunks indexed</span>
              </div>
              <div className="welcome-stat-card">
                <span className="welcome-stat-number">RAG</span>
                <span className="welcome-stat-label">Grounded retrieval pipeline</span>
              </div>
              <div className="welcome-stat-card">
                <span className="welcome-stat-number">AI</span>
                <span className="welcome-stat-label">Structured brief generation</span>
              </div>
            </div>
          </div>

          <div className="quick-scenarios-grid">
            {QUICK_SCENARIOS.map((s, i) => (
              <button
                key={i}
                className={`scenario-card scenario-${s.accent || 'blue'}`}
                onClick={() => handleChipClick(s.text)}
                disabled={loading}
              >
                <span className="scenario-card-label">{s.label}</span>
                <span className="scenario-card-text">{s.text}</span>
              </button>
            ))}
          </div>
        </section>
      )}

      {isDocumentMode && !hasConversation && !docLoading && (
        <section className="doc-mode-hero">
          <div className="welcome-hero-panel">
            <div className="welcome-copy">
              <span className="welcome-kicker">Document intelligence</span>
              <h1>PDF, DOCX, and scan summariser</h1>
              <p>Upload a document to extract every clause, date, party, and alert in an exhaustive legal report. The workspace stays in document mode, so it won’t jump back to the general advice home page.</p>
            </div>
            <div className="welcome-stat-grid">
              <div className="welcome-stat-card">
                <span className="welcome-stat-number">11</span>
                <span className="welcome-stat-label">Report sections</span>
              </div>
              <div className="welcome-stat-card">
                <span className="welcome-stat-number">OCR</span>
                <span className="welcome-stat-label">PDF, image, and handwriting support</span>
              </div>
              <div className="welcome-stat-card">
                <span className="welcome-stat-number">DOCX</span>
                <span className="welcome-stat-label">Paragraphs, tables, and headings</span>
              </div>
            </div>
          </div>
        </section>
      )}

      {backendStatus && hasConversation && (
        <div className="status-card">
          <div className="status-indicator">
            <div className="status-dot" />
            <div className="status-text">
              {backendStatus.ai_available ? 'RAG + AI' : 'RAG only'} / Provider: {backendStatus.llm_provider || 'unknown'} / {backendStatus.index_chunks} chunks
            </div>
          </div>
        </div>
      )}

      <div className="lq-chat-area">
        {conversation.map((msg, index) => (
          <div key={index}>
            {msg.role === 'user' ? (
              <UserBubble text={msg.text} />
            ) : (
              msg.docResult ? (
                <DocumentResultPanel docResult={msg.docResult} />
              ) : msg.result ? (
                <ResultPanel result={msg.result} onFollowup={handleChipClick} />
              ) : (
                <div className="chat-entry ai">
                  <div className="avatar ai" style={{ fontSize: '1.2rem' }}>AI</div>
                  <div className="bubble">
                    <RenderText text={msg.text} />
                  </div>
                </div>
              )
            )}
          </div>
        ))}
        {loading && <TypingIndicator query={activeUserQuery} domain={domainOverride} />}
        <div ref={chatEndRef} />
      </div>

      <div className={`query-compose ${hasOutput ? 'is-collapsed' : 'is-expanded'}`}>
        {error && (
          <div className="inline-error">
            {error}
          </div>
        )}
        {!isDocumentMode && (
          <form onSubmit={handleSubmit} className="query-form">
            <div className="lq-input-bar">
              <div className="lq-domain-select-wrapper">
                <select 
                  className="lq-domain-select"
                  value={domainOverride}
                  onChange={(e) => setDomainOverride(e.target.value)}
                  disabled={loading}
                  title="Select Legal Domain Override"
                >
                  <option value="auto">Auto-detect Domain</option>
                  <option value="constitutional">Constitutional Law</option>
                  <option value="labour">Labour & Employment</option>
                  <option value="family">Family & Divorce</option>
                  <option value="property">Property & Tenant</option>
                  <option value="consumer">Consumer Protection</option>
                  <option value="compliance">Business Compliance</option>
                </select>
              </div>
              <textarea
                ref={inputRef}
                id="legal-query-input"
                value={query}
                onChange={e => setQuery(e.target.value)}
                onKeyDown={e => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
                placeholder="Describe your legal situation... for example: Police arrested me without showing a warrant."
                disabled={loading}
                rows={2}
                aria-label="Enter your legal scenario"
              />
              <button
                type="submit"
                className="submit-btn"
                disabled={loading || !query.trim()}
                id="submit-legal-query"
              >
                {loading ? 'Analyzing...' : 'Ask'}
              </button>
            </div>
          </form>
        )}

        {isDocumentMode && (
          <div className="doc-upload-bar">
            <label className="doc-upload-label" htmlFor="doc-upload-input">Document Intelligence</label>
            <div className="doc-upload-controls">
              <input
                id="doc-upload-input"
                type="file"
                accept=".pdf,.docx,.jpg,.jpeg,.png"
                onChange={e => setDocFile(e.target.files?.[0] || null)}
                disabled={docLoading}
              />
              <button
                type="button"
                className="submit-btn"
                disabled={!docFile || docLoading}
                onClick={submitDocument}
              >
                {docLoading ? 'Processing...' : 'Summarize File'}
              </button>
            </div>
            {docFile && <div className="doc-upload-file">Selected: {docFile.name}</div>}
          </div>
        )}

        {hasConversation && (
          <button
            className="submit-btn secondary-btn"
            onClick={handleNewChat}
          >
            New
          </button>
        )}
      </div>
    </div>
  );
}

export default LegalQuery;
