from flask import request, jsonify
from oauth2 import get_current_user
from database import get_db
from models import Question, QuestionBank, CorrectAnswer
from sqlalchemy.exc import DataError
from . import views


@views.route('/users/<int:user_id>/question_bank/<int:question_bank_id>/questions', methods=['POST'], strict_slashes=False)
def add_question_to_bank(user_id, question_bank_id):
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

    question_bank = db.query(QuestionBank).filter(QuestionBank.id == question_bank_id, QuestionBank.creator_id == user_id).first()
    if not question_bank:
        return jsonify({"detail": "Question bank not found"}), 404

    data = request.json

    if data['question_type'] not in ['true_false', 'choose', 'written']:
        return jsonify({"detail": "Invalid question type"}), 400

    new_question = Question(
        quiz_banks_id=question_bank_id, content=data['content'],
        points=data['points'], question_type=data['question_type']
    )
    db.add(new_question)
    db.commit()

    if new_question.question_type == 'true_false' or new_question.question_type == 'choose':
        correct_answer_data = data.get('correct_answer')
        if not correct_answer_data:
            db.delete(new_question)
            db.commit()
            return jsonify({"detail": "Correct answer is required"}), 400

        correct_answer = CorrectAnswer(
            question_id=new_question.id,
            correct_answer=correct_answer_data
        )
        db.add(correct_answer)
        db.commit()

    return jsonify({"message": "Question added to question bank successfully", "question_id": new_question.id}), 201

@views.route('/users/<int:user_id>/question_bank/<int:question_bank_id>/questions/<int:question_id>', methods=['GET'], strict_slashes=False)
def get_one_question_from_bank(user_id, question_bank_id, question_id):
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

    question = db.query(Question).filter(Question.id == question_id, Question.quiz_banks_id == question_bank_id).first()
    if not question:
        return jsonify({"detail": "Question not found"}), 404

    response_data = {
        "id": question.id, "content": question.content,
        "question_type": question.question_type, "points": question.points,
        "created_at": question.created_at,
    }

    if question.question_type in ['true_false', 'choose']:
        correct_answer = db.query(CorrectAnswer).filter(CorrectAnswer.question_id == question_id).first()
        if correct_answer:
            response_data["correct_answer"] = correct_answer.correct_answer

    return jsonify(response_data), 200

@views.route('/users/<int:user_id>/question_bank/<int:question_bank_id>/questions/', methods=['GET'], strict_slashes=False)
def get_all_questions_in_bank(user_id, question_bank_id):
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

    questions = db.query(Question).filter(Question.quiz_banks_id == question_bank_id).all()
    if not questions:
        return jsonify({"detail": "Question not found"}), 404

    response_data = []
    for question in questions:
        question_data = {
            "id": question.id,
            "content": question.content,
            "points": question.points,
            "created_at": question.created_at,
            "updated_at": question.updated_at,
            "question_type": question.question_type
        }

        if question.question_type in ['true_false', 'choose']:
            correct_answer = db.query(CorrectAnswer).filter(CorrectAnswer.question_id == question.id).first()
            if correct_answer:
                question_data["correct_answer"] = correct_answer.correct_answer

        response_data.append(question_data)

    return jsonify(response_data), 200

@views.route('/users/<int:user_id>/question_bank/<int:question_bank_id>/questions/<int:question_id>/delete', methods=['DELETE'], strict_slashes=False)
def delete_question_from_bank(user_id, question_bank_id, question_id):
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

    question = db.query(Question).filter(Question.id == question_id, Question.quiz_banks_id == question_bank_id).first()
    if not question:
        return jsonify({"detail": "Question not found"}), 404

    db.delete(question)
    db.commit()
    return jsonify({"message": "Question deleted from question bank successfully"}), 200

@views.route('/users/<int:user_id>/question_bank/<int:question_bank_id>/questions/<int:question_id>/update', methods=['PUT'], strict_slashes=False)
def update_question_in_bank(user_id, question_bank_id, question_id):
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

    question = db.query(Question).filter(Question.id == question_id, Question.quiz_banks_id == question_bank_id).first()
    if not question:
        return jsonify({"detail": "Question not found"}), 404

    data = request.json

    if data['question_type'] not in ['true_false', 'choose', 'written']:
        return jsonify({"detail": "Invalid question type"}), 400

    try:
        question.content = data['content']
        question.points = data['points']
        question.question_type = data['question_type']
        db.commit()
        return jsonify({"message": "Question updated successfully"}), 200
    
    except DataError:
        db.rollback()
        return jsonify({"detail": "Database error occurred"}), 500

