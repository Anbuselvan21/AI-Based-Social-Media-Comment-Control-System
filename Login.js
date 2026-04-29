import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';

function Login({ onLogin }) {
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
      const response = await axios.post('http://localhost:5000/api/auth/login', {
        username,
        password
      });

      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      
      if (onLogin) onLogin(response.data.access_token, response.data.user);
      
      window.location.href = '/dashboard';
    } catch (err) {
      setError(err.response?.data?.error || 'Invalid username or password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="beautiful-login-page">
      <div className="floating-shapes">
        <div className="shape shape-1"></div>
        <div className="shape shape-2"></div>
        <div className="shape shape-3"></div>
        <div className="shape shape-4"></div>
        <div className="shape shape-5"></div>
      </div>

      <div className="login-container">
        <div className="login-card">
          <div className="card-header">
            <div className="logo-container">
              <div className="logo-icon">
                <div className="logo-inner">
                  <span className="logo-text">AI</span>
                </div>
                <div className="logo-glow"></div>
              </div>
            </div>
            <h1 className="title"><span className="gradient-text">Welcome to AI Comment Control System</span></h1>
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
                  placeholder="Enter your username"
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
                  placeholder="Enter your password"
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
                  <span>Signing In...</span>
                </>
              ) : (
                <>
                  <span className="btn-icon">→</span>
                  <span>Sign In</span>
                  <div className="btn-glow"></div>
                </>
              )}
            </button>
          </form>

          <div className="card-footer">
            <div className="divider">
              <span className="divider-line"></span>
              <span className="divider-text">New to the platform?</span>
              <span className="divider-line"></span>
            </div>

            <Link to="/register" className="register-link">
              <span className="register-icon">✨</span>
              Create New Account
            </Link>
          </div>

          <div className="admin-access">
            <span className="admin-label">Admin access?</span>
            <a href="/admin-login" target="_blank" rel="noopener noreferrer" className="admin-link">
              <span className="admin-icon">🛡️</span>
              Admin Panel
            </a>
          </div>
        </div>

        <div className="info-section">
          <div className="info-card">
            <div className="info-icon">🔍</div>
            <h3>Text Analysis</h3>
            <p>Real-time detection of offensive language in text</p>
          </div>
          <div className="info-card">
            <div className="info-icon">🖼️</div>
            <h3>Image Analysis</h3>
            <p>OCR-powered meme content moderation</p>
          </div>
          <div className="info-card">
            <div className="info-icon">📊</div>
            <h3>Analytics</h3>
            <p>Comprehensive content safety dashboard</p>
          </div>
        </div>
      </div>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');

        .beautiful-login-page {
          min-height: 100vh;
          background: linear-gradient(135deg, #ffffff 0%, #f5f7fa 100%);
          display: flex;
          justify-content: center;
          align-items: center;
          padding: 2rem;
          position: relative;
          overflow: hidden;
          font-family: 'Poppins', sans-serif;
        }

        .floating-shapes {
          position: absolute;
          width: 100%;
          height: 100%;
          overflow: hidden;
          z-index: 0;
        }

        .shape {
          position: absolute;
          border-radius: 50%;
          animation: float 20s infinite ease-in-out;
        }

        .shape-1 {
          width: 300px;
          height: 300px;
          background: radial-gradient(circle, rgba(108, 99, 255, 0.1) 0%, transparent 70%);
          top: -100px;
          left: -100px;
          animation-delay: 0s;
        }

        .shape-2 {
          width: 400px;
          height: 400px;
          background: radial-gradient(circle, rgba(16, 185, 129, 0.08) 0%, transparent 70%);
          top: 50%;
          right: -150px;
          animation-delay: -5s;
        }

        .shape-3 {
          width: 250px;
          height: 250px;
          background: radial-gradient(circle, rgba(245, 158, 11, 0.08) 0%, transparent 70%);
          bottom: -80px;
          left: 20%;
          animation-delay: -10s;
        }

        .shape-4 {
          width: 200px;
          height: 200px;
          background: radial-gradient(circle, rgba(139, 92, 246, 0.08) 0%, transparent 70%);
          top: 30%;
          left: 10%;
          animation-delay: -15s;
        }

        .shape-5 {
          width: 350px;
          height: 350px;
          background: radial-gradient(circle, rgba(236, 72, 153, 0.05) 0%, transparent 70%);
          bottom: 20%;
          right: 10%;
          animation-delay: -8s;
        }

        @keyframes float {
          0%, 100% { transform: translate(0, 0) rotate(0deg); }
          25% { transform: translate(20px, -20px) rotate(5deg); }
          50% { transform: translate(0, 20px) rotate(0deg); }
          75% { transform: translate(-20px, -10px) rotate(-5deg); }
        }

        .login-container {
          display: flex;
          gap: 3rem;
          align-items: center;
          max-width: 1200px;
          width: 100%;
          position: relative;
          z-index: 1;
        }

        .login-card {
          flex: 1;
          max-width: 480px;
          background: #ffffff;
          border-radius: 24px;
          padding: 3rem;
          border: 1px solid #e2e8f0;
          box-shadow: 
            0 4px 6px -1px rgba(0, 0, 0, 0.1),
            0 2px 4px -1px rgba(0, 0, 0, 0.06),
            0 20px 25px -5px rgba(0, 0, 0, 0.05);
          animation: slideIn 0.8s ease;
        }

        @keyframes slideIn {
          from { opacity: 0; transform: translateY(30px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .card-header {
          text-align: center;
          margin-bottom: 2.5rem;
        }

        .logo-container {
          display: flex;
          justify-content: center;
          margin-bottom: 1.5rem;
        }

        .logo-icon {
          position: relative;
          width: 80px;
          height: 80px;
        }

        .logo-inner {
          width: 80px;
          height: 80px;
          background: linear-gradient(135deg, #6c63ff 0%, #9333ea 100%);
          border-radius: 20px;
          display: flex;
          align-items: center;
          justify-content: center;
          position: relative;
          z-index: 2;
          animation: pulse 3s infinite;
          box-shadow: 0 10px 25px rgba(108, 99, 255, 0.3);
        }

        @keyframes pulse {
          0%, 100% { box-shadow: 0 10px 25px rgba(108, 99, 255, 0.3); }
          50% { box-shadow: 0 10px 35px rgba(108, 99, 255, 0.5); }
        }

        .logo-text {
          font-size: 1.5rem;
          font-weight: 800;
          color: white;
        }

        .logo-glow {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: 120px;
          height: 120px;
          background: radial-gradient(circle, rgba(108, 99, 255, 0.2) 0%, transparent 70%);
          animation: glow 2s infinite;
        }

        @keyframes glow {
          0%, 100% { opacity: 0.5; transform: translate(-50%, -50%) scale(1); }
          50% { opacity: 1; transform: translate(-50%, -50%) scale(1.2); }
        }

        .title {
          font-size: 1.75rem;
          font-weight: 700;
          color: #1e293b;
          margin-bottom: 0.5rem;
          line-height: 1.3;
          text-align: center;
        }

        .gradient-text {
          background: linear-gradient(135deg, #6c63ff 0%, #9333ea 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          font-weight: 700;
        }

        .error-banner {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 1rem 1.25rem;
          background: #fef2f2;
          border: 1px solid #fecaca;
          border-radius: 12px;
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
          color: #dc2626;
          font-size: 0.9rem;
        }

        .login-form {
          display: flex;
          flex-direction: column;
          gap: 1.25rem;
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
          background: #f8fafc;
          border: 2px solid #e2e8f0;
          border-radius: 14px;
          font-size: 1rem;
          color: #333;
          transition: all 0.3s ease;
        }

        .input-icon-wrapper input:focus {
          outline: none;
          border-color: #6c63ff;
          background: #ffffff;
          box-shadow: 0 0 0 4px rgba(108, 99, 255, 0.1);
        }

        .input-icon-wrapper input::placeholder {
          color: #888;
        }

        .input-highlight {
          position: absolute;
          bottom: 0;
          left: 50%;
          width: 0;
          height: 2px;
          background: linear-gradient(90deg, #6c63ff, #9333ea);
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
          padding: 1rem 2rem;
          background: linear-gradient(135deg, #6c63ff 0%, #9333ea 100%);
          border: none;
          border-radius: 14px;
          font-size: 1.1rem;
          font-weight: 600;
          color: white;
          cursor: pointer;
          overflow: hidden;
          transition: all 0.3s ease;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.75rem;
          margin-top: 0.5rem;
          box-shadow: 0 4px 15px rgba(108, 99, 255, 0.3);
        }

        .login-btn:hover:not(:disabled) {
          transform: translateY(-3px);
          box-shadow: 0 15px 35px rgba(108, 99, 255, 0.4);
        }

        .login-btn:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }

        .btn-icon {
          font-size: 1.3rem;
          transition: transform 0.3s;
        }

        .login-btn:hover .btn-icon {
          transform: translateX(5px);
        }

        .btn-glow {
          position: absolute;
          top: 0;
          left: -100%;
          width: 100%;
          height: 100%;
          background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
          animation: btnShine 3s infinite;
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

        .card-footer {
          margin-top: 2rem;
        }

        .divider {
          display: flex;
          align-items: center;
          gap: 1rem;
          margin-bottom: 1.5rem;
        }

        .divider-line {
          flex: 1;
          height: 1px;
          background: #e2e8f0;
        }

        .divider-text {
          color: #64748b;
          font-size: 0.85rem;
        }

        .register-link {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.75rem;
          padding: 1rem;
          background: #f0fdf4;
          border: 1px solid #bbf7d0;
          border-radius: 14px;
          color: #16a34a;
          text-decoration: none;
          font-weight: 500;
          transition: all 0.3s ease;
        }

        .register-link:hover {
          background: #dcfce7;
          transform: translateY(-2px);
        }

        .register-icon {
          font-size: 1.2rem;
        }

        .admin-access {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.75rem;
          margin-top: 1.5rem;
          padding-top: 1.5rem;
          border-top: 1px solid #e2e8f0;
        }

        .admin-label {
          color: #64748b;
          font-size: 0.9rem;
        }

        .admin-link {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          color: #d97706;
          text-decoration: none;
          font-weight: 500;
          transition: all 0.3s;
        }

        .admin-link:hover {
          color: #f59e0b;
          text-decoration: underline;
        }

        .info-section {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
          animation: fadeInRight 0.8s ease 0.3s both;
        }

        @keyframes fadeInRight {
          from { opacity: 0; transform: translateX(30px); }
          to { opacity: 1; transform: translateX(0); }
        }

        .info-card {
          background: #ffffff;
          border: 1px solid #e2e8f0;
          border-radius: 16px;
          padding: 1.5rem;
          transition: all 0.3s ease;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }

        .info-card:hover {
          transform: translateX(10px);
          border-color: #6c63ff;
          box-shadow: 0 4px 15px rgba(108, 99, 255, 0.1);
        }

        .info-icon {
          font-size: 2rem;
          margin-bottom: 0.75rem;
        }

        .info-card h3 {
          color: #1e293b;
          font-size: 1.1rem;
          font-weight: 600;
          margin-bottom: 0.5rem;
        }

        .info-card p {
          color: #64748b;
          font-size: 0.9rem;
        }

        @media (max-width: 900px) {
          .login-container {
            flex-direction: column;
          }

          .info-section {
            flex-direction: row;
            flex-wrap: wrap;
            justify-content: center;
          }

          .info-card {
            flex: 1;
            min-width: 200px;
          }
        }
      `}</style>
    </div>
  );
}

export default Login;
