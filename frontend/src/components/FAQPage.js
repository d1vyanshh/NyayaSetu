import React, { useState } from 'react';
import { Link } from 'react-router-dom';

const FAQPage = () => {
  const [activeIndex, setActiveIndex] = useState(null);

  const faqs = [
    {
      question: "What is LegalAI and how does it work?",
      answer: "LegalAI is an AI-powered legal assistance platform that analyzes constitutional provisions and related legal principles. Our system uses advanced AI algorithms to process legal queries, analyze documents, and provide legal information based on constitutional law and established legal precedents."
    },
    {
      question: "Is LegalAI a substitute for a lawyer?",
      answer: "No, LegalAI is not a substitute for professional legal advice. While our platform provides valuable legal information and analysis, it should be used as a supplementary tool. For specific legal matters, we recommend consulting with a qualified attorney."
    },
    {
      question: "What types of legal issues can LegalAI help with?",
      answer: "LegalAI can assist with various legal matters including constitutional law analysis, document review, business legal consultation, property law, family law, employment law, privacy rights, education rights, healthcare rights, and digital rights. Our services are based on constitutional provisions and related legal principles."
    },
    {
      question: "How accurate is the legal information provided?",
      answer: "While we strive for accuracy, LegalAI's responses are based on AI analysis and should be verified by legal professionals. Our system continuously learns and improves, but users should exercise discretion and seek professional legal advice for critical matters."
    },
    {
      question: "Is my legal information kept confidential?",
      answer: "Yes, we take privacy seriously. All legal queries and documents are encrypted and stored securely. We have strict privacy policies in place to protect your information. Please refer to our Privacy Policy for detailed information."
    },
    {
      question: "How do I get started with LegalAI?",
      answer: "Getting started is easy! Simply create an account, choose a subscription plan, and you can begin using our services. You can start by asking legal questions, uploading documents for review, or exploring our various legal assistance features."
    },
    {
      question: "What are the subscription options?",
      answer: "We offer various subscription plans to suit different needs, including monthly and annual options. Each plan comes with different features and usage limits. Visit our Pricing page for detailed information about our subscription options."
    },
    {
      question: "Can I cancel my subscription?",
      answer: "Yes, you can cancel your subscription at any time. However, please note that subscription fees are non-refundable. You'll continue to have access to the service until the end of your current billing period."
    },
    {
      question: "How does the AI document review work?",
      answer: "Our AI document review system analyzes legal documents by identifying key provisions, potential issues, and relevant legal principles. It can help identify important clauses, suggest improvements, and provide explanations of complex legal language."
    },
    {
      question: "What if I need more specialized legal help?",
      answer: "For complex or specialized legal matters, we recommend consulting with a qualified attorney. While LegalAI provides general legal information and analysis, certain situations may require personalized legal advice from a licensed professional."
    }
  ];

  const toggleFAQ = (index) => {
    setActiveIndex(activeIndex === index ? null : index);
  };

  return (
    <div className="page-container faq-page">
      <div className="faq-header">
        <h1>Frequently Asked Questions</h1>
        <div className="faq-subtitle">Find answers to common questions about LegalAI</div>
      </div>

      <div className="faq-content">
        {faqs.map((faq, index) => (
          <div 
            key={index} 
            className={`faq-item ${activeIndex === index ? 'active' : ''}`}
            onClick={() => toggleFAQ(index)}
          >
            <div className="faq-question">
              <h3>{faq.question}</h3>
              <span className="faq-icon">
                {activeIndex === index ? '−' : '+'}
              </span>
            </div>
            {activeIndex === index && (
              <div className="faq-answer">
                <p>{faq.answer}</p>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="faq-cta">
        <h2>Still have questions?</h2>
        <p>Contact our support team for additional assistance</p>
        <Link to="/contact" className="cta-button">Contact Support</Link>
      </div>
    </div>
  );
};

export default FAQPage; 