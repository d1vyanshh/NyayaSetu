import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

const Hero = ({
  title = 'Know Your Constitutional Rights',
  subtitle = 'Get clarity on laws and legal options with AI-powered analysis',
  backgroundImage = '/images/hero-bg.png',
}) => {
  const [query, setQuery] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [animateIn, setAnimateIn] = useState(false);
  const inputRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    // Trigger animation after component mount
    setAnimateIn(true);

    // Focus input after animation completes
    const timer = setTimeout(() => {
      if (inputRef.current) inputRef.current.focus();
    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) {
      setError('Please enter a legal question to proceed');
      if (inputRef.current) inputRef.current.focus();
      return;
    }

    setError('');
    setLoading(true);

    try {
      navigate('/legal-advice', { state: { query } });
    } catch (err) {
      console.error(err);
      setError('Failed to connect to the server. Please try again later.');
      if (inputRef.current) inputRef.current.focus();
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="hero" style={{ backgroundImage: `url(${backgroundImage})` }}>
      <div className="hero-overlay" aria-hidden="true"></div>

      {/* Animated background elements */}
      <div className="hero-bg-elements" aria-hidden="true">
        <div className="bg-element element-1"></div>
        <div className="bg-element element-2"></div>
        <div className="bg-element element-3"></div>
      </div>

      <div className={`hero-content ${animateIn ? 'animate-in' : ''}`}>
        <div className="hero-badge" aria-hidden="true">AI-Powered Legal Assistance</div>
        <h1 className="hero-title">{title}</h1>
        <p className="hero-subtitle">{subtitle}</p>
        <div className="hero-search-container">
          <form onSubmit={handleSubmit} className="hero-form" id="hero-query-form">
            <label htmlFor="hero-query" className="visually-hidden">Enter your legal question</label>
            <div className="input-group">
              <div className="input-icon" aria-hidden="true">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="11" cy="11" r="8"></circle>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                </svg>
              </div>
              <input
                ref={inputRef}
                type="text"
                id="hero-query"
                className="hero-form-input"
                placeholder="Describe your legal issue or ask a question..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                disabled={loading}
                aria-describedby={error ? "hero-error" : undefined}
              />
            </div>
          </form>

          <button
            type="submit"
            form="hero-query-form"
            className="hero-form-button ripple-button"
            disabled={loading}
            aria-label={loading ? "Processing your request" : "Get legal advice"}
          >
            {loading ? (
              <>
                <svg className="spinner" viewBox="0 0 50 50" aria-hidden="true">
                  <circle className="path" cx="25" cy="25" r="20" fill="none" strokeWidth="5"></circle>
                </svg>
                <span>Processing</span>
              </>
            ) : (
              <>Get Advice</>
            )}
          </button>
        </div>

        {error && (
          <div className="hero-error" id="hero-error" role="alert">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="8" x2="12" y2="12"></line>
              <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
            {error}
          </div>
        )}

          <div className="hero-features">
            <div className="feature">
              <div className="feature-icon" aria-hidden="true">⚖️</div>
              <div className="feature-text">Expert Legal Analysis</div>
            </div>
            <div className="feature">
              <div className="feature-icon" aria-hidden="true">⚡</div>
              <div className="feature-text">Instant Responses</div>
            </div>
            <div className="feature">
              <div className="feature-icon" aria-hidden="true">🔒</div>
              <div className="feature-text">Secure & Confidential</div>
            </div>
          </div>

        <div className="hero-cta-secondary">
          <a href="/legal-advice" className="cta-link">Start a consultation</a>
          <span className="cta-separator" aria-hidden="true">or</span>
          <a href="/about" className="cta-link">Learn how it works</a>
        </div>
      </div>
    </section>
  );
};

export default Hero;