import React from 'react';

const PrivacyPolicy = () => {
  return (
    <div className="page-container privacy-page">
      <div className="privacy-header">
        <h1>Privacy Policy</h1>
        <div className="privacy-subtitle">Last updated: {new Date().toLocaleDateString()}</div>
      </div>

      <div className="privacy-content">
        <section className="privacy-section">
          <h2>1. Introduction</h2>
          <p>
            At LegalAI, we take your privacy seriously. This Privacy Policy explains how we collect, use, 
            and protect your personal information when you use our AI-powered legal assistance platform.
          </p>
        </section>

        <section className="privacy-section">
          <h2>2. Information We Collect</h2>
          <div className="privacy-list">
            <h3>2.1 Personal Information</h3>
            <ul>
              <li>Contact information (email, phone number)</li>
              <li>Account credentials</li>
              <li>Payment information</li>
              <li>Communication preferences</li>
            </ul>

            <h3>2.2 Legal Information</h3>
            <ul>
              <li>Legal queries and questions</li>
              <li>Document uploads</li>
              <li>Case-related information</li>
              <li>Legal research history</li>
            </ul>
          </div>
        </section>

        <section className="privacy-section">
          <h2>3. How We Use Your Information</h2>
          <div className="privacy-list">
            <ul>
              <li>Provide legal assistance and analysis</li>
              <li>Improve our AI algorithms</li>
              <li>Personalize your experience</li>
              <li>Communicate with you about our services</li>
              <li>Ensure platform security</li>
            </ul>
          </div>
        </section>

        <section className="privacy-section">
          <h2>4. Data Security</h2>
          <p>
            We implement industry-standard security measures to protect your information, including:
          </p>
          <div className="privacy-list">
            <ul>
              <li>End-to-end encryption</li>
              <li>Secure data storage</li>
              <li>Regular security audits</li>
              <li>Access controls</li>
            </ul>
          </div>
        </section>

        <section className="privacy-section">
          <h2>5. Your Rights</h2>
          <div className="privacy-list">
            <ul>
              <li>Access your personal data</li>
              <li>Request data correction</li>
              <li>Request data deletion</li>
              <li>Opt-out of communications</li>
              <li>Export your data</li>
            </ul>
          </div>
        </section>

        <section className="privacy-section">
          <h2>6. Contact Us</h2>
          <p>
            If you have any questions about this Privacy Policy or our data practices, please contact us at:
          </p>
          <div className="contact-info">
            <p>Email: privacy@legalai.com</p>
            <p>Phone: +1 (555) 123-4567</p>
            <p>Address: 123 Legal Street, Suite 456, San Francisco, CA 94103</p>
          </div>
        </section>
      </div>
    </div>
  );
};

export default PrivacyPolicy; 