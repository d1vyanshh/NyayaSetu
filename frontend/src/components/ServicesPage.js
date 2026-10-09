import React, { useState } from 'react';
import { Link } from 'react-router-dom';

const ServicesPage = () => {
  const [activeTab, setActiveTab] = useState('all');

  const services = [
    {
      id: 1,
      icon: '⚖️',
      title: 'Constitutional Law Analysis',
      description: 'Get expert analysis of constitutional provisions, fundamental rights, and constitutional remedies. Understand your constitutional rights and protections.',
      features: [
        'Analysis of fundamental rights',
        'Constitutional remedies guidance',
        'Interpretation of constitutional provisions',
        'Case law references',
        'Legal precedents analysis'
      ],
      category: 'featured'
    },
    {
      id: 2,
      icon: '📝',
      title: 'Legal Document Review',
      description: 'Have our AI analyze legal documents, contracts, and agreements to identify potential issues and explain complex legal language.',
      features: [
        'Contract clause analysis',
        'Plain language explanation of terms',
        'Risk identification',
        'Compliance checking',
        'Standard practice comparison'
      ],
      category: 'featured'
    },
    {
      id: 3,
      icon: '🏢',
      title: 'Business Legal Consultation',
      description: 'Get guidance on business formation, compliance, intellectual property, and corporate legal matters.',
      features: [
        'Business formation guidance',
        'Compliance requirements',
        'IP protection strategies',
        'Contract drafting assistance',
        'Regulatory compliance'
      ],
      category: 'business'
    },
    {
      id: 4,
      icon: '🏠',
      title: 'Property Law Assistance',
      description: 'Information about property laws, real estate transactions, and property rights under the Constitution.',
      features: [
        'Property rights analysis',
        'Real estate transaction guidance',
        'Land acquisition laws',
        'Property dispute resolution',
        'Constitutional property protections'
      ],
      category: 'property'
    },
    {
      id: 5,
      icon: '👪',
      title: 'Family Law Guidance',
      description: 'Understanding family law provisions, marriage laws, and constitutional protections for family rights.',
      features: [
        'Marriage laws analysis',
        'Family rights protection',
        'Divorce provisions',
        'Child custody guidance',
        'Constitutional family protections'
      ],
      category: 'personal'
    },
    {
      id: 6,
      icon: '💼',
      title: 'Employment Law Support',
      description: 'Information about labor laws, workplace rights, and constitutional protections for workers.',
      features: [
        'Labor rights analysis',
        'Workplace discrimination',
        'Employment contracts',
        'Workers\' rights protection',
        'Constitutional labor provisions'
      ],
      category: 'business'
    },
    {
      id: 7,
      icon: '🔒',
      title: 'Privacy & Data Protection',
      description: 'Understanding privacy rights, data protection laws, and constitutional privacy protections.',
      features: [
        'Privacy rights analysis',
        'Data protection laws',
        'Digital rights guidance',
        'Privacy policy review',
        'Constitutional privacy protections'
      ],
      category: 'digital'
    },
    {
      id: 8,
      icon: '🎓',
      title: 'Education Rights',
      description: 'Information about educational rights, constitutional provisions for education, and related legal matters.',
      features: [
        'Right to education analysis',
        'Educational institution regulations',
        'Student rights protection',
        'Education policy guidance',
        'Constitutional education provisions'
      ],
      category: 'personal'
    },
    {
      id: 9,
      icon: '🏥',
      title: 'Healthcare Rights',
      description: 'Understanding healthcare rights, medical laws, and constitutional provisions for health.',
      features: [
        'Healthcare rights analysis',
        'Medical laws guidance',
        'Patient rights protection',
        'Healthcare policy review',
        'Constitutional health provisions'
      ],
      category: 'personal'
    },
    {
      id: 10,
      icon: '🌐',
      title: 'Digital Rights & Cyber Law',
      description: 'Guidance on digital rights, cyber laws, and constitutional protections in the digital space.',
      features: [
        'Digital rights analysis',
        'Cyber law provisions',
        'Online privacy protection',
        'Digital security guidance',
        'Constitutional digital protections'
      ],
      category: 'digital'
    }
  ];

  const categories = [
    { id: 'all', name: 'All Services' },
    { id: 'featured', name: 'Featured' },
    { id: 'business', name: 'Business' },
    { id: 'personal', name: 'Personal' },
    { id: 'property', name: 'Property' },
    { id: 'digital', name: 'Digital' }
  ];

  const filteredServices = activeTab === 'all' 
    ? services 
    : services.filter(service => service.category === activeTab);

  return (
    <div className="page-container services-page">
      <div className="services-hero">
        <div className="services-hero-content">
          <h1>AI-Powered Legal Services</h1>
          <p className="services-subtitle">Comprehensive legal assistance based on advanced analysis of constitutional provisions</p>
          <div className="services-stats">
            <div className="stat">
              <span className="stat-number">10+</span>
              <span className="stat-label">Practice Areas</span>
            </div>
            <div className="stat">
              <span className="stat-number">24/7</span>
              <span className="stat-label">Availability</span>
            </div>
            <div className="stat">
              <span className="stat-number">99%</span>
              <span className="stat-label">Accuracy</span>
            </div>
          </div>
        </div>
      </div>
      
      <div className="services-intro">
        <div className="services-intro-content">
          <h2>How Our AI Legal Services Can Help You</h2>
          <p>
            Our advanced AI platform offers a range of legal assistance services designed to help you understand and navigate 
            constitutional provisions and related legal matters. Each service is powered by our sophisticated AI system 
            that analyzes constitutional text and relevant legal principles to provide accurate, reliable guidance.
          </p>
        </div>
      </div>
      
      <div className="services-categories">
        {categories.map(category => (
          <button
            key={category.id}
            className={`category-button ${activeTab === category.id ? 'active' : ''}`}
            onClick={() => setActiveTab(category.id)}
          >
            {category.name}
          </button>
        ))}
      </div>
      
      <div className="services-grid">
        {filteredServices.map(service => (
          <div key={service.id} className={`service-card ${service.category === 'featured' ? 'featured' : ''}`}>
            <div className="service-header">
              <div className="service-icon">{service.icon}</div>
              <h3>{service.title}</h3>
            </div>
            <p className="service-description">{service.description}</p>
            
            <div className="service-features">
              <h4>What's included:</h4>
              <ul>
                {service.features.map((feature, index) => (
                  <li key={index}>{feature}</li>
                ))}
              </ul>
            </div>
            
            <Link to="/" className="service-action-button ripple-button">Get Started</Link>
          </div>
        ))}
      </div>
      
      <div className="services-process">
        <h2>How It Works</h2>
        <div className="process-steps">
          <div className="process-step">
            <div className="step-number">1</div>
            <h3 className="step-title">Describe Your Legal Issue</h3>
            <p>Tell us about your legal concern or question in detail. The more information you provide, the more accurate our AI can be.</p>
          </div>
          <div className="process-step">
            <div className="step-number">2</div>
            <h3 className="step-title">AI Analysis</h3>
            <p>Our advanced AI analyzes constitutional provisions, legal precedents, and relevant laws to generate comprehensive insights.</p>
          </div>
          <div className="process-step">
            <div className="step-number">3</div>
            <h3 className="step-title">Review Your Results</h3>
            <p>Receive detailed analysis and guidance specific to your situation, with clear explanations and actionable recommendations.</p>
          </div>
        </div>
      </div>
      
      <div className="services-cta">
        <div className="cta-content">
          <h2>Need Specialized Legal Help?</h2>
          <p>
            For complex legal matters requiring personalized attention, we can provide detailed analysis 
            of constitutional provisions and related legal principles specific to your situation.
          </p>
          <div className="cta-buttons">
            <Link to="/" className="cta-button primary pulse-button">Try It Now</Link>
            <Link to="/contact" className="cta-button secondary ripple-button">Contact Us</Link>
          </div>
        </div>
      </div>
      
      <div className="services-testimonials">
        <h2>What Our Clients Say</h2>
        <div className="testimonials-grid">
          <div className="testimonial">
            <div className="testimonial-content">
              <p>"The constitutional law analysis provided by LegalAI was incredibly thorough and helped me understand my rights much better than I expected."</p>
            </div>
            <div className="testimonial-author">
              <span className="author-name">Michael K.</span>
              <span className="author-title">Business Owner</span>
            </div>
          </div>
          <div className="testimonial">
            <div className="testimonial-content">
              <p>"I was impressed by the depth of analysis for my property rights question. The AI provided clear guidance that helped me resolve my issue."</p>
            </div>
            <div className="testimonial-author">
              <span className="author-name">Sarah J.</span>
              <span className="author-title">Property Investor</span>
            </div>
          </div>
          <div className="testimonial">
            <div className="testimonial-content">
              <p>"The document review service saved me hours of reading complex legal language. The plain-English explanations were exactly what I needed."</p>
            </div>
            <div className="testimonial-author">
              <span className="author-name">David L.</span>
              <span className="author-title">Small Business Owner</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ServicesPage; 