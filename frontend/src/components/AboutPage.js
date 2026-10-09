import React from "react";

const AboutPage = () => {
  return (
    <div className="page-container about-page">
      <div className="about-header">
        <h1>About LegalAI</h1>
        <div className="about-subtitle">
          Transforming legal assistance with AI
        </div>
      </div>

      <div className="about-content">
        <section className="about-section">
          <h2>Our Mission</h2>
          <p>
            At LegalAI, we're committed to making legal assistance accessible to
            everyone. Our advanced AI technology is designed to provide quick,
            reliable legal guidance for common questions and concerns, bridging
            the gap between complex legal matters and everyday understanding.
          </p>
        </section>

        <section className="about-section">
          <h2>How Our AI Works</h2>
          <p>
            Our AI system has been trained on a vast database of legal
            documents, case studies, and expert knowledge. When you submit a
            query, our algorithms analyze your question, identify relevant legal
            concepts, and generate a clear, concise response based on
            established legal principles and precedents.
          </p>
          <div className="ai-process">
            <div className="process-step">
              <div className="step-number">1</div>
              <div className="step-title">Query Analysis</div>
              <p>
                Your question is analyzed to understand intent and legal context
              </p>
            </div>
            <div className="process-step">
              <div className="step-number">2</div>
              <div className="step-title">Information Retrieval</div>
              <p>
                Relevant legal information is gathered from our knowledge base
              </p>
            </div>
            <div className="process-step">
              <div className="step-number">3</div>
              <div className="step-title">Response Generation</div>
              <p>
                A clear, tailored answer is created specifically for your
                situation
              </p>
            </div>
          </div>
        </section>

        <section className="about-section">
          <h2>Important Disclaimer</h2>
          <div className="disclaimer-box">
            <p>
              While our AI provides valuable legal information, it should not be
              considered a substitute for professional legal advice. LegalAI is
              an informational resource designed to help you understand legal
              concepts and potential approaches to common legal issues.
            </p>
            <p>
              For specific legal concerns, we strongly recommend consulting with
              a qualified attorney who can provide personalized guidance based
              on your unique circumstances and the specific laws in your
              jurisdiction.
            </p>
          </div>
        </section>

        <section className="about-section">
          <h2>Our Team</h2>
          <p>
            LegalAI was developed by a team of legal experts, AI researchers,
            and software engineers dedicated to improving access to legal
            knowledge. Our diverse team brings together expertise from
            prestigious law schools, leading technology companies, and
            innovative AI research labs.
          </p>
          <div className="team-grid">
            <div className="team-member">
              <div className="member-avatar">👨‍⚖️</div>
              <div className="member-name">Gaurang Mundhra</div>
              <div className="member-title">Legal Director</div>
            </div>
            <div className="team-member">
              <div className="member-avatar">👨‍💻</div>
              <div className="member-name">Pranit Dugad</div>
              <div className="member-title">Chief Technology Officer</div>
            </div>
            <div className="team-member">
              <div className="member-avatar">👨‍💻</div>
              <div className="member-name">Gaurang Dhole</div>
              <div className="member-title">AI Research Lead</div>
            </div>
            <div className="team-member">
              <div className="member-avatar">👨‍💻</div>
              <div className="member-name">Rushikesh Gaikar</div>
              <div className="member-title">Legal Research Specialist</div>
            </div>
            <div className="team-member">
              <div className="member-avatar">👨‍💻</div>
              <div className="member-name">Atharva Raut</div>
              <div className="member-title">Legal Research Specialist</div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default AboutPage;
