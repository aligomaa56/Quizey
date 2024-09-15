from flask import request, jsonify
from oauth2 import get_current_user
from database import get_db
from models import Quiz, Question, CorrectAnswer
from sqlalchemy.exc import DataError
from . import views


@views.route('/users/<int:user_id>/quizzes/<int:quiz_id>/questions', methods=['POST'], strict_slashes=False)
def create_question(user_id, quiz_id):
    """ Create a new question.
    Args:
        user_id (int): The ID of the user.
        quiz_id (int): The ID of the quiz.
    Returns:
        JSON: A JSON response containing a message and the question ID.
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
    """ Get a question.
    Args:
        user_id (int): The ID of the user.
        quiz_id (int): The ID of the quiz.
        question_id (int): The ID of the question.
    Returns:
        JSON: A JSON response containing the question details.
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
    """ Get all questions in a quiz.
    Args:
        user_id (int): The ID of the user.
        quiz_id (int): The ID of the quiz.
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
    """ Update a question.
    Args:
        user_id (int): The ID of the user.
        quiz_id (int): The ID of the quiz.
        question_id (int): The ID of the question.
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
    """ Delete a question.
    Args:
        user_id (int): The ID of the user.
        quiz_id (int): The ID of the quiz.
        question_id (int): The ID of the question.
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
    if user.role != 'teacher':
        return jsonify({"detail": "Unauthorized access"}), 403
    
    question = db.query(Question).filter(Question.id == question_id, Question.quiz_id == quiz_id).first()
    if not question:
        return jsonify({"detail": "Question not found"}), 404

    db.delete(question)
    db.commit()
    return jsonify({"message": "Question deleted successfully"}), 200

