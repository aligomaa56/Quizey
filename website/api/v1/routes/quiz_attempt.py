from flask import request, jsonify
from oauth2 import get_current_user
from database import get_db
from models import Quiz, QuizAttempt, Question
from sqlalchemy.exc import DataError, IntegrityError
from datetime import datetime, timedelta
from utils import evaluate_quiz
import pytz
from . import views


@views.route('/users/<int:user_id>/quizzes/<int:quiz_id>/attempts', methods=['POST'], strict_slashes=False)
def create_quiz_attempt(user_id, quiz_id):
    """ Create a new quiz attempt.
    Args:
        user_id (int): The ID of the user.
        quiz_id (int): The ID of the quiz.
    Returns:
        JSON: A JSON response containing a message and the attempt ID.
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
    if user.role != 'student':
        return jsonify({"detail": "Unauthorized access"}), 403
    
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        return jsonify({"detail": "Quiz not found"}), 404

    tz = pytz.UTC
    current_time = datetime.now(tz)
    if quiz.start_time > current_time or quiz.end_time < current_time:
        return jsonify({"detail": "Quiz is not active"}), 400

    existing_attempts = db.query(QuizAttempt).filter(QuizAttempt.user_id == user_id, QuizAttempt.quiz_id == quiz_id).count()
    if existing_attempts >= quiz.max_attempts:
        return jsonify({"detail": "You have reached the maximum number of attempts"}), 400

    total_participants = db.query(QuizAttempt.user_id).filter(QuizAttempt.quiz_id == quiz_id).distinct().count()

    if quiz.max_participants and total_participants >= quiz.max_participants:
        return jsonify({"detail": "Max participants reached for this quiz"}), 403

    attempt = QuizAttempt(
        user_id=user_id, quiz_id=quiz_id, started_at=datetime.now(),
        ended_at= datetime.now() + timedelta(hours=quiz.duration), score=0.0, is_submitted=False
        )
    db.add(attempt)
    db.commit()

    return jsonify({"message": "Quiz attempt created successfully", "attempt_id": attempt.id}), 201

@views.route('/users/<int:user_id>/quizzes/<int:quiz_id>/attempts/<int:attempt_id>/update', methods=['PUT'], strict_slashes=False)
def update_quiz_attempt(user_id, quiz_id, attempt_id):
    """ Update a quiz attempt.
    Args:
        user_id (int): The ID of the user.
        quiz_id (int): The ID of the quiz.
        attempt_id (int): The ID of the quiz attempt.
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
    
    attempt = db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id, QuizAttempt.user_id == user_id, QuizAttempt.quiz_id == quiz_id).first()
    if not attempt:
        return jsonify({"detail": "Attempt not found"}), 404
    if attempt.is_submitted:
        return jsonify({"detail": "Attempt has already been submitted and cannot be updated"}), 400

    data = request.json

    try:
        if user.role == 'teacher':
            attempt.score = data['score']
        attempt.is_submitted = data['is_submitted']
        db.commit()
        return jsonify({"message": "Attempt updated successfully"}), 200

    except [DataError, IntegrityError]:
        db.rollback()
        return jsonify({"detail": "Database error occurred"}), 500

@views.route('/users/<int:user_id>/quizzes/<int:quiz_id>/attempts/<int:attempt_id>', methods=['GET'], strict_slashes=False)
def get_one_quiz_attempt(user_id, quiz_id, attempt_id):
    """ Get a quiz attempt.
    Args:
        user_id (int): The ID of the user.
        quiz_id (int): The ID of the quiz.
        attempt_id (int): The ID of the quiz attempt.
    Returns:
        JSON: A JSON response containing the quiz attempt details.
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
    if user.role != 'student':
        return jsonify({"detail": "Unauthorized access"}), 403

    attempt = db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id, QuizAttempt.user_id == user_id, QuizAttempt.quiz_id == quiz_id).first()
    if not attempt:
        return jsonify({"detail": "Attempt not found"}), 404

    return jsonify({
        "id": attempt.id, "user_id": attempt.user_id, "quiz_id": attempt.quiz_id,
        "started_at": attempt.started_at, "ended_at": attempt.ended_at,
        "score": attempt.score, "is_submitted": attempt.is_submitted
    }), 200

@views.route('/users/<int:user_id>/quizzes/<int:quiz_id>/attempts/<int:attempt_id>/submit', methods=['POST'], strict_slashes=False)
def submit_quiz_attempt(user_id, quiz_id, attempt_id):
    """ Submit a quiz attempt.
    Args:
        user_id (int): The ID of the user.
        quiz_id (int): The ID of the quiz.
        attempt_id (int): The ID of the quiz attempt.
    Returns:
        JSON: A JSON response containing a message and the total score.
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
    if user.role != 'student':
        return jsonify({"detail": "Unauthorized access"}), 403

    attempt = db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id, QuizAttempt.user_id == user_id, QuizAttempt.quiz_id == quiz_id).first()
    if not attempt:
        return jsonify({"detail": "Attempt not found"}), 404

    data = request.json

    if data.get('is_submitted') is None:
        return jsonify({"detail": "is_submitted is required"}), 400
    
    if data['is_submitted'] is not True:
        return jsonify({"detail": "is_submitted must be true"}), 400
    
    if attempt.is_submitted:
        return jsonify({"detail": "Attempt has already been submitted"}), 400

    total_score = evaluate_quiz(attempt_id)

    try:
        attempt.score = total_score
        attempt.is_submitted = True
        db.commit()
    except DataError:
        db.rollback()
        return jsonify({"detail": "Database error occurred"}), 500

    return jsonify({"message": "Quiz attempt submitted successfully", "Score": attempt.score}), 200

