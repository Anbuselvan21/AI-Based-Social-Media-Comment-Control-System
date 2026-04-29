from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_jwt_extended import verify_jwt_in_request
from functools import wraps
from database import get_db
from werkzeug.security import generate_password_hash
import csv
import io
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            claims = get_jwt_identity()
            from flask_jwt_extended import get_jwt
            if not get_jwt().get('is_admin'):
                return jsonify({'error': 'Admin access required'}), 403
            return fn(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': 'Authentication required'}), 401
    return wrapper

@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@admin_required
def dashboard():
    conn = get_db()
    cursor = conn.cursor()
    
    total_comments = cursor.execute('SELECT COUNT(*) as count FROM comments').fetchone()['count']
    abusive = cursor.execute("SELECT COUNT(*) as count FROM comments WHERE prediction = 'Abusive'").fetchone()['count']
    non_abusive = cursor.execute("SELECT COUNT(*) as count FROM comments WHERE prediction = 'Non-Abusive'").fetchone()['count']
    intermediate = cursor.execute("SELECT COUNT(*) as count FROM comments WHERE prediction = 'Intermediate'").fetchone()['count']
    
    # Image comments stats
    image_safe = cursor.execute("SELECT COUNT(*) as count FROM comments WHERE type = 'image' AND prediction = 'Non-Abusive'").fetchone()['count']
    image_warning = cursor.execute("SELECT COUNT(*) as count FROM comments WHERE type = 'image' AND prediction = 'Intermediate'").fetchone()['count']
    
    # Text comments stats
    text_safe = cursor.execute("SELECT COUNT(*) as count FROM comments WHERE type = 'text' AND prediction = 'Non-Abusive'").fetchone()['count']
    text_warning = cursor.execute("SELECT COUNT(*) as count FROM comments WHERE type = 'text' AND prediction = 'Intermediate'").fetchone()['count']
    
    total_users = cursor.execute('SELECT COUNT(*) as count FROM users WHERE is_admin = 0').fetchone()['count']
    blocked_users = cursor.execute('SELECT COUNT(*) as count FROM users WHERE is_blocked = 1').fetchone()['count']
    
    recent_comments = cursor.execute('''
        SELECT c.*, u.username 
        FROM comments c 
        JOIN users u ON c.user_id = u.id 
        ORDER BY c.created_at DESC 
        LIMIT 10
    ''').fetchall()
    
    comments_by_type = cursor.execute('''
        SELECT type, COUNT(*) as count 
        FROM comments 
        GROUP BY type
    ''').fetchall()
    
    conn.close()
    
    return jsonify({
        'stats': {
            'total_comments': total_comments,
            'abusive': abusive,
            'non_abusive': non_abusive,
            'intermediate': intermediate,
            'abusive_percentage': round((abusive / total_comments * 100), 2) if total_comments > 0 else 0,
            'total_users': total_users,
            'blocked_users': blocked_users,
            # Image stats
            'image_safe': image_safe,
            'image_warning': image_warning,
            'image_total': image_safe + image_warning,
            # Text stats
            'text_safe': text_safe,
            'text_warning': text_warning,
            'text_total': text_safe + text_warning
        },
        'recent_comments': [dict(c) for c in recent_comments],
        'comments_by_type': [dict(c) for c in comments_by_type]
    }), 200

@admin_bp.route('/comments', methods=['GET'])
@jwt_required()
@admin_required
def get_all_comments():
    filter_type = request.args.get('filter', 'all')
    comment_type = request.args.get('type', 'all')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    conn = get_db()
    cursor = conn.cursor()
    
    query = '''
        SELECT c.*, u.username, u.email 
        FROM comments c 
        JOIN users u ON c.user_id = u.id 
        WHERE 1=1
    '''
    params = []
    
    if filter_type != 'all':
        query += ' AND c.prediction = ?'
        params.append(filter_type)
    
    if comment_type != 'all':
        query += ' AND c.type = ?'
        params.append(comment_type)
    
    query += ' ORDER BY c.created_at DESC LIMIT ? OFFSET ?'
    params.extend([per_page, (page - 1) * per_page])
    
    comments = cursor.execute(query, params).fetchall()
    
    count_query = '''
        SELECT COUNT(*) as count 
        FROM comments c 
        JOIN users u ON c.user_id = u.id 
        WHERE 1=1
    '''
    count_params = []
    
    if filter_type != 'all':
        count_query += ' AND c.prediction = ?'
        count_params.append(filter_type)
    
    if comment_type != 'all':
        count_query += ' AND c.type = ?'
        count_params.append(comment_type)
    
    total = cursor.execute(count_query, count_params).fetchone()['count']
    
    conn.close()
    
    return jsonify({
        'comments': [dict(c) for c in comments],
        'total': total,
        'page': page,
        'per_page': per_page
    }), 200

@admin_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_comment(comment_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM comments WHERE id = ?', (comment_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Comment deleted successfully'}), 200

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required
def get_users():
    conn = get_db()
    cursor = conn.cursor()
    
    users = cursor.execute('''
        SELECT u.id, u.username, u.email, u.is_blocked, u.warning_count, u.created_at,
               COUNT(c.id) as comment_count
        FROM users u
        LEFT JOIN comments c ON u.id = c.user_id
        WHERE u.is_admin = 0
        GROUP BY u.id
        ORDER BY u.created_at DESC
    ''').fetchall()
    
    conn.close()
    
    return jsonify([dict(u) for u in users]), 200

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
@admin_required
def get_user_details(user_id):
    conn = get_db()
    cursor = conn.cursor()
    
    user = cursor.execute('''
        SELECT u.id, u.username, u.email, u.is_blocked, u.warning_count, u.created_at,
               COUNT(c.id) as total_comments
        FROM users u
        LEFT JOIN comments c ON u.id = c.user_id
        WHERE u.id = ?
        GROUP BY u.id
    ''', (user_id,)).fetchone()
    
    if not user:
        conn.close()
        return jsonify({'error': 'User not found'}), 404
    
    abusive_count = cursor.execute('''
        SELECT COUNT(*) as count FROM comments 
        WHERE user_id = ? AND prediction = 'Abusive'
    ''', (user_id,)).fetchone()['count']
    
    intermediate_count = cursor.execute('''
        SELECT COUNT(*) as count FROM comments 
        WHERE user_id = ? AND prediction = 'Intermediate'
    ''', (user_id,)).fetchone()['count']
    
    non_abusive_count = cursor.execute('''
        SELECT COUNT(*) as count FROM comments 
        WHERE user_id = ? AND prediction = 'Non-Abusive'
    ''', (user_id,)).fetchone()['count']
    
    warnings = cursor.execute('''
        SELECT * FROM warnings 
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 10
    ''', (user_id,)).fetchall()
    
    recent_comments = cursor.execute('''
        SELECT * FROM comments 
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 10
    ''', (user_id,)).fetchall()
    
    conn.close()
    
    return jsonify({
        'user': dict(user),
        'stats': {
            'total_comments': user['total_comments'],
            'abusive': abusive_count,
            'intermediate': intermediate_count,
            'non_abusive': non_abusive_count
        },
        'warnings': [dict(w) for w in warnings],
        'recent_comments': [dict(c) for c in recent_comments]
    }), 200

