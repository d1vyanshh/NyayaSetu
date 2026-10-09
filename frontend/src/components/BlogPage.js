import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { blogPosts } from './BlogData';

const BlogPage = () => {
  const [activeCategory, setActiveCategory] = useState('All Posts');

  const categories = ['All Posts', ...new Set(blogPosts.map(post => post.category))];

  const filteredPosts = activeCategory === 'All Posts' 
    ? blogPosts 
    : blogPosts.filter(post => post.category === activeCategory);

  return (
    <div className="page-container blog-page">
      <div className="blog-header">
        <h1>Legal Insights Blog</h1>
        <div className="blog-subtitle">Stay informed with the latest legal analysis and updates</div>
      </div>

      <div className="blog-categories">
        {categories.map(category => (
          <button
            key={category}
            className={`category-button ${activeCategory === category ? 'active' : ''}`}
            onClick={() => setActiveCategory(category)}
          >
            {category}
          </button>
        ))}
      </div>

      <div className="blog-grid">
        {filteredPosts.map(post => (
          <article key={post.id} className="blog-card">
            <div className="blog-image">
              <img src={post.image} alt={post.title} />
              <div className="blog-category">{post.category}</div>
            </div>
            <div className="blog-content">
              <div className="blog-meta">
                <span className="blog-date">{post.date}</span>
                <span className="blog-read-time">{post.readTime}</span>
              </div>
              <h2>{post.title}</h2>
              <p>{post.excerpt}</p>
              <Link to={`/blog/${post.id}`} className="read-more">
                Read More
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M4 8H12M12 8L8 4M12 8L8 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </Link>
            </div>
          </article>
        ))}
      </div>

      <div className="blog-newsletter">
        <h2>Subscribe to Our Legal Insights</h2>
        <p>Get the latest legal analysis and updates delivered to your inbox</p>
        <form className="newsletter-form">
          <input 
            type="email" 
            placeholder="Enter your email address" 
            className="newsletter-input"
            required
          />
          <button type="submit" className="newsletter-button">Subscribe</button>
        </form>
      </div>
    </div>
  );
};

export default BlogPage; 