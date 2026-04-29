from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    confirm_password = data.get('confirmPassword')
    
    if not all([username, email, password, confirm_password]):
        return jsonify({'error': 'All fields are required'}), 400
    
    if password != confirm_password:
        return jsonify({'error': 'Passwords do not match'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    existing_user = cursor.execute(
        'SELECT * FROM users WHERE username = ? OR email = ?',
        (username, email)
    ).fetchone()
    
    if existing_user:
        conn.close()
        return jsonify({'error': 'Username or email already exists'}), 409
    
    hashed_password = generate_password_hash(password)
    
    try:
        cursor.execute(
            'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
            (username, email, hashed_password)
        )
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    user = cursor.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    if user['is_blocked']:
        return jsonify({'error': 'Your account has been blocked'}), 403
    
    access_token = create_access_token(
        identity=str(user['id']),
        additional_claims={'username': user['username'], 'is_admin': bool(user['is_admin'])}
    )
    
    return jsonify({
        'access_token': access_token,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'is_admin': bool(user['is_admin'])
        }
    }), 200

@auth_bp.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    user = cursor.execute(
        'SELECT * FROM users WHERE username = ? AND is_admin = 1',
        (username,)
    ).fetchone()
    conn.close()
    
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'error': 'Invalid admin credentials'}), 401
    
    access_token = create_access_token(
        identity=str(user['id']),
        additional_claims={'username': user['username'], 'is_admin': True}
    )
    
    return jsonify({
        'access_token': access_token,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'is_admin': True
        }
    }), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    
    conn = get_db()
    cursor = conn.cursor()
    
    user = cursor.execute('SELECT id, username, email, is_admin, is_blocked, created_at FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'id': user['id'],
        'username': user['username'],
        'email': user['email'],
        'is_admin': bool(user['is_admin']),
        'is_blocked': bool(user['is_blocked']),
        'created_at': user['created_at']
    }), 200