@admin_bp.route('/users/<int:user_id>/reset-warnings', methods=['POST'])
@jwt_required()
@admin_required
def reset_user_warnings(user_id):
    conn = get_db()
    cursor = conn.cursor()
    
    user = cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if not user:
        conn.close()
        return jsonify({'error': 'User not found'}), 404
    
    cursor.execute('UPDATE users SET is_blocked = 0, warning_count = 0 WHERE id = ?', (user_id,))
    cursor.execute('DELETE FROM warnings WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    
    return jsonify({
        'message': f'User {user["username"]} has been unblocked and all warnings reset',
        'is_blocked': False,
        'warning_count': 0
    }), 200

@admin_bp.route('/users/<int:user_id>/block', methods=['POST'])
@jwt_required()
@admin_required
def block_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    
    user = cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if not user:
        conn.close()
        return jsonify({'error': 'User not found'}), 404
    
    if user['is_admin']:
        conn.close()
        return jsonify({'error': 'Cannot block admin users'}), 403
    
    new_status = 0 if user['is_blocked'] else 1
    
    cursor.execute('UPDATE users SET is_blocked = ? WHERE id = ?', (new_status, user_id))
    
    if new_status == 0:
        cursor.execute('UPDATE users SET warning_count = 0 WHERE id = ?', (user_id,))
        cursor.execute('DELETE FROM warnings WHERE user_id = ?', (user_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'message': 'User unblocked and warnings reset' if new_status == 0 else 'User blocked',
        'is_blocked': bool(new_status),
        'warning_count': 0 if new_status == 0 else user['warning_count']
    }), 200

@admin_bp.route('/users/<int:user_id>/delete', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    
    user = cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    
    if not user:
        conn.close()
        return jsonify({'error': 'User not found'}), 404
    
    if user['is_admin']:
        conn.close()
        return jsonify({'error': 'Cannot delete admin users'}), 403
    
    cursor.execute('DELETE FROM comments WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'User deleted successfully'}), 200

@admin_bp.route('/analytics/daily', methods=['GET'])
@jwt_required()
@admin_required
def daily_analytics():
    days = int(request.args.get('days', 7))
    
    conn = get_db()
    cursor = conn.cursor()
    
    daily_stats = cursor.execute('''
        SELECT DATE(created_at) as date, 
               COUNT(*) as total,
               SUM(CASE WHEN prediction = 'Abusive' THEN 1 ELSE 0 END) as abusive
        FROM comments
        WHERE created_at >= DATE('now', '-' || ? || ' days')
        GROUP BY DATE(created_at)
        ORDER BY date
    ''', (days,)).fetchall()
    
    conn.close()
    
    return jsonify([dict(d) for d in daily_stats]), 200

@admin_bp.route('/export/csv', methods=['GET'])
@jwt_required()
@admin_required
def export_csv():
    conn = get_db()
    cursor = conn.cursor()
    
    comments = cursor.execute('''
        SELECT c.*, u.username, u.email 
        FROM comments c 
        JOIN users u ON c.user_id = u.id 
        ORDER BY c.id DESC
    ''').fetchall()
    
    conn.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['ID', 'Username', 'Email', 'Type', 'Content', 'Prediction', 'Confidence', 'Created At'])
    
    for comment in comments:
        created_at = comment['created_at']
        if isinstance(created_at, str):
            try:
                dt = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                created_at = dt.strftime('%m/%d/%Y %I:%M:%S %p')
            except:
                pass
        writer.writerow([
            comment['id'],
            comment['username'],
            comment['email'],
            comment['type'],
            comment['content'] or '',
            comment['prediction'],
            comment['confidence'],
            created_at
        ])
    
    return output.getvalue(), 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': 'attachment; filename=comments_export.csv'
    }

@admin_bp.route('/export/pdf', methods=['GET'])
@jwt_required()
@admin_required
def export_pdf():
    conn = get_db()
    cursor = conn.cursor()
    
    total_comments = cursor.execute('SELECT COUNT(*) as count FROM comments').fetchone()['count']
    abusive = cursor.execute("SELECT COUNT(*) as count FROM comments WHERE prediction = 'Abusive'").fetchone()['count']
    non_abusive = cursor.execute("SELECT COUNT(*) as count FROM comments WHERE prediction = 'Non-Abusive'").fetchone()['count']
    intermediate = cursor.execute("SELECT COUNT(*) as count FROM comments WHERE prediction = 'Intermediate'").fetchone()['count']
    
    conn.close()
    
    report = f"""
    AI Comment Control System - Report
    Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    Summary Statistics:
    - Total Comments: {total_comments}
    - Abusive: {abusive} ({round(abusive/total_comments*100, 2) if total_comments > 0 else 0}%)
    - Non-Abusive: {non_abusive} ({round(non_abusive/total_comments*100, 2) if total_comments > 0 else 0}%)
    - Intermediate: {intermediate} ({round(intermediate/total_comments*100, 2) if total_comments > 0 else 0}%)
    """
    
    return report, 200, {
        'Content-Type': 'text/plain',
        'Content-Disposition': 'attachment; filename=report.txt'
    }
