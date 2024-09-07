from flask import Blueprint, request, jsonify
from oauth2 import get_current_user
from database import get_db
from models import Quiz, Question, QuizAttempt, QuestionBank
from sqlalchemy.exc import DataError
from datetime import datetime


views = Blueprint('views', __name__)


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

    try:
        new_quiz = Quiz(
            title=data['title'], description=data['description'],
            creator_id=user.id, start_time=start_time,
            end_time=end_time, duration=data['duration'],
            max_attempts=data['max_attempts'], max_participants=data['max_participants'],
            is_published=data['is_published']
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
        return jsonify({"detail": "Quiz not found"}), 404

    response_data = []
    for quiz in quizzes:
        response_data.append({
            "id": quiz.id, "title": quiz.title,
            "description": quiz.description, "start_time": quiz.start_time,
            "end_time": quiz.end_time, "duration": quiz.duration,
            "max_attempts": quiz.max_attempts, "max_participants": quiz.max_participants,
            "is_published": quiz.is_published, "created_at": quiz.created_at,
            "updated_at": quiz.updated_at, "questions": [
                {"id":q.id,"content":q.content, "type":q.type, "points":q.points, "order":q.order}
                for q in quiz.questions
                ],
            "attempts": [a.id for a in quiz.attempts]
        })

    return jsonify(response_data), 200 

@views.route('/users/<int:user_id>/quizzes/<int:quiz_id>', methods=['GET'], strict_slashes=False)
def get_one_quiz(user_id, quiz_id):
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
    question = db.query(Question).filter(Question.quiz_id == quiz_id).all()
    attempts = db.query(QuizAttempt).filter(QuizAttempt.quiz_id == quiz_id).all()
    if not quiz:
        return jsonify({"detail": "Quiz not found"}), 404

    return jsonify({
        "id": quiz.id, "title": quiz.title, "description": quiz.description,
        "start_time": quiz.start_time, "end_time": quiz.end_time, "duration": quiz.duration,
        "max_attempts": quiz.max_attempts, "max_participants": quiz.max_participants,
        "is_published": quiz.is_published, "created_at": quiz.created_at,
        "updated_at": quiz.updated_at, "questions": [
                {"id":q.id,"content":q.content, "type":q.type, "points":q.points, "order":q.order}
                for q in quiz.questions
                ],
        "attempts": [a.id for a in attempts]
    }), 200

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

@views.route('/users/<int:user_id>/quizzes/<int:quiz_id>/questions', methods=['POST'], strict_slashes=False)
def create_question(user_id, quiz_id):
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
    
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id, Quiz.creator_id == user_id).first()
    if not quiz:
        return jsonify({"detail": "Quiz not found"}), 404

    data = request.json
    new_question = Question(
        quiz_id=quiz_id, content=data['content'],
        type=data['type'], points=data['points'],
        order=data['order']
    )
    db.add(new_question)
    db.commit()

    return jsonify({"message": "Question created successfully", "question_id": new_question.id}), 201

@views.route('/users/<int:user_id>/quizzes/<int:quiz_id>/questions/<int:question_id>', methods=['GET'], strict_slashes=False)
def get_one_question(user_id, quiz_id, question_id):
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
    
    question = db.query(Question).filter(Question.id == question_id, Question.quiz_id == quiz_id).first()
    if not question:
        return jsonify({"detail": "Question not found"}), 404

    return jsonify({
        "id": question.id, "content": question.content,
        "type": question.type, "points": question.points,
        "order": question.order, "created_at": question.created_at,
        "updated_at": question.updated_at
    }), 200

@views.route('/users/<int:user_id>/quizzes/<int:quiz_id>/questions/', methods=['Get'], strict_slashes=False)
def get_all_questions(user_id, quiz_id):
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
    
    questions = db.query(Question).filter(Question.quiz_id == quiz_id).all()
    if not questions:
        return jsonify({"detail": "Question not found"}), 404

    response_data = []
    for question in questions:
        response_data.append({
            "id": question.id, "content": question.content,
            "type": question.type, "points": question.points,
            "order": question.order
        })

    return jsonify(response_data), 200

