from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from oauth2 import create_access_token, get_current_user
from database import get_db
from models import User
import re


auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.query(User).filter(User.username == username).first()
        if user:
            if check_password_hash(user.hashed_password, password):
                access_token = create_access_token(data={'user_id': user.id, 'user_name': user.username})
                return jsonify({'access_token': access_token, 'token_type': 'bearer'})
            else:
                return jsonify({'message': 'Incorrect password or username'}), 401
        else:
            return jsonify({'message': 'Incorrect password or username'}), 401
    return jsonify({'message': 'Invalid request method'})

@auth.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        password = request.form.get('password')
        role = request.form.get('role')
        db = get_db()

        if not email or not username or not password or not role:
            return jsonify({'message': 'All fields are required'}), 400
        if len(password) < 8:
            return jsonify({'message': 'Password must be at least 8 characters long'}), 400
        if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
            return jsonify({'message': 'Invalid email format'}), 400
        if role not in ['admin', 'user']:
            return jsonify({'message': 'Invalid role'}), 400
        if db.query(User).filter(User.username == username).first():
            return jsonify({'message': 'Username already exists'}), 400
        if db.query(User).filter(User.email == email).first():
            return jsonify({'message': 'Email already exists'}), 400

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, first_name=first_name, last_name=last_name, role=role, hashed_password=hashed_password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return jsonify({'message': 'User created successfully', 'user_id': new_user.id}), 201

@auth.route('/users/<int:user_id>/profile', methods=['GET'])
def get_user_profile(user_id: int):
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"detail": "Token is missing"}), 401

    token = token.replace("Bearer ", "")
    user = get_current_user(token)

    if user is None:
        return jsonify({"detail": "Invalid or expired token"}), 401
    if user.id != user_id:
        return jsonify({"detail": "Unauthorized access"}), 403

    return jsonify({"username": user.username, "first_name": user.first_name,
                    "last_name": user.last_name, "email": user.email,
                    "role": user.role, "created_at": user.created_at}), 200

@auth.route('/users/<int:user_id>/profile/update', methods=['PUT'])
def update_user_profile(user_id):
    db = get_db()
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"detail": "Token is missing"}), 401
    
    token = token.replace("Bearer ", "")  # Remove the "Bearer " prefix if it's present
    user = get_current_user(token)

    if user is None:
        return jsonify({"detail": "Invalid or expired token"}), 401
    
    if user.id != user_id:
        return jsonify({"detail": "Unauthorized access"}), 403

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404
    if request.method == 'PUT':
        if 'email' in request.form:
            email = request.form.get('email')
            if db.query(User).filter(User.email == email).first():
                return jsonify({'message': 'Email already exists'}), 400
            user.email = email
        if 'first_name' in request.form:
            user.first_name = request.form.get('first_name')
        if 'last_name' in request.form:
            user.last_name = request.form.get('last_name')
        if 'password' in request.form:
            password = request.form.get('password')
            if len(password) < 8:
                return jsonify({'message': 'Password must be at least 8 characters long'}), 400
            user.hashed_password = generate_password_hash(password)
        
        db.add(user)
        db.commit()
        return jsonify({'message': 'User profile updated successfully',
                    "username": user.username, "first_name": user.first_name,
                    "last_name": user.last_name, "email": user.email,
                    "role": user.role, "password": password,
                    "created_at": user.created_at, "updated_at": user.updated_at}), 200

@auth.route('/users/<int:user_id>/profile/delete', methods=['DELETE'])
def delete_user_profile(user_id):
    db = get_db()
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"detail": "Token is missing"}), 401

    token = token.replace("Bearer ", "")
    user = get_current_user(token)

    if user is None:
        return jsonify({"detail": "Invalid or expired token"}), 401
    if user.id != user_id:
        return jsonify({"detail": "Unauthorized access"}), 403
    if not user:
        return jsonify({'message': 'User not found'}), 404

    user = db.query(User).filter(User.id == user_id).first()

    db.delete(user)
    db.commit()

    return jsonify({'message': 'User deleted successfully'}), 200
