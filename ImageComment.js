import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

function ImageComment() {
  const [selectedImage, setSelectedImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const [warningCount, setWarningCount] = useState(0);
  const [blocked, setBlocked] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('http://localhost:5000/api/history', {
        headers: { Authorization: `Bearer ${token}` }
      });
      const imageComments = response.data
        .filter(c => c.type === 'image' && c.prediction !== 'Error')
        .slice(0, 10);
      setHistory(imageComments);
    } catch (err) {
      console.error('Failed to fetch history:', err);
    }
  };

  const handleImageSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedImage(file);
      setPreview(URL.createObjectURL(file));
      setResult(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      setSelectedImage(file);
      setPreview(URL.createObjectURL(file));
      setResult(null);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedImage) return;

    setLoading(true);
    setResult(null);

    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('image', selectedImage);

      const response = await axios.post(
        'http://localhost:5000/api/predict-image',
        formData,
        {
          headers: { 
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      );
      
      if (response.data.blocked) {
        setBlocked(true);
        setResult(response.data);
      } else {
        setResult(response.data);
        if (response.data.warning) {
          setWarningCount(response.data.warning_count || 0);
        }
        if (!response.data.abusive_blocked) {
          fetchHistory();
        }
      }
    } catch (err) {
      console.error('Full error:', err);
      console.error('Response:', err.response);
      console.error('Response data:', err.response?.data);
      
      if (err.response?.status === 403) {
        setBlocked(true);
        setResult(err.response?.data);
      } else {
        const errorData = err.response?.data || {};
        setResult({
          result: {
            prediction: 'Error',
            confidence: 0,
            probabilities: { abusive: 0, non_abusive: 0, intermediate: 0 },
            error: errorData.error || errorData.message || err.message || 'Unknown error',
            rawData: JSON.stringify(errorData)
          }
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
  };

  const getResultClass = () => {
    if (!result) return '';
    if (result.blocked) return 'result-danger';
    if (result.image_blocked) return 'result-warning';
    switch (result.result.prediction) {
      case 'Non-Abusive': return 'result-safe';
      case 'Abusive': return 'result-danger';
      case 'Intermediate': return 'result-warning';
      case 'Error': return 'result-error';
      default: return '';
    }
  };

  const canPost = () => {
    if (blocked) return false;
    if (!selectedImage) return false;
    if (loading) return false;
    return true;
  };

  const getButtonText = () => {
    if (blocked) return 'Account Blocked';
    if (loading) return 'Analyzing Image...';
    if (warningCount > 0) return `Post Image (Warning: ${warningCount}/3)`;
    return 'Post Image';
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
        <h2>Image Comment Analysis</h2>
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
            <div className="upload-area"
                 onDrop={handleDrop}
                 onDragOver={handleDragOver}
                 onClick={() => fileInputRef.current?.click()}>
              {preview ? (
                <div className="image-preview-container">
                  <img src={preview} alt="Preview" className="image-preview" />
                  <button 
                    type="button"
                    className="remove-image"
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedImage(null);
                      setPreview(null);
                    }}
                  >
                    ×
                  </button>
                </div>
              ) : (
                <div className="upload-placeholder">
                  <div className="upload-icon">📷</div>
                  <p>Click to upload or drag and drop</p>
                  <p className="upload-hint">PNG, JPG, GIF up to 10MB</p>
                </div>
              )}
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleImageSelect}
                style={{ display: 'none' }}
              />
            </div>

            {result?.abusive_blocked && (
              <div className="blocked-notice">
                <span className="blocked-icon">🚫</span>
                <span>{result.warning_message}</span>
              </div>
            )}

            {result?.warning && !result.blocked && !result.abusive_blocked && (
              <div className="warning-notice">
                <span className="warning-icon">⚠️</span>
                <span>{result.warning_message}</span>
              </div>
            )}

            <button 
              type="submit" 
              className="btn-primary btn-large"
              disabled={!canPost()}
            >
              {loading ? (
                <>
                  <span className="spinner"></span>
                  Analyzing Image...
                </>
              ) : getButtonText()}
            </button>
          </form>

          {result && !result.blocked && !result.image_blocked && (
            <div className={`prediction-result ${getResultClass()}`}>
              <h3>Prediction Result</h3>
              <div className="result-main">
                <div className="result-prediction">
                  {result.result.prediction}
                </div>
                {result.result.error && (
                  <div className="result-error-msg">{result.result.error}</div>
                )}
                {result.result.rawData && (
                  <div className="result-error-msg" style={{fontSize: '0.7rem', wordBreak: 'break-all'}}>
                    Raw: {result.result.rawData}
                  </div>
                )}
                {result.result.model_used && (
                  <div className="result-model">Model: {result.result.model_used}</div>
                )}
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
                      style={{ width: `${result.result.probabilities?.abusive || 0}%` }}
                    />
                  </div>
                  <div className="probability-value">{result.result.probabilities?.abusive || 0}%</div>
                </div>
                <div className="probability-bar">
                  <div className="probability-label">Non-Abusive</div>
                  <div className="probability-track">
                    <div 
                      className="probability-fill safe"
                      style={{ width: `${result.result.probabilities?.non_abusive || 0}%` }}
                    />
                  </div>
                  <div className="probability-value">{result.result.probabilities?.non_abusive || 0}%</div>
                </div>
                <div className="probability-bar">
                  <div className="probability-label">Intermediate</div>
                  <div className="probability-track">
                    <div 
                      className="probability-fill warning"
                      style={{ width: `${result.result.probabilities?.intermediate || 0}%` }}
                    />
                  </div>
                  <div className="probability-value">{result.result.probabilities?.intermediate || 0}%</div>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="history-section">
          <h3>Recent Image Comments</h3>
          {history.length === 0 ? (
            <p className="no-history">No image comments yet</p>
          ) : (
            <div className="history-list">
              {history.map(comment => (
                <div key={comment.id} className="history-item image-history">
                  {comment.image_path && (
                    <img 
                      src={`http://localhost:5000/uploads/${comment.image_path}`}
                      alt="Comment"
                      className="history-image"
                      onError={(e) => e.target.style.display = 'none'}
                    />
                  )}
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

export default ImageComment;
