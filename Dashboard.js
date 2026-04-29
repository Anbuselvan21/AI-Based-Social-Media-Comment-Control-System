import React, { useState, useEffect } from 'react';
import axios from 'axios';

function Dashboard({ user }) {
  const [stats, setStats] = useState({
    total: 0,
    text: 0,
    image: 0
  });
  const [recentComments, setRecentComments] = useState([]);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('http://localhost:5000/api/history', {
        headers: { Authorization: `Bearer ${token}` }
      });

      const comments = response.data;
      setStats({
        total: comments.length,
        text: comments.filter(c => c.type === 'text').length,
        image: comments.filter(c => c.type === 'image').length
      });
      setRecentComments(comments.slice(0, 5));
    } catch (err) {
      console.error('Failed to fetch history:', err);
    }
  };

  const getPredictionClass = (prediction) => {
    switch (prediction) {
      case 'Non-Abusive': return 'safe';
      case 'Abusive': return 'danger';
      case 'Intermediate': return 'warning';
      default: return '';
    }
  };

  return (
    <div className="dashboard">
      <div className="welcome-section">
        <h2>Welcome, {user?.username || 'User'}! 👋</h2>
        <p>AI-Powered Social Media Comment Control System - Protect your platform from harmful content</p>
      </div>

      <div className="main-options">
        <div className="option-card" onClick={() => window.location.href = '/text-comment'}>
          <div className="option-icon text-icon">💬</div>
          <h3>Text Comment Analysis</h3>
          <p>Analyze text comments for offensive content using AI</p>
        </div>
        <div className="option-card" onClick={() => window.location.href = '/image-comment'}>
          <div className="option-icon image-icon">🖼️</div>
          <h3>Image Comment Analysis</h3>
          <p>Analyze image comments for inappropriate content</p>
        </div>
      </div>

      <div className="stats-section">
        <div className="section-header">
          <h3>📊 Your Statistics</h3>
        </div>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon total">📝</div>
            <div className="stat-info">
              <div className="stat-value">{stats.total}</div>
              <div className="stat-label">Total Comments</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon safe">💬</div>
            <div className="stat-info">
              <div className="stat-value">{stats.text}</div>
              <div className="stat-label">Text Comments</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon warning">🖼️</div>
            <div className="stat-info">
              <div className="stat-value">{stats.image}</div>
              <div className="stat-label">Image Comments</div>
            </div>
          </div>
        </div>
      </div>

      {recentComments.length > 0 && (
        <div className="recent-section">
          <div className="section-header">
            <h3>🕐 Recent Comments</h3>
          </div>
          <div className="recent-list">
            {recentComments.map(comment => (
              <div key={comment.id} className={`recent-item ${getPredictionClass(comment.prediction)}`}>
                <div className="recent-content">
                  <span className="recent-type">{comment.type.toUpperCase()}</span>
                  <div className="recent-text">
                    {comment.content || <em>Image: {comment.image_path}</em>}
                  </div>
                </div>
                <div className={`recent-prediction ${getPredictionClass(comment.prediction)}`}>
                  {comment.prediction}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