@views.route('/users/<int:user_id>/quizzes/<int:quiz_id>/questions/<int:question_id>/update', methods=['PUT'], strict_slashes=False)
def update_question(user_id, quiz_id, question_id):
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
    
    question = db.query(Question).filter(Question.id == question_id, Question.quiz_id == quiz_id).first()
    if not question:
        return jsonify({"detail": "Question not found"}), 404

    data = request.json
    try:
        question.content = data['content']
        question.type = data['type']
        question.points = data['points']
        question.order = data['order']
        db.commit()
        return jsonify({"message": "Question updated successfully"}), 200
    
    except DataError:
        db.rollback()
        return jsonify({"detail": "Database error occurred"}), 500

@views.route('/users/<int:user_id>/quizzes/<int:quiz_id>/questions/<int:question_id>/delete', methods=['DELETE'], strict_slashes=False)
def delete_question(user_id, quiz_id, question_id):
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
    
    question = db.query(Question).filter(Question.id == question_id, Question.quiz_id == quiz_id).first()
    if not question:
        return jsonify({"detail": "Question not found"}), 404

    db.delete(question)
    db.commit()
    return jsonify({"message": "Question deleted successfully"}), 200

@views.route('/users/<int:user_id>/question_bank', methods=['POST'], strict_slashes=False)
def create_question_bank(user_id):
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
    new_question_bank = QuestionBank(
        creator_id=user_id, title=data['title'],
        description=data['description']
    )
    db.add(new_question_bank)
    db.commit()

    return jsonify({"message": "Question bank created successfully", "question_bank_id": new_question_bank.id}), 201

@views.route('/users/<int:user_id>/question_bank/<int:question_bank_id>/update', methods=['PUT'], strict_slashes=False)
def update_question_bank(user_id, question_bank_id):
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
    try:
        question_bank.title = data['title']
        question_bank.description = data['description']
        db.commit()
        return jsonify({"message": "Question bank updated successfully"}), 200
    
    except DataError:
        db.rollback()
        return jsonify({"detail": "Database error occurred"}), 500

@views.route('/users/<int:user_id>/question_bank/<int:question_bank_id>/delete', methods=['DELETE'], strict_slashes=False)
def delete_question_bank(user_id, question_bank_id):
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

    db.delete(question_bank)
    db.commit()
    return jsonify({"message": "Question bank deleted successfully"}), 200

@views.route('/users/<int:user_id>/question_bank', methods=['GET'], strict_slashes=False)
def get_all_question_banks(user_id):
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

    question_banks = db.query(QuestionBank).filter(QuestionBank.creator_id == user_id).all()

    if not question_banks:
        return jsonify({"detail": "Question bank not found"}), 404
    
    response_data = []
    for question_bank in question_banks:
        response_data.append({
            "id": question_bank.id, "title": question_bank.title,
            "description": question_bank.description, "created_at": question_bank.created_at,
            "updated_at": question_bank.updated_at, "questions": [
                {"id":q.id,"content":q.content, "type":q.type, "points":q.points, "order":q.order}
                for q in question_bank.questions
                ]
        })

    return jsonify(response_data), 200

@views.route('/users/<int:user_id>/question_bank/<int:question_bank_id>', methods=['GET'], strict_slashes=False)
def get_one_question_bank(user_id, question_bank_id):
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
        "id": question_back.id, "title": question_back.title,
        "description": question_back.description, "created_at": question_back.created_at,
        "updated_at": question_back.updated_at, "questions": [
                {"id":q.id,"content":q.content, "type":q.type, "points":q.points, "order":q.order}
                for q in question_back.questions
                ]
    }), 200

@views.route('/users/<int:user_id>/question_banck/<int:question_bank_id>/questions', methods=['POST'], strict_slashes=False)
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
    new_question = Question(
        quiz_banks_id=question_bank_id, content=data['content'],
        type=data['type'], points=data['points']
    )
    db.add(new_question)
    db.commit()

    return jsonify({"message": "Question added to question bank successfully", "question_id": new_question.id}), 201

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
    try:
        question.content = data['content']
        question.type = data['type']
        question.points = data['points']
        db.commit()
        return jsonify({"message": "Question updated successfully"}), 200
    
    except DataError:
        db.rollback()
        return jsonify({"detail": "Database error occurred"}), 500

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
        response_data.append({
            "id": question.id, "content": question.content,
            "type": question.type, "points": question.points
        })

    return jsonify(response_data), 200
