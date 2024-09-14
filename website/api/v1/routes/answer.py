from flask import request, jsonify
from oauth2 import get_current_user
from database import get_db
from models import Question, QuizAttempt, CorrectAnswer, Answer
from sqlalchemy.exc import DataError
from . import views


@views.route('/users/<int:user_id>/quizzes/<int:quiz_id>/attempts/<int:attempt_id>/questions/<int:question_id>/answer', methods=['POST'], strict_slashes=False)
def submit_answer(user_id, quiz_id, attempt_id, question_id):
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
    if user.role != 'student':
        return jsonify({"detail": "Unauthorized access"}), 403

    attempt = db.query(QuizAttempt).filter_by(id=attempt_id, user_id=user_id, quiz_id=quiz_id, is_submitted=False).first()
    if not attempt:
        return jsonify({"detail": "Attempt not found"}), 404
    
    if attempt.is_submitted:
        return jsonify({"detail": "Attempt has already been submitted and cannot be updated"}), 400

    question = db.query(Question).filter(Question.id == question_id, Question.quiz_id == quiz_id).first()
    if not question:
        return jsonify({"detail": "Question not found"}), 404

    data = request.json
    
    if data.get('content') is None:
        return jsonify({"detail": "Answer content is required"}), 400

    if question.question_type == 'true_false' or question.question_type == 'choose':
        correct_answer = db.query(CorrectAnswer).filter(CorrectAnswer.question_id == question_id).first()
        if not correct_answer:
            return jsonify({"detail": "Correct answer not found"}), 404
        if data['content'] != correct_answer.correct_answer:
            score = 0
        else:
            score = question.points
    else:
        score = 0
    answer = Answer(
        question_id=question_id, attempt_id=attempt.id,
        content=data['content'], points_awarded=score
    )
    db.add(answer)
    db.commit()

    return jsonify({"message": "Answer submitted successfully"}), 201

@views.route('/users/<int:user_id>/quizzes/<int:quiz_id>/attempts/<int:attempt_id>/questions/<int:question_id>/answer', methods=['GET'], strict_slashes=False)
def get_one_answer(user_id, quiz_id, attempt_id, question_id):
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
    if user.role != 'student':
        return jsonify({"detail": "Unauthorized access"}), 403

    attempt = db.query(QuizAttempt).filter_by(id=attempt_id, user_id=user_id, quiz_id=quiz_id, is_submitted=False).first()
    if not attempt:
        return jsonify({"detail": "Attempt not found"}), 404

    if attempt.is_submitted:
        return jsonify({"detail": "Attempt has already been submitted"}), 400

    question = db.query(Question).filter(Question.id == question_id, Question.quiz_id == quiz_id).first()
    if not question:
        return jsonify({"detail": "Question not found"}), 404

    answer = db.query(Answer).filter(Answer.attempt_id == attempt_id, Answer.question_id == question_id).first()
    if not answer:
        return jsonify({"detail": "Answer not found"}), 404

    return jsonify({
        "id": answer.id, "question_id": answer.question_id,
        "attempt_id": answer.attempt_id, "content": answer.content,
        "points_awarded": answer.points_awarded
    }), 200

@views.route('/users/<int:user_id>/quizzes/<int:quiz_id>/attempts/<int:attempt_id>/answer', methods=['GET'], strict_slashes=False)
def get_all_attempt_answers(user_id, quiz_id, attempt_id):
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
    if user.role == 'student':
        attempt = db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id, QuizAttempt.user_id == user_id, QuizAttempt.quiz_id == quiz_id).first()
    if user.role == 'teacher':
        attempt = db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id, QuizAttempt.quiz_id == quiz_id).first()

    if not attempt:
        return jsonify({"detail": "Attempt not found"}), 404

    answers = db.query(Answer).filter(Answer.attempt_id == attempt_id).all()
    if not answers:
        return jsonify({"detail": "Answer not found"}), 404

    response_data = []
    for answer in answers:
        response_data.append({
            "id": answer.id, "question_id": answer.question_id,
            "attempt_id": answer.attempt_id, "content": answer.content,
            "points_awarded": answer.points_awarded
        })

    return jsonify(response_data), 200

@views.route('/users/<int:user_id>/quizzes/<int:quiz_id>/attempts/<int:attempt_id>/questions/<int:question_id>/answer/update', methods=['PUT'], strict_slashes=False)
def update_answer(user_id, quiz_id, attempt_id, question_id):
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
    if user.role != 'student':
        return jsonify({"detail": "Unauthorized access"}), 403

    attempt = db.query(QuizAttempt).filter_by(id=attempt_id, user_id=user_id, quiz_id=quiz_id, is_submitted=False).first()
    if not attempt:
        return jsonify({"detail": "Attempt not found"}), 404

    if attempt.is_submitted:
        return jsonify({"detail": "Attempt has already been submitted and cannot be updated"}), 400

    question = db.query(Question).filter(Question.id == question_id, Question.quiz_id == quiz_id).first()
    if not question:
        return jsonify({"detail": "Question not found"}), 404

    answer = db.query(Answer).filter(Answer.attempt_id == attempt_id, Answer.question_id == question_id).first()
    if not answer:
        return jsonify({"detail": "Answer not found"}), 404

    data = request.json
    if data.get('content') is None:
        return jsonify({"detail": "Answer content is required"}), 400

    if question.question_type == 'true_false' or question.question_type == 'choose':
        correct_answer = db.query(CorrectAnswer).filter(CorrectAnswer.question_id == question_id).first()
        if not correct_answer:
            return jsonify({"detail": "Correct answer not found"}), 404
        if data['content'] != correct_answer.correct_answer:
            score = 0
        else:
            score = question.points
    else:
        score = 0

    try:
        answer.content = data['content']
        answer.points_awarded = score
        db.commit()
        return jsonify({"message": "Answer updated successfully"}), 200
    
    except DataError:
        db.rollback()
        return jsonify({"detail": "Database error occurred"}), 500

@views.route('/users/<int:user_id>/quizzes/<int:quiz_id>/attempts/<int:attempt_id>/questions/<int:question_id>/answer/delete', methods=['DELETE'], strict_slashes=False)
def delete_answer(user_id, quiz_id, attempt_id, question_id):
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
    if user.role != 'student':
        return jsonify({"detail": "Unauthorized access"}), 403

    attempt = db.query(QuizAttempt).filter_by(id=attempt_id, user_id=user_id, quiz_id=quiz_id, is_submitted=False).first()
    if not attempt:
        return jsonify({"detail": "Attempt not found"}), 404

    question = db.query(Question).filter(Question.id == question_id, Question.quiz_id == quiz_id).first()
    if not question:
        return jsonify({"detail": "Question not found"}), 404

    answer = db.query(Answer).filter(Answer.attempt_id == attempt_id, Answer.question_id == question_id).first()
    if not answer:
        return jsonify({"detail": "Answer not found"}), 404

    db.delete(answer)
    db.commit()
    return jsonify({"message": "Answer deleted successfully"}), 200
