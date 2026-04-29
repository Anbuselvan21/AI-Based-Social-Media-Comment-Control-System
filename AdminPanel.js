import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, AreaChart, Area } from 'recharts';

function AdminPanel() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [stats, setStats] = useState(null);
  const [comments, setComments] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedUsers, setSelectedUsers] = useState({});
  const [moderationLog, setModerationLog] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [showAlert, setShowAlert] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [userHistory, setUserHistory] = useState([]);
  const [userStats, setUserStats] = useState(null);
  const [showUserModal, setShowUserModal] = useState(false);
  
  const currentUser = JSON.parse(localStorage.getItem('user') || '{}');

  useEffect(() => {
    fetchDashboard();
    fetchModerationLog();
  }, []);

  useEffect(() => {
    if (activeTab === 'comments') {
      fetchComments();
    } else if (activeTab === 'users') {
      fetchUsers();
    }
  }, [activeTab, filter, typeFilter]);

  useEffect(() => {
    if (stats && stats.recent_comments) {
      const abusiveRecent = stats.recent_comments.filter(c => c.prediction === 'Abusive').length;
      if (abusiveRecent > 0) {
        setAlerts(prev => [...prev, {
          id: Date.now(),
          type: 'warning',
          message: `${abusiveRecent} new abusive comment(s) detected!`,
          time: new Date().toLocaleTimeString()
        }]);
        setShowAlert(true);
        setTimeout(() => setShowAlert(false), 5000);
      }
    }
  }, [stats]);

  const getAuthHeaders = () => ({
    headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
  });

  const fetchDashboard = async () => {
    setLoading(true);
    try {
      const response = await axios.get('http://localhost:5000/api/admin/dashboard', getAuthHeaders());
      setStats(response.data);
    } catch (err) {
      console.error('Failed to fetch dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchComments = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filter !== 'all') params.append('filter', filter);
      if (typeFilter !== 'all') params.append('type', typeFilter);
      
      const response = await axios.get(
        `http://localhost:5000/api/admin/comments?${params.toString()}`,
        getAuthHeaders()
      );
      setComments(response.data.comments);
    } catch (err) {
      console.error('Failed to fetch comments:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await axios.get('http://localhost:5000/api/admin/users', getAuthHeaders());
      setUsers(response.data);
    } catch (err) {
      console.error('Failed to fetch users:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchModerationLog = async () => {
    const log = JSON.parse(localStorage.getItem('moderationLog') || '[]');
    setModerationLog(log.slice(0, 20));
  };

  const fetchUserDetails = async (user) => {
    setSelectedUser(user);
    setShowUserModal(true);
    try {
      const response = await axios.get(`http://localhost:5000/api/admin/users/${user.id}`, getAuthHeaders());
      setUserHistory(response.data.recent_comments || []);
      setUserStats(response.data.stats || null);
    } catch (err) {
      console.error('Failed to fetch user details:', err);
    }
  };

  const addToModerationLog = (action, details) => {
    const newLog = [{
      id: Date.now(),
      action,
      details,
      admin: 'Admin',
      time: new Date().toLocaleString()
    }, ...moderationLog].slice(0, 50);
    localStorage.setItem('moderationLog', JSON.stringify(newLog));
    setModerationLog(newLog);
  };

  const handleDeleteComment = async (id, username, content) => {
    if (!window.confirm('Are you sure you want to delete this comment?')) return;
    
    try {
      await axios.delete(`http://localhost:5000/api/admin/comments/${id}`, getAuthHeaders());
      addToModerationLog('Deleted Comment', `User: ${username}, Content: ${content?.substring(0, 30)}...`);
      fetchComments();
      fetchDashboard();
    } catch (err) {
      console.error('Failed to delete comment:', err);
    }
  };

  const handleApproveComment = async (id) => {
    try {
      addToModerationLog('Approved Comment', `Comment ID: ${id}`);
      fetchComments();
    } catch (err) {
      console.error('Failed to approve comment:', err);
    }
  };

  const handleBlockUser = async (userId, username, isBlocked) => {
    try {
      await axios.post(`http://localhost:5000/api/admin/users/${userId}/block`, {}, getAuthHeaders());
      addToModerationLog(isBlocked ? 'Unblocked User' : 'Blocked User', `Username: ${username}`);
      fetchUsers();
      fetchDashboard();
    } catch (err) {
      console.error('Failed to block user:', err);
    }
  };

  const handleResetWarnings = async (userId, username) => {
    if (!window.confirm(`Reset all warnings for ${username}?`)) return;
    
    try {
      await axios.post(`http://localhost:5000/api/admin/users/${userId}/reset-warnings`, {}, getAuthHeaders());
      addToModerationLog('Reset Warnings', `Username: ${username}`);
      fetchUsers();
      fetchDashboard();
      setShowUserModal(false);
    } catch (err) {
      console.error('Failed to reset warnings:', err);
    }
  };

  const handleDeleteUser = async (userId, username) => {
    if (!window.confirm('Are you sure? This will also delete all their comments.')) return;
    
    try {
      await axios.delete(`http://localhost:5000/api/admin/users/${userId}/delete`, getAuthHeaders());
      addToModerationLog('Deleted User', `Username: ${username}`);
      fetchUsers();
      fetchDashboard();
    } catch (err) {
      console.error('Failed to delete user:', err);
    }
  };

  const fetchUserHistory = async (user) => {
    setSelectedUser(user);
    setShowUserModal(true);
    
    try {
      const allComments = await axios.get('http://localhost:5000/api/admin/comments', getAuthHeaders());
      const userComments = allComments.data.comments.filter(c => c.user_id === user.id);
      setUserHistory(userComments);
      
      const abusive = userComments.filter(c => c.prediction === 'Abusive').length;
      const nonAbusive = userComments.filter(c => c.prediction === 'Non-Abusive').length;
      const intermediate = userComments.filter(c => c.prediction === 'Intermediate').length;
      
      setUserStats({
        total: userComments.length,
        abusive,
        nonAbusive,
        intermediate,
        textComments: userComments.filter(c => c.type === 'text').length,
        imageComments: userComments.filter(c => c.type === 'image').length,
        abuseRate: userComments.length > 0 ? Math.round((abusive / userComments.length) * 100) : 0
      });
    } catch (err) {
      console.error('Failed to fetch user history:', err);
    }
  };

  const handleBulkAction = async (action) => {
    const selectedIds = Object.keys(selectedUsers).filter(id => selectedUsers[id]);
    
    if (selectedIds.length === 0) {
      alert('Please select items first');
      return;
    }

    if (action === 'delete') {
      if (!window.confirm(`Delete ${selectedIds.length} selected item(s)?`)) return;
      for (const id of selectedIds) {
        await handleDeleteComment(id, 'Selected User', '');
      }
    }
    
    setSelectedUsers({});
  };

  const toggleSelect = (id) => {
    setSelectedUsers(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const exportCSV = async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/admin/export/csv', getAuthHeaders());
      const blob = new Blob([response.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `comments_export_${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
      addToModerationLog('Exported Report', 'CSV Export');
    } catch (err) {
      console.error('Failed to export CSV:', err);
    }
  };

  const pieData = stats ? [
    { name: 'Safe', value: stats.stats.non_abusive, color: '#22c55e' },
    { name: 'Warning', value: stats.stats.intermediate, color: '#f97316' }
  ] : [];

  const imageData = stats ? [
    { name: 'Safe', value: stats.stats.image_safe || 0, color: '#22c55e' },
    { name: 'Warning', value: stats.stats.image_warning || 0, color: '#f97316' }
  ] : [];

  const textData = stats ? [
    { name: 'Safe', value: stats.stats.text_safe || 0, color: '#22c55e' },
    { name: 'Warning', value: stats.stats.text_warning || 0, color: '#f97316' }
  ] : [];

  const filteredComments = comments.filter(comment => 
    comment.username?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    comment.content?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredUsers = users.filter(user =>
    user.username?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="admin-panel">
      {showAlert && alerts.length > 0 && (
        <div className="admin-alert">
          <span className="alert-icon">⚠️</span>
          <span className="alert-message">{alerts[alerts.length - 1]?.message}</span>
          <button onClick={() => setShowAlert(false)} className="alert-close">×</button>
        </div>
      )}

      <div className="admin-header">
        <div className="admin-title">
          <h2>🛡️ Admin Control Center</h2>
          <p>Manage users, monitor content, and maintain community guidelines</p>
        </div>
        <div className="admin-info">
          <span className="admin-user">👤 Logged in as: <strong>{currentUser.username || 'Admin'}</strong></span>
          <span className="admin-email">{currentUser.email}</span>
        </div>
        <div className="admin-actions">
          <button onClick={exportCSV} className="btn-export">
            📊 Export Report
          </button>
          <button onClick={() => { localStorage.clear(); window.location.href = '/admin-login'; }} className="btn-logout">
            🚪 Logout
          </button>
        </div>
      </div>

      <div className="admin-tabs">
        <button className={`tab-button ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={() => setActiveTab('dashboard')}>
          📈 Dashboard
        </button>
        <button className={`tab-button ${activeTab === 'comments' ? 'active' : ''}`} onClick={() => setActiveTab('comments')}>
          💬 Comments ({comments.length})
        </button>
        <button className={`tab-button ${activeTab === 'users' ? 'active' : ''}`} onClick={() => setActiveTab('users')}>
          👥 Users ({users.length})
        </button>
        <button className={`tab-button ${activeTab === 'logs' ? 'active' : ''}`} onClick={() => setActiveTab('logs')}>
          📋 Activity Logs
        </button>
        <button className={`tab-button ${activeTab === 'analytics' ? 'active' : ''}`} onClick={() => setActiveTab('analytics')}>
          📊 Analytics
        </button>
      </div>

      {activeTab === 'dashboard' && stats && (
        <div className="dashboard-content">
          <div className="stats-cards">
            <div className="stat-card-admin total">
              <div className="stat-icon">💬</div>
              <div className="stat-info">
                <div className="stat-value">{stats.stats.total_comments}</div>
                <div className="stat-label">Total Comments</div>
                <div className="stat-change positive">Safe posts only</div>
              </div>
            </div>
            <div className="stat-card-admin users">
              <div className="stat-icon">👥</div>
              <div className="stat-info">
                <div className="stat-value">{stats.stats.total_users}</div>
                <div className="stat-label">Total Users</div>
                <div className="stat-change positive">Registered users</div>
              </div>
            </div>
            <div className="stat-card-admin safe">
              <div className="stat-icon">✅</div>
              <div className="stat-info">
                <div className="stat-value safe">{stats.stats.non_abusive}</div>
                <div className="stat-label">Safe Comments</div>
                <div className="stat-change positive">100% safe</div>
              </div>
            </div>
            <div className="stat-card-admin blocked">
              <div className="stat-icon">🔒</div>
              <div className="stat-info">
                <div className="stat-value">{stats.stats.blocked_users}</div>
                <div className="stat-label">Blocked Users</div>
                <div className="stat-change neutral">Due to warnings</div>
              </div>
            </div>
          </div>

          <div className="dashboard-grid">
            <div className="chart-container">
              <h3>🖼️ Image Comments Distribution</h3>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie 
                    data={imageData} 
                    cx="50%" 
                    cy="50%" 
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {imageData.map((entry, index) => (
                      <Cell key={`image-cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              <div className="chart-legend">
                {imageData.map((item, index) => (
                  <div key={index} className="legend-item">
                    <span className="legend-color" style={{ backgroundColor: item.color }}></span>
                    <span>{item.name}: {item.value}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="chart-container">
              <h3>💬 Text Comments Distribution</h3>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie 
                    data={textData} 
                    cx="50%" 
                    cy="50%" 
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {textData.map((entry, index) => (
                      <Cell key={`text-cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              <div className="chart-legend">
                {textData.map((item, index) => (
                  <div key={index} className="legend-item">
                    <span className="legend-color" style={{ backgroundColor: item.color }}></span>
                    <span>{item.name}: {item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="recent-activity">
            <h3>🔔 Recent Comments Requiring Attention</h3>
            <div className="activity-list">
              {stats.recent_comments.slice(0, 5).map(comment => (
                <div key={comment.id} className={`activity-item ${comment.prediction === 'Abusive' ? 'abusive' : comment.prediction === 'Intermediate' ? 'intermediate' : 'safe'}`}>
                  <div className="activity-user">
                    <span className="user-avatar">{comment.username?.[0]?.toUpperCase()}</span>
                    <span className="user-name">{comment.username}</span>
                  </div>
                  <div className="activity-content">
                    {comment.content || <em>Image Comment</em>}
                  </div>
                  <div className={`activity-status ${comment.prediction?.toLowerCase().replace('-', '')}`}>
                    {comment.prediction}
                  </div>
                  <div className="activity-actions">
                    <button onClick={() => handleDeleteComment(comment.id, comment.username, comment.content)} className="btn-action-small delete">Delete</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'comments' && (
        <div className="comments-content">
          <div className="filters-bar">
            <div className="search-box">
              <input type="text" placeholder="🔍 Search comments or users..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} />
            </div>
            <div className="filter-group">
              <label>Prediction:</label>
              <select value={filter} onChange={(e) => setFilter(e.target.value)}>
                <option value="all">All</option>
                <option value="Non-Abusive">✅ Non-Abusive</option>
                <option value="Intermediate">⚠️ Intermediate</option>
              </select>
            </div>
            <div className="filter-group">
              <label>Type:</label>
              <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
                <option value="all">All</option>
                <option value="text">💬 Text</option>
                <option value="image">🖼️ Image</option>
              </select>
            </div>
            <div className="bulk-actions">
              <button onClick={() => handleBulkAction('delete')} className="btn-bulk">🗑️ Bulk Delete</button>
            </div>
          </div>

          <div className="comments-table">
            <table>
              <thead>
                <tr>
                  <th><input type="checkbox" onChange={(e) => {
                    const allIds = filteredComments.map(c => c.id);
                    setSelectedUsers(allIds.reduce((acc, id) => ({ ...acc, [id]: e.target.checked }), {}));
                  }} /></th>
                  <th>User</th>
                  <th>Type</th>
                  <th>Content</th>
                  <th>Prediction</th>
                  <th>Confidence</th>
                  <th>Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredComments.map(comment => (
                  <tr key={comment.id} className={comment.prediction === 'Abusive' ? 'row-abusive' : ''}>
                    <td><input type="checkbox" checked={selectedUsers[comment.id] || false} onChange={() => toggleSelect(comment.id)} /></td>
                    <td><span className="user-badge">{comment.username?.[0]?.toUpperCase()}</span> {comment.username}</td>
                    <td><span className={`type-badge ${comment.type}`}>{comment.type === 'text' ? '💬' : '🖼️'}</span></td>
                    <td className="content-cell">{comment.content || <em>Image</em>}</td>
                    <td>
                      <span className={`prediction-badge ${comment.prediction === 'Non-Abusive' ? 'safe' : comment.prediction === 'Abusive' ? 'danger' : 'warning'}`}>
                        {comment.prediction === 'Abusive' ? '🚫' : comment.prediction === 'Intermediate' ? '⚠️' : '✅'} {comment.prediction}
                      </span>
                    </td>
                    <td><div className="confidence-bar"><div className="confidence-fill" style={{ width: `${comment.confidence}%` }}></div></div> {comment.confidence}%</td>
                    <td>{new Date(comment.created_at).toLocaleString()}</td>
                    <td>
                      <button onClick={() => handleApproveComment(comment.id)} className="btn-action-small approve">✓</button>
                      <button onClick={() => handleDeleteComment(comment.id, comment.username, comment.content)} className="btn-action-small delete">🗑️</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filteredComments.length === 0 && <div className="no-data">No comments found</div>}
          </div>
        </div>
      )}

      {activeTab === 'users' && (
        <div className="users-content">
          <div className="filters-bar">
            <div className="search-box">
              <input type="text" placeholder="🔍 Search users..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} />
            </div>
          </div>

          <div className="users-grid">
            {filteredUsers.map(user => (
              <div key={user.id} className={`user-card ${user.is_blocked ? 'blocked' : ''}`} onClick={() => fetchUserDetails(user)}>
                <div className="user-card-header">
                  <div className="user-avatar-large">{user.username?.[0]?.toUpperCase()}</div>
                  <div className="user-info">
                    <h4>{user.username}</h4>
                    <p>{user.email}</p>
                    <span className={`status-badge ${user.is_blocked ? 'blocked' : 'active'}`}>
                      {user.is_blocked ? '🔒 Blocked' : '✅ Active'}
                    </span>
                  </div>
                </div>
                <div className="user-stats">
                  <div className="user-stat">
                    <span className="stat-number">{user.comment_count}</span>
                    <span className="stat-text">Comments</span>
                  </div>
                  <div className="user-stat">
                    <span className="stat-number warning">{user.warning_count || 0}</span>
                    <span className="stat-text">Warnings</span>
                  </div>
                  <div className="user-stat">
                    <span className="stat-number">{new Date(user.created_at).toLocaleDateString()}</span>
                    <span className="stat-text">Joined</span>
                  </div>
                </div>
                <div className="user-actions" onClick={(e) => e.stopPropagation()}>
                  <button onClick={() => handleBlockUser(user.id, user.username, user.is_blocked)} className={`btn-user ${user.is_blocked ? 'unblock' : 'block'}`}>
                    {user.is_blocked ? '🔓 Unblock' : '🔒 Block'}
                  </button>
                  <button onClick={() => handleDeleteUser(user.id, user.username)} className="btn-user delete">🗑️ Delete</button>
                </div>
              </div>
            ))}
          </div>
          {filteredUsers.length === 0 && <div className="no-data">No users found</div>}
        </div>
      )}

      {activeTab === 'logs' && (
        <div className="logs-container">
          <div className="logs-header-modern">
            <div className="logs-title-section">
              <h3>📋 Moderation Activity Log</h3>
              <p>Track all admin actions and system events</p>
            </div>
            <div className="logs-actions">
              <button onClick={() => { localStorage.removeItem('moderationLog'); setModerationLog([]); }} className="btn-clear-logs-modern">
                🗑️ Clear All
              </button>
            </div>
          </div>

          {moderationLog.length === 0 ? (
            <div className="empty-logs">
              <div className="empty-logs-icon">📭</div>
              <h4>No Activity Yet</h4>
              <p>Moderation actions will appear here</p>
            </div>
          ) : (
            <>
              <div className="logs-stats-bar">
                <div className="log-stat">
                  <span className="log-stat-icon">📝</span>
                  <span className="log-stat-value">{moderationLog.length}</span>
                  <span className="log-stat-label">Total Actions</span>
                </div>
                <div className="log-stat success">
                  <span className="log-stat-icon">✅</span>
                  <span className="log-stat-value">{moderationLog.filter(l => l.action.includes('Unblock') || l.action.includes('Approve') || l.action.includes('Export')).length}</span>
                  <span className="log-stat-label">Positive Actions</span>
                </div>
                <div className="log-stat warning">
                  <span className="log-stat-icon">⚠️</span>
                  <span className="log-stat-value">{moderationLog.filter(l => l.action.includes('Block') || l.action.includes('Reset')).length}</span>
                  <span className="log-stat-label">Moderations</span>
                </div>
                <div className="log-stat danger">
                  <span className="log-stat-icon">🗑️</span>
                  <span className="log-stat-value">{moderationLog.filter(l => l.action.includes('Delete')).length}</span>
                  <span className="log-stat-label">Deletions</span>
                </div>
              </div>

              <div className="logs-timeline">
                {moderationLog.map((log, index) => {
                  const isDelete = log.action.includes('Delete');
                  const isBlock = log.action.includes('Block') || log.action.includes('Reset');
                  const isPositive = log.action.includes('Unblock') || log.action.includes('Approve') || log.action.includes('Export');
                  
                  return (
                    <div key={log.id} className={`log-timeline-item ${isDelete ? 'delete' : isBlock ? 'block' : isPositive ? 'positive' : ''}`}>
                      <div className="log-timeline-marker">
                        <div className="log-timeline-dot"></div>
                        {index < moderationLog.length - 1 && <div className="log-timeline-line"></div>}
                      </div>
                      <div className="log-timeline-content">
                        <div className="log-timeline-header">
                          <span className={`log-action-badge ${isDelete ? 'delete' : isBlock ? 'block' : isPositive ? 'positive' : ''}`}>
                            {isDelete ? '🗑️' : isBlock ? '⚠️' : isPositive ? '✅' : '📝'} {log.action}
                          </span>
                          <span className="log-time">{log.time}</span>
                        </div>
                        <div className="log-details">{log.details}</div>
                        <div className="log-admin-badge">👤 {log.admin}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </div>
      )}

      {activeTab === 'analytics' && stats && (
        <div className="analytics-container">
          <div className="analytics-header">
            <h3>📊 Analytics Dashboard</h3>
            <p>Platform insights and moderation statistics</p>
          </div>

          <div className="analytics-grid-new">
            {/* Safety Score Card */}
            <div className="analytics-card-large safety-card">
              <div className="card-header">
                <span className="card-icon">🛡️</span>
                <h4>Safety Score</h4>
              </div>
              <div className="safety-gauge">
                <div className="gauge-circle">
                  <svg viewBox="0 0 120 120">
                    <circle cx="60" cy="60" r="54" fill="none" stroke="#334155" strokeWidth="12"/>
                    <circle cx="60" cy="60" r="54" fill="none" stroke="#22c55e" strokeWidth="12" 
                      strokeDasharray={`${Math.min(stats.stats.non_abusive / (stats.stats.total_comments || 1) * 339.3, 339.3)} 339.3`}
                      strokeLinecap="round"
                      transform="rotate(-90 60 60)"/>
                  </svg>
                  <div className="gauge-value">
                    <span className="gauge-number">{Math.round(stats.stats.non_abusive / (stats.stats.total_comments || 1) * 100)}%</span>
                    <span className="gauge-label">Safe</span>
                  </div>
                </div>
              </div>
              <div className="safety-breakdown">
                <div className="breakdown-item">
                  <span className="breakdown-dot safe"></span>
                  <span>Safe: {stats.stats.non_abusive}</span>
                </div>
                <div className="breakdown-item">
                  <span className="breakdown-dot warning"></span>
                  <span>Warning: {stats.stats.intermediate}</span>
                </div>
              </div>
            </div>

            {/* Platform Overview */}
            <div className="analytics-card-large overview-card">
              <div className="card-header">
                <span className="card-icon">📈</span>
                <h4>Platform Overview</h4>
              </div>
              <div className="overview-stats">
                <div className="overview-stat">
                  <div className="overview-icon">👥</div>
                  <div className="overview-info">
                    <span className="overview-value">{stats.stats.total_users}</span>
                    <span className="overview-label">Total Users</span>
                  </div>
                </div>
                <div className="overview-stat">
                  <div className="overview-icon">💬</div>
                  <div className="overview-info">
                    <span className="overview-value">{stats.stats.total_comments}</span>
                    <span className="overview-label">Comments</span>
                  </div>
                </div>
                <div className="overview-stat">
                  <div className="overview-icon blocked">🔒</div>
                  <div className="overview-info">
                    <span className="overview-value">{stats.stats.blocked_users}</span>
                    <span className="overview-label">Blocked</span>
                  </div>
                </div>
                <div className="overview-stat">
                  <div className="overview-icon warning">⚠️</div>
                  <div className="overview-info">
                    <span className="overview-value">{stats.stats.intermediate}</span>
                    <span className="overview-label">Warnings</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Content Distribution Chart */}
            <div className="analytics-card-large chart-card">
              <div className="card-header">
                <span className="card-icon">📊</span>
                <h4>Image Distribution</h4>
              </div>
              <div className="distribution-chart">
                <div className="chart-bar">
                  <div className="bar-label">Safe</div>
                  <div className="bar-track">
                    <div className="bar-fill safe" style={{width: `${(stats.stats.image_safe / (stats.stats.image_total || 1)) * 100}%`}}></div>
                  </div>
                  <div className="bar-value">{stats.stats.image_safe || 0}</div>
                </div>
                <div className="chart-bar">
                  <div className="bar-label">Warning</div>
                  <div className="bar-track">
                    <div className="bar-fill warning" style={{width: `${(stats.stats.image_warning / (stats.stats.image_total || 1)) * 100}%`}}></div>
                  </div>
                  <div className="bar-value">{stats.stats.image_warning || 0}</div>
                </div>
              </div>
            </div>

            {/* Text Distribution Chart */}
            <div className="analytics-card-large chart-card">
              <div className="card-header">
                <span className="card-icon">💬</span>
                <h4>Text Distribution</h4>
              </div>
              <div className="distribution-chart">
                <div className="chart-bar">
                  <div className="bar-label">Safe</div>
                  <div className="bar-track">
                    <div className="bar-fill safe" style={{width: `${(stats.stats.text_safe / (stats.stats.text_total || 1)) * 100}%`}}></div>
                  </div>
                  <div className="bar-value">{stats.stats.text_safe || 0}</div>
                </div>
                <div className="chart-bar">
                  <div className="bar-label">Warning</div>
                  <div className="bar-track">
                    <div className="bar-fill warning" style={{width: `${(stats.stats.text_warning / (stats.stats.text_total || 1)) * 100}%`}}></div>
                  </div>
                  <div className="bar-value">{stats.stats.text_warning || 0}</div>
                </div>
              </div>
            </div>

            {/* Moderation Performance */}
            <div className="analytics-card-large performance-card">
              <div className="card-header">
                <span className="card-icon">⚡</span>
                <h4>Moderation Performance</h4>
              </div>
              <div className="performance-metrics-new">
                <div className="metric-card">
                  <span className="metric-icon">📝</span>
                  <span className="metric-value">{moderationLog.length}</span>
                  <span className="metric-label">Actions Today</span>
                </div>
                <div className="metric-card">
                  <span className="metric-icon success">✅</span>
                  <span className="metric-value">{moderationLog.filter(l => l.action.includes('Unblock')).length}</span>
                  <span className="metric-label">Unblocks</span>
                </div>
                <div className="metric-card">
                  <span className="metric-icon danger">🗑️</span>
                  <span className="metric-value">{moderationLog.filter(l => l.action.includes('Delete')).length}</span>
                  <span className="metric-label">Deletions</span>
                </div>
                <div className="metric-card">
                  <span className="metric-icon warning">🔄</span>
                  <span className="metric-value">{moderationLog.filter(l => l.action.includes('Reset')).length}</span>
                  <span className="metric-label">Resets</span>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="analytics-card-large actions-card">
              <div className="card-header">
                <span className="card-icon">🚀</span>
                <h4>Quick Actions</h4>
              </div>
              <div className="quick-actions-grid">
                <button onClick={() => setActiveTab('users')} className="quick-action-btn">
                  <span className="action-icon">👥</span>
                  <span className="action-text">Manage Users</span>
                </button>
                <button onClick={() => setActiveTab('comments')} className="quick-action-btn">
                  <span className="action-icon">💬</span>
                  <span className="action-text">View Comments</span>
                </button>
                <button onClick={exportCSV} className="quick-action-btn export">
                  <span className="action-icon">📊</span>
                  <span className="action-text">Export Report</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {showUserModal && selectedUser && (
        <div className="user-modal-overlay" onClick={() => setShowUserModal(false)}>
          <div className="user-modal-beautiful" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close-btn" onClick={() => setShowUserModal(false)}>×</button>
            
            <div className="modal-profile">
              <div className="profile-avatar">
                {selectedUser.username?.[0]?.toUpperCase()}
              </div>
              <h2>{selectedUser.username}</h2>
              <p>{selectedUser.email}</p>
              <span className={`profile-status ${selectedUser.is_blocked ? 'blocked' : 'active'}`}>
                {selectedUser.is_blocked ? '🔒 Blocked Account' : '✅ Active Account'}
              </span>
            </div>

            <div className="modal-stats-grid">
              <div className="stat-mini-card safe">
                <span className="stat-mini-icon">✅</span>
                <span className="stat-mini-value">{userStats?.nonAbusive || userStats?.non_abusive || 0}</span>
                <span className="stat-mini-label">Safe</span>
              </div>
              <div className="stat-mini-card warning">
                <span className="stat-mini-icon">⚠️</span>
                <span className="stat-mini-value">{userStats?.intermediate || 0}</span>
                <span className="stat-mini-label">Warning</span>
              </div>
              <div className="stat-mini-card total">
                <span className="stat-mini-icon">💬</span>
                <span className="stat-mini-value">{userHistory.length}</span>
                <span className="stat-mini-label">Total</span>
              </div>
              <div className="stat-mini-card alert">
                <span className="stat-mini-icon">⚠️</span>
                <span className="stat-mini-value">{selectedUser.warning_count || 0}</span>
                <span className="stat-mini-label">Warnings</span>
              </div>
            </div>

            <div className="modal-comments-section">
              <h3>📋 User Comments History</h3>
              <div className="comments-scroll">
                {userHistory.length === 0 ? (
                  <div className="no-comments">No comments yet</div>
                ) : (
                  userHistory.map((comment, index) => (
                    <div key={index} className={`comment-card ${comment.prediction?.toLowerCase().replace('-', '')}`}>
                      <div className="comment-header">
                        <span className="comment-type-icon">{comment.type === 'text' ? '💬' : '🖼️'}</span>
                        <span className={`comment-badge ${comment.prediction?.toLowerCase().replace('-', '')}`}>
                          {comment.prediction === 'Intermediate' ? '⚠️ Warning' : '✅ Safe'}
                        </span>
                        <span className="comment-date">{new Date(comment.created_at).toLocaleString()}</span>
                      </div>
                      <div className="comment-body">
                        {comment.content || <em className="image-text">Image Comment</em>}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="modal-footer-actions">
              <button onClick={() => { handleResetWarnings(selectedUser.id, selectedUser.username); }} className="btn-action-modal reset">
                🔄 Reset Warnings
              </button>
              <button onClick={() => { handleBlockUser(selectedUser.id, selectedUser.username, selectedUser.is_blocked); setShowUserModal(false); }} className={`btn-action-modal ${selectedUser.is_blocked ? 'unblock' : 'block'}`}>
                {selectedUser.is_blocked ? '🔓 Unblock User' : '🔒 Block User'}
              </button>
              <button onClick={() => { handleDeleteUser(selectedUser.id, selectedUser.username); setShowUserModal(false); }} className="btn-action-modal delete">
                🗑️ Delete User
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AdminPanel;
