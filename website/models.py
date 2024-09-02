from sqlalchemy import (
    Column, Integer, String, Text, Float,
    DateTime, ForeignKey, Boolean, func
)
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(50), nullable=False)
    role = Column(String(50), nullable=False)
    is_blocked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    quizzes = relationship('Quiz', backref='creator', lazy='dynamic')
    quiz_attempts = relationship('QuizAttempt', backref='user', lazy='dynamic')
    question_banks = relationship('QuestionBank', backref='creator', lazy='dynamic')


class Quiz(Base):
    __tablename__ = 'quizzes'
    id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    creator_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    duration = Column(Integer, nullable=False)
    max_attempts = Column(Integer, default=1)
    max_participants = Column(Integer)
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    questions = relationship('Question', backref='quiz',lazy='dynamic', cascade='all, delete-orphan')
    attempts = relationship('QuizAttempt', backref='quiz', lazy='dynamic', cascade='all, delete-orphan')


class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True, nullable=False)
    quiz_id = Column(Integer, ForeignKey('quizzes.id'), nullable=False)
    quiz_banks_id = Column(Integer, ForeignKey('question_banks.id'))
    content = Column(Text, nullable=False)
    type = Column(String(50), nullable=False)
    points = Column(Integer, nullable=False, default=1)
    order = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    answers = relationship('Answer', backref='questions', lazy='dynamic', cascade='all, delete-orphan')


class Answer(Base):
    __tablename__ = 'answers'
    id = Column(Integer, primary_key=True, nullable=False)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False)
    quiz_attemp_id = Column(Integer, ForeignKey('quiz_attempts.id'), nullable=False)
    content = Column(Text)
    is_correct = Column(Boolean)
    points_awarded = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class QuizAttempt(Base):
    __tablename__ = 'quiz_attempts'
    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    quiz_id = Column(Integer, ForeignKey('quizzes.id'), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=False)
    score = Column(Float)
    is_submitted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    answers = relationship('Answer', backref='quiz_attempts', lazy='dynamic', cascade='all, delete-orphan')


class QuestionBank(Base):
    __tablename__ = 'question_banks'
    id = Column(Integer, primary_key=True, nullable=False)
    creator_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(String(127), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    questions = relationship('Question', backref='question_banks', lazy='dynamic', cascade='all, delete-orphan')
