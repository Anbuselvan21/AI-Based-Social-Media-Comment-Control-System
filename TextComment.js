import React, { useState, useEffect } from 'react';
import axios from 'axios';

function TextComment() {
  const [text, setText] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [realtimeFeedback, setRealtimeFeedback] = useState(null);
  const [history, setHistory] = useState([]);
  const [warningCount, setWarningCount] = useState(0);
  const [blocked, setBlocked] = useState(false);

  useEffect(() => {
    fetchHistory();
  }, []);

  useEffect(() => {
    if (text.trim().length > 0) {
      const timer = setTimeout(() => {
        checkRealtime(text);
      }, 500);
      return () => clearTimeout(timer);
    } else {
      setRealtimeFeedback(null);
    }
  }, [text]);

  const checkRealtime = async (textToCheck) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        'http://localhost:5000/api/predict-text/realtime',
        { text: textToCheck },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setRealtimeFeedback(response.data);
    } catch (err) {
      console.error('Realtime check failed:', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;

    setLoading(true);
    setResult(null);

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        'http://localhost:5000/api/predict-text',
        { text },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      if (response.data.blocked) {
        setBlocked(true);
        setResult(response.data);
      } else {
        setResult(response.data);
        if (response.data.warning) {
          setWarningCount(response.data.warning_count || 0);
        }
        fetchHistory();
      }
    } catch (err) {
      if (err.response?.status === 403) {
        setBlocked(true);
        setResult(err.response?.data);
      }
      console.error('Prediction failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('http://localhost:5000/api/history', {
        headers: { Authorization: `Bearer ${token}` }
      });
      const textComments = response.data.filter(c => c.type === 'text');
      setHistory(textComments.slice(0, 10));
    } catch (err) {
      console.error('Failed to fetch history:', err);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
  };

  const getFeedbackClass = () => {
    if (!realtimeFeedback) return '';
    if (!realtimeFeedback.detected) return 'feedback-safe';
    if (realtimeFeedback.severity === 'abusive') return 'feedback-danger';
    if (realtimeFeedback.severity === 'intermediate') return 'feedback-warning';
    return 'feedback-safe';
  };

  const canPost = () => {
    if (blocked) return false;
    if (!text.trim()) return false;
    if (loading) return false;
    if (realtimeFeedback && realtimeFeedback.severity === 'abusive') return false;
    return true;
  };

  const getButtonText = () => {
    if (blocked) return 'Account Blocked';
    if (loading) return 'Analyzing...';
    if (realtimeFeedback && realtimeFeedback.severity === 'abusive') return 'Cannot Post Abusive Content';
    if (warningCount > 0) return `Post (Warning: ${warningCount}/3)`;
    return 'Post Comment';
  };

  const getResultClass = () => {
    if (!result) return '';
    if (result.blocked) return 'result-danger';
    if (result.result?.prediction === 'Non-Abusive') return 'result-safe';
    if (result.result?.prediction === 'Intermediate') return 'result-warning';
    return '';
  };

  if (blocked) {
    return (
      <div className="comment-interface">
        <div className="blocked-overlay">
          <div className="blocked-card">
            <div className="blocked-icon">🚫</div>
            <h2>Account Blocked</h2>
            <p>Your account has been blocked due to multiple violations of community guidelines.</p>
            <p className="blocked-message">Please contact the administrator for further assistance.</p>
            <button onClick={handleLogout} className="btn-primary">
              Return to Login
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="comment-interface">
      <div className="page-header">
        <h2>Text Comment Analysis</h2>
        <p className="page-subtitle">AI-Based Social Media Comment Control System</p>
        {warningCount > 0 && (
          <div className="warning-banner">
            <span>⚠️</span> You have {warningCount} warning(s). After 3 warnings, your account will be blocked.
          </div>
        )}
      </div>

      <div className="content-grid">
        <div className="input-section">
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Enter your comment:</label>
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Type your comment here..."
                rows={6}
                className="comment-textarea"
                disabled={blocked}
              />
            </div>

            {realtimeFeedback && (
              <div className={`realtime-feedback ${getFeedbackClass()}`}>
                <span className="feedback-icon">
                  {!realtimeFeedback.detected ? '✓' : 
                   realtimeFeedback.severity === 'abusive' ? '🚫' : '⚠️'}
                </span>
                <span className="feedback-message">{realtimeFeedback.message}</span>
                {realtimeFeedback.words && realtimeFeedback.words.length > 0 && (
                  <div className="detected-words">
                    Detected: {realtimeFeedback.words.join(', ')}
                  </div>
                )}
              </div>
            )}

            {result?.warning && !result.blocked && (
              <div className="warning-notice">
                <span className="warning-icon">⚠️</span>
                <span>{result.warning_message}</span>
              </div>
            )}

            <button 
              type="submit" 
              className={`btn-primary btn-large ${!canPost() ? 'btn-disabled' : ''}`}
              disabled={!canPost()}
            >
              {loading ? (
                <>
                  <span className="spinner"></span>
                  Analyzing...
                </>
              ) : getButtonText()}
            </button>
          </form>

          {result && !result.blocked && (
            <div className={`prediction-result ${getResultClass()}`}>
              <h3>Prediction Result</h3>
              <div className="result-main">
                <div className="result-prediction">{result.result.prediction}</div>
                <div className="result-confidence">
                  Confidence: {result.result.confidence}%
                </div>
              </div>
              
              <div className="result-probabilities">
                <h4>Probabilities</h4>
                <div className="probability-bar">
                  <div className="probability-label">Abusive</div>
                  <div className="probability-track">
                    <div 
                      className="probability-fill danger"
                      style={{ width: `${result.result.probabilities.abusive}%` }}
                    />
                  </div>
                  <div className="probability-value">{result.result.probabilities.abusive}%</div>
                </div>
                <div className="probability-bar">
                  <div className="probability-label">Non-Abusive</div>
                  <div className="probability-track">
                    <div 
                      className="probability-fill safe"
                      style={{ width: `${result.result.probabilities.non_abusive}%` }}
                    />
                  </div>
                  <div className="probability-value">{result.result.probabilities.non_abusive}%</div>
                </div>
                <div className="probability-bar">
                  <div className="probability-label">Intermediate</div>
                  <div className="probability-track">
                    <div 
                      className="probability-fill warning"
                      style={{ width: `${result.result.probabilities.intermediate}%` }}
                    />
                  </div>
                  <div className="probability-value">{result.result.probabilities.intermediate}%</div>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="history-section">
          <h3>Recent Text Comments</h3>
          {history.length === 0 ? (
            <p className="no-history">No text comments yet</p>
          ) : (
            <div className="history-list">
              {history.map(comment => (
                <div key={comment.id} className="history-item">
                  <div className="history-content">{comment.content}</div>
                  <div className="history-meta">
                    <span className={`history-prediction ${
                      comment.prediction === 'Non-Abusive' ? 'safe' :
                      comment.prediction === 'Abusive' ? 'danger' : 'warning'
                    }`}>
                      {comment.prediction}
                    </span>
                    <span className="history-confidence">{comment.confidence}%</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default TextComment;
