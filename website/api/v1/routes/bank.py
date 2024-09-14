from flask import request, jsonify
from oauth2 import get_current_user
from database import get_db
from models import QuestionBank
from sqlalchemy.exc import DataError
from . import views


@views.route('/users/<int:user_id>/question_bank', methods=['POST'], strict_slashes=False)
def create_bank(user_id):
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
    if user.role != 'teacher':
        return jsonify({"detail": "Unauthorized access"}), 403

    data = request.json
    new_bank = QuestionBank(
        creator_id=user_id, title=data['title'],
        description=data['description']
    )
    db.add(new_bank)
    db.commit()

    return jsonify({"message": "Question bank created successfully", "question_bank_id": new_bank.id}), 201

@views.route('/users/<int:user_id>/question_bank/<int:question_bank_id>/update', methods=['PUT'], strict_slashes=False)
def update_bank(user_id, question_bank_id):
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
    if user.role != 'teacher':
        return jsonify({"detail": "Unauthorized access"}), 403

    bank = db.query(QuestionBank).filter(QuestionBank.id == question_bank_id, QuestionBank.creator_id == user_id).first()
    if not bank:
        return jsonify({"detail": "Question bank not found"}), 404

    data = request.json
    try:
        bank.title = data['title']
        bank.description = data['description']

        db.commit()
        return jsonify({"message": "Question bank updated successfully"}), 200
    
    except DataError:
        db.rollback()
        return jsonify({"detail": "Database error occurred"}), 500

@views.route('/users/<int:user_id>/question_bank/<int:question_bank_id>/delete', methods=['DELETE'], strict_slashes=False)
def delete_bank(user_id, question_bank_id):
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
    if user.role != 'teacher':
        return jsonify({"detail": "Unauthorized access"}), 403

    bank = db.query(QuestionBank).filter(QuestionBank.id == question_bank_id, QuestionBank.creator_id == user_id).first()
    if not bank:
        return jsonify({"detail": "Question bank not found"}), 404

    db.delete(bank)
    db.commit()
    return jsonify({"message": "Question bank deleted successfully"}), 200

@views.route('/users/<int:user_id>/question_bank', methods=['GET'], strict_slashes=False)
def get_all_banks(user_id):
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
    if user.role != 'teacher':
        return jsonify({"detail": "Unauthorized access"}), 403

    banks = db.query(QuestionBank).filter(QuestionBank.creator_id == user_id).all()

    if not banks:
        return jsonify({"detail": "Question bank not found"}), 404
    
    response_data = []
    for question_bank in banks:
        response_data.append({
            "title": question_bank.title,
            "description": question_bank.description, "created_at": question_bank.created_at,
            "updated_at": question_bank.updated_at
        })

    return jsonify(response_data), 200

@views.route('/users/<int:user_id>/question_bank/<int:question_bank_id>', methods=['GET'], strict_slashes=False)
def get_one_bank(user_id, question_bank_id):
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
    if user.role != 'teacher':
        return jsonify({"detail": "Unauthorized access"}), 403

    question_back = db.query(QuestionBank).filter(QuestionBank.id == question_bank_id, QuestionBank.creator_id == user_id).first()

    if not question_back:
        return jsonify({"detail": "Question bank not found"}), 404
    
    return jsonify({
        "title": question_back.title,
        "description": question_back.description, "created_at": question_back.created_at,
        "updated_at": question_back.updated_at
    }), 200
