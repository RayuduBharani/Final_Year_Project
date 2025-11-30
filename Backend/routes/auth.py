from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

from config.database import users_collection, sessions_collection
from utils.helpers import serialize_doc, generate_session_token

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/login', methods=['POST'])
def login():
    """HR Login endpoint"""
    data = request.get_json()
    email = data.get('email', '').lower().strip()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password are required'}), 400
    
    user = users_collection.find_one({'email': email})
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
    
    # Create session token
    token = generate_session_token()
    sessions_collection.insert_one({
        'token': token,
        'user_id': str(user['_id']),
        'email': email,
        'expires_at': datetime.now() + timedelta(hours=24)
    })
    
    return jsonify({
        'success': True,
        'message': 'Login successful',
        'token': token,
        'user': {
            'id': str(user['_id']),
            'email': user['email'],
            'name': user['name'],
            'role': user['role']
        }
    })


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """HR Logout endpoint"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token:
        sessions_collection.delete_one({'token': token})
    return jsonify({'success': True, 'message': 'Logged out successfully'})


@auth_bp.route('/verify', methods=['GET'])
def verify_token():
    """Verify if session token is valid"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    session = sessions_collection.find_one({'token': token})
    
    if not session:
        return jsonify({'valid': False}), 401
    
    if datetime.now() > session['expires_at']:
        sessions_collection.delete_one({'token': token})
        return jsonify({'valid': False, 'message': 'Session expired'}), 401
    
    user = users_collection.find_one({'email': session['email']})
    return jsonify({
        'valid': True,
        'user': {
            'id': str(user['_id']),
            'email': user['email'],
            'name': user['name'],
            'role': user['role']
        }
    })


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new HR user"""
    data = request.get_json()
    email = data.get('email', '').lower().strip()
    password = data.get('password', '')
    name = data.get('name', '').strip()
    
    if not email or not password or not name:
        return jsonify({'success': False, 'message': 'All fields are required'}), 400
    
    if len(password) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400
    
    if users_collection.find_one({'email': email}):
        return jsonify({'success': False, 'message': 'Email already registered'}), 400
    
    result = users_collection.insert_one({
        'email': email,
        'password': generate_password_hash(password),
        'name': name,
        'role': 'hr',
        'created_at': datetime.now()
    })
    
    return jsonify({'success': True, 'message': 'Registration successful', 'user_id': str(result.inserted_id)})
