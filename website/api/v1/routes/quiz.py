from flask import request, jsonify
from oauth2 import get_current_user
from database import get_db
from models import Quiz, Question, QuizAttempt, CorrectAnswer
from sqlalchemy.exc import DataError
from datetime import datetime
from . import views

@views.route('/users/<int:user_id>/quizzes', methods=['POST'], strict_slashes=False)
def create_quiz(user_id):
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

    try:
        start_time = datetime.strptime(data['start_time'], '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(data['end_time'], '%Y-%m-%d %H:%M:%S')
    except ValueError as e:
        return jsonify({"detail": f"Invalid datetime format: {e}"}), 400

    quiz_type=data['quiz_type']
    if quiz_type not in ['mcq', 'mixed', 'written']:
        return jsonify({"detail": "Invalid quiz type"}), 400
    
    try:
        new_quiz = Quiz(
            title=data['title'], description=data['description'],
            creator_id=user.id, start_time=start_time,
            end_time=end_time, duration=data['duration'],
            max_attempts=data['max_attempts'], max_participants=data['max_participants'],
            is_published=data['is_published'], quiz_type=quiz_type
        )
        db.add(new_quiz)
        db.commit()
        return jsonify({"message": "Quiz created successfully", "quiz_id": new_quiz.id}), 201
    
    except DataError:
        db.rollback()
        return jsonify({"detail": "Database error occurred"}), 500

@views.route('/users/<int:user_id>/quizzes/', methods=['GET'], strict_slashes=False)
def get_all_quizzes(user_id):
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

    quizzes = (
        db.query(Quiz)
        .outerjoin(Question, Quiz.id == Question.quiz_id)
        .outerjoin(QuizAttempt, Quiz.id == QuizAttempt.quiz_id)
        .filter(Quiz.creator_id == user_id)
        .all()
    )
    
    if not quizzes:
        return jsonify({"detail": "No quizzes found"}), 404

    response_data = []
    for quiz in quizzes:
        quiz_data = {
            "id": quiz.id, "title": quiz.title, "description": quiz.description,
            "start_time": quiz.start_time, "end_time": quiz.end_time, "duration": quiz.duration,
            "max_attempts": quiz.max_attempts, "max_participants": quiz.max_participants,
            "is_published": quiz.is_published, "created_at": quiz.created_at,
            "updated_at": quiz.updated_at, "quiz_type": quiz.quiz_type, "questions": [],
            "attempts": [a.id for a in quiz.attempts]
        }

        for q in quiz.questions:
            question_data = {
                "id": q.id, "content": q.content, "question_type": q.question_type, "points": q.points, "order": q.order
            }
            if q.question_type in ['true_false', 'choose']:
                correct_answer = db.query(CorrectAnswer).filter(CorrectAnswer.question_id == q.id).first()
                if correct_answer:
                    question_data["correct_answer"] = correct_answer.correct_answer
            
            quiz_data["questions"].append(question_data)
        
        response_data.append(quiz_data)

    return jsonify(response_data), 200

@views.route('/users/<int:user_id>/quizzes/<int:quiz_id>', methods=['GET'], strict_slashes=False)
def get_one_quiz(user_id, quiz_id, num_page=1, page_size=1):
    start = (num_page - 1) * page_size
    end = start + page_size
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
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            return jsonify({"detail": "Quiz not found"}), 404
        questions = db.query(Question).filter(Question.quiz_id == quiz_id).all()
        attempts = db.query(QuizAttempt).filter(QuizAttempt.quiz_id == quiz_id).all()
    else:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id, Quiz.is_published == True).first()
        if not quiz:
            return jsonify({"detail": "Quiz not found"}), 404
        questions = db.query(Question).filter(Question.quiz_id == quiz_id).slice(start, end).all()

    response_data = {
        "id": quiz.id, "title": quiz.title, "description": quiz.description,
        "start_time": quiz.start_time, "end_time": quiz.end_time, "duration": quiz.duration,
        "max_attempts": quiz.max_attempts, "max_participants": quiz.max_participants,
        "is_published": quiz.is_published, "created_at": quiz.created_at,
        "updated_at": quiz.updated_at, "quiz_type": quiz.quiz_type, "questions": [
            {"id": q.id, "content": q.content, "question_type": q.question_type, "points": q.points, "order": q.order}
            for q in questions
        ],
        "attempts": [a.id for a in attempts] if user.role == 'teacher' else None
    }

    if user.role == 'teacher':
        for q in response_data["questions"]:
            if q["question_type"] in ['true_false', 'choose']:
                correct_answer = db.query(CorrectAnswer).filter(CorrectAnswer.question_id == q["id"]).first()
                if correct_answer:
                    q["correct_answer"] = correct_answer.correct_answer

    return jsonify(response_data), 200

@views.route('/users/<int:user_id>/quizzes/<int:quiz_id>/update', methods=['PUT'], strict_slashes=False)
def update_quiz(user_id, quiz_id):
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
    
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        return jsonify({"detail": "Quiz not found"}), 404

    data = request.json
    quiz_type=data['quiz_type']
    if quiz_type not in ['mcq', 'mixed', 'written']:
        return jsonify({"detail": "Invalid quiz type"}), 400
    
    questions = db.query(Question).filter(Question.quiz_id == quiz_id).all()

    if questions:
        for question in questions:
            if question.question_type == 'true_false' or question.question_type == 'choose':
                if quiz_type == 'written':
                    return jsonify({"detail": "Invalid quiz type for this quiz"}), 400
            elif question.question_type == 'written':
                if quiz_type == 'mcq':
                    return jsonify({"detail": "Invalid quiz type for this quiz"}), 400

    try:
        start_time = datetime.strptime(data['start_time'], '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(data['end_time'], '%Y-%m-%d %H:%M:%S')
    except ValueError as e:
        return jsonify({"detail": f"Invalid datetime format: {e}"}), 400

    try:
        quiz.title = data['title']
        quiz.description = data['description']
        quiz.start_time = start_time
        quiz.end_time = end_time
        quiz.duration = data['duration']
        quiz.max_attempts = data['max_attempts']
        quiz.max_participants = data['max_participants']
        quiz.is_published = data['is_published']
        quiz.quiz_type = data['quiz_type']
        db.commit()
        return jsonify({"message": "Quiz updated successfully"}), 200
    
    except DataError:
        db.rollback()
        return jsonify({"detail": "Database error occurred"}), 500
    
@views.route('/users/<int:user_id>/quizzes/<int:quiz_id>/delete', methods=['DELETE'], strict_slashes=False)
def delete_quiz(user_id, quiz_id):
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
    
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        return jsonify({"detail": "Quiz not found"}), 404

    db.delete(quiz)
    db.commit()
    return jsonify({"message": "Quiz deleted successfully"}), 200
