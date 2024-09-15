from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from oauth2 import get_current_user
from database import get_db
from models import User
from . import auth


@auth.route('/users/<int:user_id>/profile', methods=['GET'])
def get_user_profile(user_id: int):
    """
    Get user profile.
    Args:
        user_id (int): The ID of the user.
    Returns:
        JSON: A JSON response containing the user profile data.
    """
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
    """
    Update user profile.
    Args:
        user_id (int): The ID of the user.
    Returns:
        JSON: A JSON response containing a message and the updated user profile data.
    """
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
                    "role": user.role, "created_at": user.created_at, "updated_at": user.updated_at}), 200

@auth.route('/users/<int:user_id>/profile/delete', methods=['DELETE'])
def delete_user_profile(user_id):
    """
    Delete user profile.
    Args:
        user_id (int): The ID of the user.
    Returns:
        JSON: A JSON response containing a message.
    """
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
