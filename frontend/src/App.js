import React, { useState, useEffect } from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import Hero from './components/Hero';
import LegalQuery from './components/LegalQuery';
import AdvancedLegalTools from './components/AdvancedLegalTools';
import JudgementPrediction from './components/JudgementPrediction';
import NyayaDraft from './components/NyayaDraft';
import ContactPage from './components/ContactPage';
import PrivacyPolicy from './components/PrivacyPolicy';
import TermsOfService from './components/TermsOfService';
import FAQPage from './components/FAQPage';
import { ThemeProvider } from './contexts/ThemeContext';
import nyayaSetuLogo from './assets/nyayasetu-logo.svg';
import './App.css';

function App() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const location = useLocation();
  const [pageTransition, setPageTransition] = useState(false);

  useEffect(() => {
    setPageTransition(true);
    const timer = setTimeout(() => setPageTransition(false), 300);
    return () => clearTimeout(timer);
  }, [location.pathname]);

  // Close menu when user navigates or presses escape key
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        setIsMenuOpen(false);
      }
    };

    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, []);

  // Close menu when location changes
  useEffect(() => {
    setIsMenuOpen(false);
  }, [location.pathname]);

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  const closeMenu = () => {
    setIsMenuOpen(false);
  };

  return (
    <ThemeProvider>
      <div className="app">
        <a href="#main-content" className="skip-to-content">Skip to content</a>
        
        <header className="app-header">
          <div className="header-container">
            <Link to="/" className="app-logo" onClick={closeMenu} aria-label="NyayaSetu Home">
              <span className="brand-text">
                <span className="brand-nyaya">Nyaya</span>
                <span className="brand-setu">Setu</span>
              </span>
            </Link>
            
            <button 
              className="mobile-menu-button" 
              onClick={toggleMenu} 
              aria-label="Toggle menu"
              aria-expanded={isMenuOpen}
            >
              {isMenuOpen ? 'Close' : 'Menu'}
            </button>
            
            <nav className="app-nav">
              <ul className={`nav-links ${isMenuOpen ? 'active' : ''}`}>
                <li>
                  <Link 
                    to="/" 
                    className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
                    onClick={closeMenu}
                  >
                    Home
                  </Link>
                </li>
                <li>
                  <Link 
                    to="/legal-advice" 
                    className={`nav-link ${location.pathname === '/legal-advice' ? 'active' : ''}`}
                    onClick={closeMenu}
                  >
                    Get Advice
                  </Link>
                </li>
                <li>
                  <Link
                    to="/ai-legal-tools"
                    className={`nav-link ${location.pathname === '/ai-legal-tools' ? 'active' : ''}`}
                    onClick={closeMenu}
                  >
                    AI Tools
                  </Link>
                </li>
                <li>
                  <Link
                    to="/judgement-prediction"
                    className={`nav-link ${location.pathname === '/judgement-prediction' ? 'active' : ''}`}
                    onClick={closeMenu}
                  >
                    Judgement Predictor
                  </Link>
                </li>
                <li>
                  <Link
                    to="/nyayadraft"
                    className={`nav-link ${location.pathname === '/nyayadraft' ? 'active' : ''}`}
                    onClick={closeMenu}
                  >
                    NyayaDraft
                  </Link>
                </li>
                <li>
                  <Link
                    to="/pdf-summariser"
                    className={`nav-link ${location.pathname === '/pdf-summariser' ? 'active' : ''}`}
                    onClick={closeMenu}
                  >
                    PDF Summariser
                  </Link>
                </li>
                <li>
                  <Link 
                    to="/contact" 
                    className={`nav-link ${location.pathname === '/contact' ? 'active' : ''}`}
                    onClick={closeMenu}
                  >
                    Contact
                  </Link>
                </li>
              </ul>
            </nav>

          </div>
        </header>
        
        <main id="main-content" className={`main-content ${pageTransition ? 'page-transition' : ''}`}>
          <Routes>
            <Route 
              path="/" 
              element={
                <Hero 
                  title="Your Legal Brief, Instantly" 
                  subtitle="Premium, structured guidance grounded in the Constitution of India. Ask a question and receive a clear, actionable brief."
                  backgroundImage="https://images.unsplash.com/photo-1589829545856-d10d557cf95f?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80"
                />
              } 
            />
            <Route path="/legal-advice" element={<LegalQuery />} />
            <Route path="/ai-legal-tools" element={<AdvancedLegalTools />} />
            <Route path="/judgement-prediction" element={<JudgementPrediction />} />
            <Route path="/nyayadraft" element={<NyayaDraft />} />
            <Route path="/pdf-summariser" element={<LegalQuery />} />
            <Route path="/contact" element={<ContactPage />} />
            <Route path="/privacy" element={<PrivacyPolicy />} />
            <Route path="/terms" element={<TermsOfService />} />
            <Route path="/faq" element={<FAQPage />} />
          </Routes>
        </main>
        
        <footer className="app-footer">
          <div className="footer-content">
            <div className="footer-section">
              <h3>NyayaSetu</h3>
              <p>Premium AI guidance for constitutional questions</p>
              <div className="social-links">
                <a href="https://twitter.com" aria-label="Twitter" target="_blank" rel="noreferrer">
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M22 4s-.7 2.1-2 3.4c1.6 10-9.4 17.3-18 11.6 2.2.1 4.4-.6 6-2C3 15.5.5 9.6 3 5c2.2 2.6 5.6 4.1 9 4-.9-4.2 4-6.6 7-3.8 1.1 0 3-1.2 3-1.2z"></path>
                  </svg>
                </a>
                <a href="https://linkedin.com" aria-label="LinkedIn" target="_blank" rel="noreferrer">
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path>
                    <rect x="2" y="9" width="4" height="12"></rect>
                    <circle cx="4" cy="4" r="2"></circle>
                  </svg>
                </a>
                <a href="https://facebook.com" aria-label="Facebook" target="_blank" rel="noreferrer">
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"></path>
                  </svg>
                </a>
                <a href="https://instagram.com" aria-label="Instagram" target="_blank" rel="noreferrer">
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect>
                    <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path>
                    <line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line>
                  </svg>
                </a>
              </div>
            </div>
            <div className="footer-section">
              <h3>Quick Links</h3>
              <ul>
                <li><Link to="/legal-advice">Get Advice</Link></li>
                <li><Link to="/pdf-summariser">PDF Summariser</Link></li>
                <li><Link to="/contact">Contact</Link></li>
                <li><Link to="/faq">FAQ</Link></li>
              </ul>
            </div>
            <div className="footer-section">
              <h3>Legal</h3>
              <ul>
                <li><Link to="/privacy">Privacy Policy</Link></li>
                <li><Link to="/terms">Terms of Service</Link></li>
              </ul>
            </div>
            <div className="footer-section">
              <h3>Support</h3>
              <ul>
                <li><Link to="/faq">FAQ</Link></li>
                <li><Link to="/contact">Contact Support</Link></li>
              </ul>
            </div>
          </div>
          <div className="footer-bottom">
            <p>(c) {new Date().getFullYear()} LegalAI. All rights reserved.</p>
          </div>
        </footer>
      </div>
    </ThemeProvider>
  );
}

export default App;
