from flask import Blueprint, request, jsonify
from oauth2 import get_current_user
from database import get_db
from models import Quiz, Question, QuizAttempt, QuestionBank, CorrectAnswer, Answer
from sqlalchemy.exc import DataError, IntegrityError
from datetime import datetime, timedelta
from utils import evaluate_quiz
from sqlalchemy import func
import pytz

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
    if not quiz:
        return jsonify({"detail": "Quiz not found"}), 404

    questions = db.query(Question).filter(Question.quiz_id == quiz_id).all()
    attempts = db.query(QuizAttempt).filter(QuizAttempt.quiz_id == quiz_id).all()

    response_data = {
        "id": quiz.id, "title": quiz.title, "description": quiz.description,
        "start_time": quiz.start_time, "end_time": quiz.end_time, "duration": quiz.duration,
        "max_attempts": quiz.max_attempts, "max_participants": quiz.max_participants,
        "is_published": quiz.is_published, "created_at": quiz.created_at,
        "updated_at": quiz.updated_at, "quiz_type": quiz.quiz_type, "questions": [
            {"id": q.id, "content": q.content, "question_type": q.question_type, "points": q.points, "order": q.order}
            for q in questions
        ],
        "attempts": [a.id for a in attempts]
    }

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

    if data['question_type'] not in ['true_false', 'choose', 'written']:
        return jsonify({"detail": "Invalid question type"}), 400

    if quiz.quiz_type == 'mcq' and data['question_type'] == 'written':
        return jsonify({"detail": "Invalid question type for this quiz"}), 400
    elif quiz.quiz_type == 'written' and (data['question_type'] == 'true_false' or data['question_type'] == 'choose'):
        return jsonify({"detail": "Invalid question type for this quiz"}), 400

    if data.get('question_type') == 'true_false' or data.get('question_type') == 'choose':
        correct_answer_data = data.get('correct_answer')
        if not correct_answer_data:
            return jsonify({"detail": "Correct answer is required"}), 400

    for question in quiz.questions:
        if question.order == data['order']:
            return jsonify({"detail": "Invalid question order"}), 400

    new_question = Question(
        quiz_id=quiz_id, content=data['content'],
        question_type=data['question_type'], points=data['points'],
        order=data['order']
    )

    db.add(new_question)
    db.commit()

    if new_question.question_type == 'true_false' or new_question.question_type == 'choose':
        correct_answer = CorrectAnswer(
            question_id=new_question.id,
            correct_answer=correct_answer_data
        )
        db.add(correct_answer)
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

    response_data = {
        "id": question.id,
        "content": question.content,
        "points": question.points,
        "order": question.order,
        "created_at": question.created_at,
        "updated_at": question.updated_at,
        "question_type": question.question_type
    }

    if question.question_type in ['true_false', 'choose']:
        correct_answer = db.query(CorrectAnswer).filter(CorrectAnswer.question_id == question_id).first()
        if correct_answer:
            response_data["correct_answer"] = correct_answer.correct_answer

    return jsonify(response_data), 200

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
        question_data = {
            "id": question.id,
            "content": question.content,
            "points": question.points,
            "order": question.order,
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

    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        return jsonify({"detail": "Quiz not found"}), 404

    data = request.json
    
    if data['question_type'] not in ['true_false', 'choose', 'written']:
        return jsonify({"detail": "Invalid question type"}), 400

    if quiz.quiz_type == 'mcq' and data['question_type'] == 'written':
        return jsonify({"detail": "Invalid question type for this quiz"}), 400
    elif quiz.quiz_type == 'written' and data['question_type'] == 'true_false' or data['question_type'] == 'choose':
        return jsonify({"detail": "Invalid question type for this quiz"}), 400

    try:
        question.content = data['content']
        question.points = data['points']

        if data['order'] != question.order:
            for q in quiz.questions:
                if q.order == data['order']:
                    return jsonify({"detail": "Invalid question order"}), 400
            question.order = data['order']

        question.order = data['order']
        question.question_type = data['question_type']

        if question.question_type == 'true_false' or question.question_type == 'choose':
            correct_answer_data = data.get('correct_answer')
            if not correct_answer_data:
                return jsonify({"detail": "Correct answer is required"}), 400

            correct_answer = db.query(CorrectAnswer).filter(CorrectAnswer.question_id == question_id).first()
            if correct_answer:
                correct_answer.correct_answer = correct_answer_data
            else:
                new_correct_answer = CorrectAnswer(
                    question_id=question_id,
                    correct_answer=correct_answer_data
                )
                db.add(new_correct_answer)
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
def get_one_question_in_bank(user_id, question_bank_id, question_id):
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

@views.route('/users/<int:user_id>/quizzes/<int:quiz_id>/attempts', methods=['POST'], strict_slashes=False)
def create_quiz_attempt(user_id, quiz_id):
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

@views.route('/users/<int:user_id>/quizzes/<int:quiz_id>/attempts/<int:attempt_id>/submit', methods=['POST'], strict_slashes=False)
def submit_quiz_attempt(user_id, quiz_id, attempt_id):
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

@views.route('/users/<int:user_id>/quizzes/<int:quiz_id>/attempts/<int:attempt_id>/questions', methods=['GET'], strict_slashes=False)
def get_all_questions_in_attempt(user_id, quiz_id, attempt_id):
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

@views.route('/users/<int:user_id>/quizzes/<int:quiz_id>/attempts/', methods=['GET'], strict_slashes=False)
def get_all_quiz_attempts(user_id, quiz_id):
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

@views.route('/users/<int:user_id>/quizzes/<int:quiz_id>/attempts/<int:attempt_id>/evaluate', methods=['GET'], strict_slashes=False)
def evaluate_quiz_attempt(user_id, quiz_id, attempt_id):
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

