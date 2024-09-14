from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from oauth2 import create_access_token
from database import get_db
from models import User
import re
from . import auth
from gmail_service import send_email
from utils import generate_verification_code

cache = {}

@auth.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.query(User).filter(User.username == username).first()

        if user:
            if not user.is_verified:
                return jsonify({'message': 'User is not verified'}), 401
            if check_password_hash(user.hashed_password, password):
                access_token = create_access_token(data={'user_id': user.id, 'user_name': user.username})
                return jsonify({'access_token': access_token, 'token_type': 'bearer'})
            else:
                return jsonify({'message': 'Incorrect password or username'}), 401
        else:
            return jsonify({'message': 'Incorrect password or username'}), 401
    return jsonify({'message': 'Invalid request method'})

@auth.route('/register', methods=['POST'])
def register():
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

    if db.query(User).filter(User.email == email).first():
        return jsonify({'message': 'Email already exists'}), 400
    if db.query(User).filter(User.username == username).first():
        return jsonify({'message': 'Username already exists'}), 400

    hashed_password = generate_password_hash(request.form.get('password'))
    new_user = User(username=request.form.get('username'),
                    email=email, first_name=request.form.get('first_name'),
                    last_name=request.form.get('last_name'), role=request.form.get('role'),
                    hashed_password=hashed_password, is_verified=False
    )
    db.add(new_user)
    db.commit()


    verification_code = generate_verification_code()
    subject = "Your Verification Code"
    body = f"Your verification code is: {verification_code}"

    try:
        send_email(email, subject, body)
    except Exception as e:
        return jsonify({'error': 'Failed to send verification email.'}), 500

    cache[email] = verification_code

    return jsonify({'message': 'Verification code sent to email. Please verify to complete registration.'}), 200

@auth.route('/verify_code', methods=['POST'])
def verify_code():
    email = request.form.get('email')
    verification_code = request.form.get('verification_code')
    db = get_db()

    stored_code = cache[email]

    if verification_code == stored_code:
        # Proceed with registration
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            return jsonify({'message': 'incorrect email or code'}), 404
        user.is_verified = True

        db.commit()
        db.refresh(user)

        # Remove the email from the cache
        cache.pop(email, None)

        return jsonify({'message': 'User registered successfully', 'user_id': user.id}), 201
    else:
        return jsonify({'message': 'Invalid verification code'}), 400

@auth.route('/forgot_password', methods=['POST'])
def forgot_password():
    email = request.form.get('email')
    db = get_db()

    if not email:
        return jsonify({'message': 'Email is required'}), 400

    user = db.query(User).filter(User.email == email).first()

    if user:
        verification_code = generate_verification_code()
        subject = "Password Reset Code"
        body = f"Your password reset code is: {verification_code}"

        try:
            send_email(email, subject, body)
        except Exception as e:
            return jsonify({'error': 'Failed to send verification email.'}), 500

        cache[email] = verification_code

        return jsonify({'message': 'Password reset code sent to email.'}), 200
    else:
        return jsonify({'message': 'User not found'}), 404

@auth.route('/reset_password', methods=['POST'])
def reset_password():
    email = request.form.get('email')
    verification_code = request.form.get('verification_code')
    new_password = request.form.get('new_password')
    db = get_db()

    stored_code = cache[email]

    if verification_code == stored_code:
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            return jsonify({'message': 'User not found'}), 404

        user.hashed_password = generate_password_hash(new_password)
        db.commit()

        cache.pop(email, None)

        return jsonify({'message': 'Password reset successfully'}), 200
    else:
        return jsonify({'message': 'Invalid verification code'}), 400
