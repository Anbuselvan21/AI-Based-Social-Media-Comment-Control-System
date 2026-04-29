import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';

function AdminLogin({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [focusedField, setFocusedField] = useState(null);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await axios.post('http://localhost:5000/api/auth/admin/login', {
        username,
        password
      });

      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      
      if (onLogin) onLogin(response.data.access_token, response.data.user);
      
      window.location.href = '/admin';
    } catch (err) {
      setError(err.response?.data?.error || 'Invalid admin credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="admin-login-page">
      <div className="particles">
        {[...Array(20)].map((_, i) => (
          <div key={i} className="particle" style={{
            '--x': `${Math.random() * 100}%`,
            '--y': `${Math.random() * 100}%`,
            '--duration': `${20 + Math.random() * 20}s`,
            '--delay': `${Math.random() * 5}s`,
            '--size': `${5 + Math.random() * 10}px`
          }}></div>
        ))}
      </div>

      <div className="login-container">
        <div className="login-card">
          <div className="card-glow"></div>
          
          <div className="card-header">
            <div className="shield-container">
              <div className="shield">
                <div className="shield-inner">
                  <span className="shield-icon">🛡️</span>
                </div>
                <div className="shield-ring"></div>
                <div className="shield-ring ring-2"></div>
              </div>
            </div>
            <h1 className="title">Admin Access</h1>
          </div>

          {error && (
            <div className="error-banner">
              <div className="error-icon">⚠️</div>
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="login-form">
            <div className={`input-group ${focusedField === 'username' ? 'focused' : ''}`}>
              <div className="input-icon-wrapper">
                <span className="field-icon">👤</span>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  onFocus={() => setFocusedField('username')}
                  onBlur={() => setFocusedField(null)}
                  placeholder="Enter admin username"
                  required
                />
                <div className="input-highlight"></div>
              </div>
            </div>

            <div className={`input-group ${focusedField === 'password' ? 'focused' : ''}`}>
              <div className="input-icon-wrapper">
                <span className="field-icon">🔒</span>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onFocus={() => setFocusedField('password')}
                  onBlur={() => setFocusedField(null)}
                  placeholder="Enter password"
                  required
                />
                <div className="input-highlight"></div>
                <button 
                  type="button" 
                  className="password-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? '🙈' : '👁️'}
                </button>
              </div>
            </div>

            <button type="submit" className="login-btn" disabled={loading}>
              {loading ? (
                <>
                  <span className="btn-spinner"></span>
                  <span>Authenticating...</span>
                </>
              ) : (
                <>
                  <span className="btn-icon">🚀</span>
                  <span>Access Control Center</span>
                  <div className="btn-glow"></div>
                </>
              )}
            </button>
          </form>

          <div className="footer-links">
            <Link to="/login" className="footer-link">
              <span>👤</span> User Login
            </Link>
            <span className="footer-divider">|</span>
            <Link to="/register" className="footer-link">
              <span>📝</span> Register
            </Link>
          </div>
        </div>

        <div className="features-panel">
          <div className="feature-item">
            <div className="feature-icon">📊</div>
            <div className="feature-content">
              <h3>Dashboard Analytics</h3>
              <p>Monitor platform activity and content trends</p>
            </div>
          </div>

          <div className="feature-item">
            <div className="feature-icon">👥</div>
            <div className="feature-content">
              <h3>User Management</h3>
              <p>Block, unblock, or manage user accounts</p>
            </div>
          </div>

          <div className="feature-item">
            <div className="feature-icon">💬</div>
            <div className="feature-content">
              <h3>Content Moderation</h3>
              <p>Review and moderate comments system-wide</p>
            </div>
          </div>

          <div className="feature-item">
            <div className="feature-icon">📋</div>
            <div className="feature-content">
              <h3>Activity Logs</h3>
              <p>Track all moderation actions and history</p>
            </div>
          </div>

          <div className="admin-badge">
            <span className="badge-icon">🛡️</span>
            <span>Admin Privileges Required</span>
          </div>
        </div>
      </div>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');

        .admin-login-page {
          min-height: 100vh;
          background: linear-gradient(135deg, #ffffff 0%, #f3f4f6 100%);
          display: flex;
          justify-content: center;
          align-items: center;
          padding: 2rem;
          position: relative;
          overflow: hidden;
          font-family: 'Poppins', sans-serif;
        }

        .particles {
          position: absolute;
          width: 100%;
          height: 100%;
          overflow: hidden;
          z-index: 0;
        }

        .particle {
          position: absolute;
          left: var(--x);
          top: var(--y);
          width: var(--size);
          height: var(--size);
          background: radial-gradient(circle, rgba(249, 115, 22, 0.1) 0%, transparent 70%);
          border-radius: 50%;
          animation: float-particle var(--duration) var(--delay) infinite ease-in-out;
        }

        @keyframes float-particle {
          0%, 100% { transform: translate(0, 0) scale(1); opacity: 0.3; }
          50% { transform: translate(50px, -50px) scale(1.5); opacity: 0.5; }
        }

        .login-container {
          display: flex;
          gap: 4rem;
          align-items: center;
          max-width: 1100px;
          width: 100%;
          position: relative;
          z-index: 1;
        }

        .login-card {
          flex: 1;
          max-width: 450px;
          background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
          border-radius: 28px;
          padding: 3rem;
          border: 1px solid #e5e7eb;
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
          position: relative;
          overflow: hidden;
          animation: slideUp 0.8s ease;
        }

        @keyframes slideUp {
          from { opacity: 0; transform: translateY(50px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .card-glow {
          position: absolute;
          top: -50%;
          left: -50%;
          width: 200%;
          height: 200%;
          background: radial-gradient(circle at center, rgba(249, 115, 22, 0.05) 0%, transparent 50%);
          animation: rotate-glow 20s linear infinite;
        }

        @keyframes rotate-glow {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        .card-header {
          text-align: center;
          margin-bottom: 2rem;
          position: relative;
          z-index: 1;
        }

        .shield-container {
          display: flex;
          justify-content: center;
          margin-bottom: 1.5rem;
        }

        .shield {
          position: relative;
          width: 100px;
          height: 100px;
        }

        .shield-inner {
          width: 100px;
          height: 100px;
          background: linear-gradient(135deg, #f97316 0%, #fb923c 50%, #fbbf24 100%);
          border-radius: 24px;
          display: flex;
          align-items: center;
          justify-content: center;
          position: relative;
          z-index: 2;
          box-shadow: 0 10px 25px rgba(249, 115, 22, 0.25);
        }

        .shield-icon {
          font-size: 3rem;
        }

        .shield-ring {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: 130px;
          height: 130px;
          border: 2px solid rgba(249, 115, 22, 0.2);
          border-radius: 30px;
          animation: pulse-ring 2s infinite;
        }

        .shield-ring.ring-2 {
          width: 160px;
          height: 160px;
          border-color: rgba(249, 115, 22, 0.1);
          animation-delay: 0.5s;
        }

        @keyframes pulse-ring {
          0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 1; }
          50% { transform: translate(-50%, -50%) scale(1.1); opacity: 0.5; }
        }

        .title {
          font-size: 1.75rem;
          font-weight: 700;
          color: #111827;
          margin-bottom: 0.5rem;
        }

        .subtitle {
          color: #6b7280;
          font-size: 0.95rem;
        }

        .error-banner {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 1rem 1.25rem;
          background: #fef2f2;
          border: 1px solid #fecaca;
          border-radius: 14px;
          margin-bottom: 1.5rem;
          animation: shake 0.5s ease;
        }

        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-5px); }
          75% { transform: translateX(5px); }
        }

        .error-icon {
          font-size: 1.25rem;
        }

        .error-banner span {
          color: #b91c1c;
          font-size: 0.9rem;
        }

        .login-form {
          display: flex;
          flex-direction: column;
          gap: 1.25rem;
          position: relative;
          z-index: 1;
        }

        .input-group {
          position: relative;
        }

        .input-icon-wrapper {
          position: relative;
          display: flex;
          align-items: center;
        }

        .field-icon {
          position: absolute;
          left: 16px;
          font-size: 1.2rem;
          z-index: 2;
          transition: transform 0.3s ease;
        }

        .input-group.focused .field-icon {
          transform: scale(1.2);
        }

        .input-icon-wrapper input {
          width: 100%;
          padding: 1rem 1rem 1rem 3.5rem;
          background: #ffffff;
          border: 1px solid #e5e7eb;
          border-radius: 14px;
          font-size: 1rem;
          color: #111827;
          transition: all 0.3s ease;
        }

        .input-icon-wrapper input:focus {
          outline: none;
          border-color: #f97316;
          box-shadow: 0 0 0 4px rgba(249, 115, 22, 0.1);
        }

        .input-icon-wrapper input::placeholder {
          color: #9ca3af;
        }

        .input-highlight {
          position: absolute;
          bottom: 0;
          left: 50%;
          width: 0;
          height: 2px;
          background: linear-gradient(90deg, #f97316, #fb923c);
          transition: all 0.3s ease;
          transform: translateX(-50%);
          border-radius: 2px;
        }

        .input-group.focused .input-highlight {
          width: calc(100% - 3.5rem);
        }

        .password-toggle {
          position: absolute;
          right: 12px;
          background: none;
          border: none;
          cursor: pointer;
          font-size: 1.3rem;
          padding: 5px;
          transition: transform 0.2s;
        }

        .password-toggle:hover {
          transform: scale(1.1);
        }

        .login-btn {
          position: relative;
          padding: 1.1rem 2rem;
          background: linear-gradient(135deg, #f97316 0%, #fb923c 100%);
          border: none;
          border-radius: 14px;
          font-size: 1.1rem;
          font-weight: 700;
          color: white;
          cursor: pointer;
          overflow: hidden;
          transition: all 0.3s ease;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.75rem;
          margin-top: 0.5rem;
          text-transform: uppercase;
          letter-spacing: 1px;
          box-shadow: 0 4px 15px rgba(249, 115, 22, 0.25);
        }

        .login-btn:hover:not(:disabled) {
          transform: translateY(-3px) scale(1.02);
          box-shadow: 0 15px 35px rgba(249, 115, 22, 0.35);
        }

        .login-btn:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }

        .btn-icon {
          font-size: 1.3rem;
        }

        .btn-glow {
          position: absolute;
          top: 0;
          left: -100%;
          width: 100%;
          height: 100%;
          background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
          animation: btnShine 2.5s infinite;
        }

        @keyframes btnShine {
          0% { left: -100%; }
          50%, 100% { left: 100%; }
        }

        .btn-spinner {
          width: 20px;
          height: 20px;
          border: 3px solid rgba(255,255,255,0.3);
          border-top-color: white;
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .footer-links {
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 1rem;
          margin-top: 1.5rem;
          padding-top: 1.5rem;
          border-top: 1px solid #e5e7eb;
          position: relative;
          z-index: 1;
        }

        .footer-link {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          color: #6b7280;
          text-decoration: none;
          font-size: 0.9rem;
          transition: color 0.3s;
        }

        .footer-link:hover {
          color: #f97316;
        }

        .footer-divider {
          color: #d1d5db;
        }

        .features-panel {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
          animation: fadeInRight 0.8s ease 0.3s both;
        }

        @keyframes fadeInRight {
          from { opacity: 0; transform: translateX(50px); }
          to { opacity: 1; transform: translateX(0); }
        }

        .feature-item {
          display: flex;
          align-items: center;
          gap: 1.25rem;
          background: #ffffff;
          border: 1px solid #e5e7eb;
          border-radius: 16px;
          padding: 1.25rem;
          transition: all 0.3s ease;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }

        .feature-item:hover {
          transform: translateX(10px);
          border-color: #f97316;
          box-shadow: 0 4px 15px rgba(249, 115, 22, 0.1);
        }

        .feature-icon {
          font-size: 2.5rem;
          flex-shrink: 0;
        }

        .feature-content h3 {
          color: #111827;
          font-size: 1.05rem;
          font-weight: 600;
          margin-bottom: 0.25rem;
        }

        .feature-content p {
          color: #6b7280;
          font-size: 0.85rem;
        }

        .admin-badge {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.75rem;
          padding: 1rem;
          background: #fee2e2;
          border: 1px solid #fca5a5;
          border-radius: 12px;
          margin-top: 1rem;
        }

        .badge-icon {
          font-size: 1.25rem;
        }

        .admin-badge span:last-child {
          color: #b91c1c;
          font-weight: 600;
          font-size: 0.9rem;
        }

        @media (max-width: 900px) {
          .login-container {
            flex-direction: column;
            gap: 2rem;
          }

          .features-panel {
            width: 100%;
          }
        }
      `}</style>
    </div>
  );
}

export default AdminLogin;
