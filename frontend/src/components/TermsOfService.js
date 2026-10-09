import React from 'react';

const TermsOfService = () => {
  return (
    <div className="page-container terms-page">
      <div className="terms-header">
        <h1>Terms of Service</h1>
        <div className="terms-subtitle">Last updated: {new Date().toLocaleDateString()}</div>
      </div>

      <div className="terms-content">
        <section className="terms-section">
          <h2>1. Acceptance of Terms</h2>
          <p>
            By accessing and using LegalAI's services, you agree to be bound by these Terms of Service 
            and all applicable laws and regulations. If you do not agree with any of these terms, you 
            are prohibited from using or accessing this platform.
          </p>
        </section>

        <section className="terms-section">
          <h2>2. Description of Service</h2>
          <p>
            LegalAI provides AI-powered legal assistance and analysis based on constitutional provisions 
            and related legal principles. Our services include but are not limited to:
          </p>
          <div className="terms-list">
            <ul>
              <li>Constitutional law analysis</li>
              <li>Legal document review</li>
              <li>Legal research assistance</li>
              <li>Case law analysis</li>
              <li>Legal guidance and recommendations</li>
            </ul>
          </div>
        </section>

        <section className="terms-section">
          <h2>3. User Responsibilities</h2>
          <div className="terms-list">
            <ul>
              <li>Provide accurate and complete information</li>
              <li>Maintain the confidentiality of your account</li>
              <li>Use the service for lawful purposes only</li>
              <li>Comply with all applicable laws and regulations</li>
              <li>Respect intellectual property rights</li>
            </ul>
          </div>
        </section>

        <section className="terms-section">
          <h2>4. Limitations of Service</h2>
          <p>
            While LegalAI provides legal information and analysis, it is important to understand that:
          </p>
          <div className="terms-list">
            <ul>
              <li>Our service does not constitute legal advice</li>
              <li>We are not a law firm or a substitute for an attorney</li>
              <li>Our AI-generated content should be verified by legal professionals</li>
              <li>We do not guarantee the accuracy of all information provided</li>
            </ul>
          </div>
        </section>

        <section className="terms-section">
          <h2>5. Intellectual Property</h2>
          <p>
            All content, features, and functionality of the LegalAI platform are owned by LegalAI and 
            are protected by international copyright, trademark, and other intellectual property laws.
          </p>
        </section>

        <section className="terms-section">
          <h2>6. Payment Terms</h2>
          <div className="terms-list">
            <ul>
              <li>Subscription fees are billed in advance</li>
              <li>All payments are non-refundable</li>
              <li>Prices are subject to change with notice</li>
              <li>Free trial terms and conditions apply</li>
            </ul>
          </div>
        </section>

        <section className="terms-section">
          <h2>7. Termination</h2>
          <p>
            We reserve the right to terminate or suspend your account and access to the service at our 
            sole discretion, without notice, for conduct that we believe violates these Terms or is 
            harmful to other users, us, or third parties, or for any other reason.
          </p>
        </section>

        <section className="terms-section">
          <h2>8. Contact Information</h2>
          <div className="contact-info">
            <p>For questions about these Terms, please contact us at:</p>
            <p>Email: legal@legalai.com</p>
            <p>Phone: +1 (555) 123-4567</p>
            <p>Address: 123 Legal Street, Suite 456, San Francisco, CA 94103</p>
          </div>
        </section>
      </div>
    </div>
  );
};

export default TermsOfService; 