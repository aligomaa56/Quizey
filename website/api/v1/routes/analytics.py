from flask import request, jsonify
from oauth2 import get_current_user
from database import get_db
from models import QuizAttempt
from utils import evaluate_quiz
from . import views


@views.route('/users/<int:user_id>/quizzes/<int:quiz_id>/attempts/<int:attempt_id>/evaluate', methods=['GET'], strict_slashes=False)
def evaluate_quiz_attempt(user_id, quiz_id, attempt_id):
    """ Evaluate a quiz attempt and return the total score.
    Args:
        user_id (int): The ID of the user.
        quiz_id (int): The ID of the quiz.
        attempt_id (int): The ID of the quiz attempt.
    Returns:
        JSON: A JSON response containing the total score.
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

    if user.role != 'teacher':
        attempt = db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id, QuizAttempt.user_id == user_id, QuizAttempt.quiz_id == quiz_id).first()
    if user.role != 'student':
        attempt = db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id, QuizAttempt.quiz_id == quiz_id).first()

    if not attempt:
        return jsonify({"detail": "Attempt not found"}), 404

    total_score = evaluate_quiz(attempt_id)
    return jsonify({"total_score": total_score}), 200
