import React from 'react';
import { Link, useLocation } from 'react-router-dom';

function Navbar({ user, onLogout }) {
  const location = useLocation();
  
  const isActive = (path) => location.pathname === path ? 'active' : '';

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <div className="logo">🛡️</div>
        <h1>AI Comment Control</h1>
      </div>
      <div className="navbar-menu">
        {user && (
          <>
            <Link to="/dashboard" className={`nav-link ${isActive('/dashboard')}`}>Dashboard</Link>
            <Link to="/text-comment" className={`nav-link ${isActive('/text-comment')}`}>Text Analysis</Link>
            <Link to="/image-comment" className={`nav-link ${isActive('/image-comment')}`}>Image Analysis</Link>
            {user.is_admin && (
              <Link to="/admin" className={`nav-link ${isActive('/admin')}`}>⚙️ Admin</Link>
            )}
            <div className="nav-user">
              <div className="user-info">
                <div className="user-avatar-nav">
                  {user.username.charAt(0).toUpperCase()}
                </div>
                <span className="user-name">{user.username}</span>
              </div>
              <button onClick={onLogout} className="btn-logout">
                🚪 Logout
              </button>
            </div>
          </>
        )}
      </div>
    </nav>
  );
}

export default Navbar;
