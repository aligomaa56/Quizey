from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from oauth2 import create_access_token
from database import get_db
from models import User
import re
from . import auth


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
        if role not in ['student', 'teacher']:
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
