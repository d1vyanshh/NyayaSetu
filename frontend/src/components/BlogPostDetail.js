import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { blogPosts } from './BlogData';

const BlogPostDetail = () => {
  const { id } = useParams();
  const [post, setPost] = useState(null);
  const [relatedPosts, setRelatedPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [shareSupported, setShareSupported] = useState(false);

  useEffect(() => {
    // Check if Web Share API is supported
    setShareSupported(navigator.share !== undefined);
    
    // Find the current blog post based on URL param
    const currentPost = blogPosts.find(post => post.id === parseInt(id));
    
    if (currentPost) {
      setPost(currentPost);
      
      // Find related posts from the same category
      const related = blogPosts
        .filter(p => p.category === currentPost.category && p.id !== currentPost.id)
        .slice(0, 3);
      
      setRelatedPosts(related);
    }
    
    setLoading(false);
    
    // Scroll to top when post changes
    window.scrollTo(0, 0);
  }, [id]);

  const handleShare = async () => {
    const shareData = {
      title: post.title,
      text: post.excerpt,
      url: window.location.href,
    };

    try {
      if (navigator.share) {
        await navigator.share(shareData);
      }
    } catch (error) {
      console.error('Error sharing:', error);
    }
  };

  const shareToTwitter = () => {
    const text = encodeURIComponent(`${post.title}\n`);
    const url = encodeURIComponent(window.location.href);
    window.open(`https://twitter.com/intent/tweet?text=${text}&url=${url}`, '_blank');
  };

  const shareToFacebook = () => {
    const url = encodeURIComponent(window.location.href);
    window.open(`https://www.facebook.com/sharer/sharer.php?u=${url}`, '_blank');
  };

  const shareToLinkedIn = () => {
    const url = encodeURIComponent(window.location.href);
    const title = encodeURIComponent(post.title);
    const summary = encodeURIComponent(post.excerpt);
    window.open(`https://www.linkedin.com/shareArticle?mini=true&url=${url}&title=${title}&summary=${summary}`, '_blank');
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(window.location.href)
      .then(() => {
        alert('Link copied to clipboard');
      })
      .catch(err => {
        console.error('Failed to copy:', err);
      });
  };

  if (loading) {
    return (
      <div className="page-container blog-post-loading">
        <div className="loading-spinner"></div>
        <p>Loading article...</p>
      </div>
    );
  }

  if (!post) {
    return (
      <div className="page-container blog-post-error">
        <h2>Blog Post Not Found</h2>
        <p>Sorry, we couldn't find the blog post you were looking for.</p>
        <Link to="/blog" className="back-to-blog">
          ← Back to Blog
        </Link>
      </div>
    );
  }

  return (
    <div className="page-container blog-post-detail">
      <div className="blog-post-navigation">
        <Link to="/blog" className="back-to-blog">
          ← Back to Blog
        </Link>
        <div className="blog-post-category">{post.category}</div>
      </div>
      
      <article className="blog-post-content">
        <div className="blog-post-header">
          <h1>{post.title}</h1>
          <div className="blog-post-meta">
            <span className="post-date">{post.date}</span>
            <span className="post-read-time">{post.readTime}</span>
          </div>
        </div>
        
        <div className="blog-post-featured-image">
          <img src={post.image} alt={post.title} />
        </div>
        
        <div className="blog-post-body">
          <h2>Introduction</h2>
          <p>{post.excerpt}</p>
          
          <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam auctor, nisl eget ultricies aliquam, nunc nisl aliquet nunc, quis aliquam nisl nunc quis nisl. Nullam auctor, nisl eget ultricies aliquam, nunc nisl aliquet nunc, quis aliquam nisl nunc quis nisl.</p>
          
          <h2>Key Points</h2>
          <p>Proin et varius est. Etiam scelerisque metus vitae purus aliquam, et finibus ligula hendrerit. Nulla facilisi. Praesent scelerisque sem id bibendum mattis. Integer sit amet mauris eget dui lobortis vehicula.</p>
          
          <ul>
            <li>Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas.</li>
            <li>Vestibulum tortor quam, feugiat vitae, ultricies eget, tempor sit amet, ante.</li>
            <li>Donec eu libero sit amet quam egestas semper.</li>
            <li>Aenean ultricies mi vitae est. Mauris placerat eleifend leo.</li>
          </ul>
          
          <h2>Legal Analysis</h2>
          <p>Fusce ac turpis quis ligula lacinia aliquet. Mauris ipsum. Nulla metus metus, ullamcorper vel, tincidunt sed, euismod in, nibh. Quisque volutpat condimentum velit. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos.</p>
          
          <blockquote>
            "Proin sodales pulvinar sic tempor. Sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Nam fermentum, nulla luctus pharetra vulputate, felis tellus mollis orci, sed rhoncus pronin sapien nunc accuan eget."
          </blockquote>
          
          <p>Maecenas tempus, tellus eget condimentum rhoncus, sem quam semper libero, sit amet adipiscing sem neque sed ipsum. Nam quam nunc, blandit vel, luctus pulvinar, hendrerit id, lorem. Maecenas nec odio et ante tincidunt tempus.</p>
          
          <h2>Conclusion</h2>
          <p>Donec vitae sapien ut libero venenatis faucibus. Nullam quis ante. Etiam sit amet orci eget eros faucibus tincidunt. Duis leo. Sed fringilla mauris sit amet nibh. Donec sodales sagittis magna.</p>
        </div>
        
        <div className="blog-post-tags">
          <span className="tag-label">Tags:</span>
          <div className="tags">
            <span className="tag">Legal</span>
            <span className="tag">{post.category}</span>
            <span className="tag">Analysis</span>
          </div>
        </div>
        
        <div className="blog-post-share">
          <span className="share-label">Share:</span>
          <div className="share-buttons">
            {shareSupported && (
              <button className="share-button share-all" onClick={handleShare} aria-label="Share">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="18" cy="5" r="3"></circle>
                  <circle cx="6" cy="12" r="3"></circle>
                  <circle cx="18" cy="19" r="3"></circle>
                  <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line>
                  <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line>
                </svg>
              </button>
            )}
            <button 
              className="share-button" 
              onClick={shareToTwitter} 
              aria-label="Share on Twitter"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 4s-.7 2.1-2 3.4c1.6 10-9.4 17.3-18 11.6 2.2.1 4.4-.6 6-2C3 15.5.5 9.6 3 5c2.2 2.6 5.6 4.1 9 4-.9-4.2 4-6.6 7-3.8 1.1 0 3-1.2 3-1.2z"></path>
              </svg>
            </button>
            <button 
              className="share-button" 
              onClick={shareToFacebook} 
              aria-label="Share on Facebook"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"></path>
              </svg>
            </button>
            <button 
              className="share-button" 
              onClick={shareToLinkedIn} 
              aria-label="Share on LinkedIn"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path>
                <rect x="2" y="9" width="4" height="12"></rect>
                <circle cx="4" cy="4" r="2"></circle>
              </svg>
            </button>
            <button 
              className="share-button"
              onClick={copyToClipboard}
              aria-label="Copy link"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
              </svg>
            </button>
          </div>
        </div>
      </article>
      
      {relatedPosts.length > 0 && (
        <div className="related-posts">
          <h3>Related Articles</h3>
          <div className="related-posts-grid">
            {relatedPosts.map(relatedPost => (
              <Link key={relatedPost.id} to={`/blog/${relatedPost.id}`} className="related-post-card">
                <div className="related-post-image">
                  <img src={relatedPost.image} alt={relatedPost.title} />
                </div>
                <div className="related-post-content">
                  <h4>{relatedPost.title}</h4>
                  <span className="related-post-date">{relatedPost.date}</span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default BlogPostDetail; 