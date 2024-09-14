from models import Question, QuizAttempt, CorrectAnswer, Question
from database import get_db
import random


def evaluate_quiz(quiz_attempt_id):
    db = get_db()
    quiz_attempt = db.query(QuizAttempt).filter(QuizAttempt.id == quiz_attempt_id).first()
    
    total_score = 0
    for answer in quiz_attempt.answers:
        question = db.query(Question).filter(Question.id == answer.question_id).first()
        correct_answer = db.query(CorrectAnswer).filter(CorrectAnswer.question_id == question.id).first()
        
        if question.question_type == 'true_false':
            if answer.content == correct_answer.correct_answer:
                answer.points_awarded = question.points
                total_score += question.points
        elif question.question_type == 'choose':
            if answer.content == correct_answer.correct_answer:
                answer.points_awarded = question.points
                total_score += question.points
        elif question.question_type == 'written':
            if answer.content == correct_answer.correct_answer:
                answer.points_awarded = question.points
                total_score += question.points
        else:
            raise ValueError('Invalid question type')

    return total_score

def generate_verification_code():
    """Generate a 6-digit random verification code."""
    return str(random.randint(100000, 999999))