@views.route('/users/<int:user_id>/quizzes/<int:quiz_id>/attempts/<int:attempt_id>/delete', methods=['DELETE'], strict_slashes=False)
def delete_quiz_attempt(user_id, quiz_id, attempt_id):
    """ Delete a quiz attempt.
    Args:
        user_id (int): The ID of the user.
        quiz_id (int): The ID of the quiz.
        attempt_id (int): The ID of the quiz attempt.
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
    if user.role != 'student':
        return jsonify({"detail": "Unauthorized access"}), 403

    attempt = db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id, QuizAttempt.user_id == user_id, QuizAttempt.quiz_id == quiz_id).first()
    if not attempt:
        return jsonify({"detail": "Attempt not found"}), 404

    db.delete(attempt)
    db.commit()
    return jsonify({"message": "Attempt deleted successfully"}), 200

@views.route('/users/<int:user_id>/quizzes/<int:quiz_id>/attempts/', methods=['GET'], strict_slashes=False)
def get_all_quiz_attempts(user_id, quiz_id):
    """ Get all quiz attempts.
    Args:
        user_id (int): The ID of the user.
        quiz_id (int): The ID of the quiz.
    Returns:
        JSON: A JSON response containing the quiz attempts.
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
    if user.role == 'teacher':
        attempts = db.query(QuizAttempt).filter(QuizAttempt.quiz_id == quiz_id).all()
    if user.role == 'student':
        attempts = db.query(QuizAttempt).filter(QuizAttempt.user_id == user_id, QuizAttempt.quiz_id == quiz_id).all()

    if not attempts:
        return jsonify({"detail": "Attempt not found"}), 404

    response_data = []
    for attempt in attempts:
        response_data.append({
            "id": attempt.id, "user_id": attempt.user_id, "quiz_id": attempt.quiz_id,
            "started_at": attempt.started_at, "ended_at": attempt.ended_at,
            "score": attempt.score, "is_submitted": attempt.is_submitted
        })

    return jsonify(response_data), 200

@views.route('/users/<int:user_id>/quizzes/<int:quiz_id>/attempts/<int:attempt_id>/questions', methods=['GET'], strict_slashes=False)
def get_all_questions_in_attempt(user_id, quiz_id, attempt_id):
    """ Get all questions in a quiz attempt.
    Args:
        user_id (int): The ID of the user.
        quiz_id (int): The ID of the quiz.
        attempt_id (int): The ID of the quiz attempt.
    Returns:
        JSON: A JSON response containing the questions.
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
    if user.role == 'student':
        attempt = db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id, QuizAttempt.user_id == user_id, QuizAttempt.quiz_id == quiz_id).first()
    if user.role == 'teacher':
        attempt = db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id, QuizAttempt.quiz_id == quiz_id).first()

    if not attempt:
        return jsonify({"detail": "Attempt not found"}), 404

    questions = db.query(Question).filter(Question.quiz_id == quiz_id).all()
    if not questions:
        return jsonify({"detail": "Question not found"}), 404

    response_data = []
    for question in questions:
        response_data.append({
            "id": question.id, "content": question.content,
            "type": question.type, "points": question.points,
            "created_at": question.created_at, "updated_at": question.updated_at,
            "question_type": question.question_type
        })

    return jsonify(response_data), 200
