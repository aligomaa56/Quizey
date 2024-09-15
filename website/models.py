from sqlalchemy import (
    Column, Integer, String, Text, Float,
    DateTime, ForeignKey, Boolean, func, Enum
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import expression


Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=False, index=True)
    last_name = Column(String, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String(50), nullable=False)
    is_blocked = Column(Boolean, server_default=expression.false(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_verified = Column(Boolean, server_default=expression.false(), nullable=False)

    quizzes = relationship('Quiz', back_populates='creator', lazy='dynamic')
    quiz_attempts = relationship('QuizAttempt', back_populates='user', lazy='dynamic')
    question_banks = relationship('QuestionBank', back_populates='creator', lazy='dynamic')

class Quiz(Base):
    __tablename__ = 'quizzes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    creator_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    duration = Column(Integer, nullable=False)
    max_attempts = Column(Integer, default=1, nullable=False)
    max_participants = Column(Integer)
    is_published = Column(Boolean, server_default=expression.false())
    quiz_type = Column(Enum('mcq', 'mixed', 'written', name='quiz_type'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    creator = relationship('User', back_populates='quizzes')
    questions = relationship('Question', back_populates='quiz',lazy='dynamic', cascade='all, delete-orphan')
    attempts = relationship('QuizAttempt', back_populates='quiz', lazy='dynamic', cascade='all, delete-orphan')


class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    quiz_id = Column(Integer, ForeignKey('quizzes.id'))
    quiz_banks_id = Column(Integer, ForeignKey('question_banks.id'))
    content = Column(Text, nullable=False)
    question_type = Column(Enum('true_false', 'choose', 'written', name='type_question'), nullable=False)
    points = Column(Integer, nullable=False, default=1)
    order = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    quiz = relationship('Quiz', back_populates='questions')
    question_bank = relationship("QuestionBank", back_populates="questions")
    answers = relationship('Answer', back_populates='question', lazy='dynamic', cascade='all, delete-orphan')
    correct_answers = relationship('CorrectAnswer', back_populates='question', lazy='dynamic', cascade='all, delete-orphan')

class QuestionBank(Base):
    __tablename__ = 'question_banks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    creator_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(String(127), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    creator = relationship('User', back_populates='question_banks')
    questions = relationship("Question", back_populates="question_bank")

class QuizAttempt(Base):
    __tablename__ = 'quiz_attempts'
    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    quiz_id = Column(Integer, ForeignKey('quizzes.id'), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    score = Column(Float)
    is_submitted = Column(Boolean, server_default=expression.false(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship('User', back_populates='quiz_attempts')
    quiz = relationship('Quiz', back_populates='attempts')
    answers = relationship('Answer', back_populates='quiz_attempt', lazy='dynamic', cascade='all, delete-orphan')

class Answer(Base):
    __tablename__ = 'answers'
    id = Column(Integer, primary_key=True, nullable=False)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False)
    attempt_id = Column(Integer, ForeignKey('quiz_attempts.id'), nullable=False)
    content = Column(Text)
    points_awarded = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    question = relationship('Question', back_populates='answers')
    quiz_attempt = relationship('QuizAttempt', back_populates='answers')

class CorrectAnswer(Base):
    __tablename__ = 'correct_answers'
    id = Column(Integer, primary_key=True, nullable=False)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False)
    correct_answer = Column(Text)
    
    question = relationship('Question', back_populates='correct_answers')
