import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(Text, nullable=False)
    option_a = Column(String(500), nullable=False)
    option_b = Column(String(500), nullable=False)
    option_c = Column(String(500), nullable=False)
    option_d = Column(String(500), nullable=False)
    correct_answer = Column(String(1), nullable=False)
    concept = Column(String(100), nullable=False)
    difficulty = Column(String(20), nullable=False)
    ideal_time_seconds = Column(Integer, nullable=False, default=60)
    trap_type = Column(String(100), nullable=True)
    numeric_answer = Column(Float, nullable=True)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    attempts = relationship("TestAttempt", back_populates="user")


class TestAttempt(Base):
    __tablename__ = "test_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    raw_score = Column(Integer, nullable=True)
    predicted_range = Column(String(50), nullable=True)
    score_ceiling = Column(String(50), nullable=True)
    ai_report = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    responses = relationship("Response", back_populates="attempt")
    metrics = relationship("DerivedMetrics", back_populates="attempt", uselist=False)
    user = relationship("User", back_populates="attempts")


class Response(Base):
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("test_attempts.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    selected_answer = Column(String(1), nullable=True)
    correct = Column(Boolean, nullable=False, default=False)
    confidence_level = Column(String(20), nullable=True)
    time_taken_seconds = Column(Float, nullable=True)
    start_delay_seconds = Column(Float, nullable=True)
    answer_changed = Column(Boolean, default=False)
    change_direction = Column(String(30), nullable=True)
    numeric_distance_from_correct = Column(Float, nullable=True)
    attempt = relationship("TestAttempt", back_populates="responses")
    question = relationship("Question")


class DerivedMetrics(Base):
    __tablename__ = "derived_metrics"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("test_attempts.id"), nullable=False, unique=True)
    carelessness_flag = Column(Boolean, default=False)
    guess_probability = Column(Float, default=0.0)
    endurance_index = Column(Float, default=0.0)
    momentum_curve = Column(JSON, nullable=True)
    efficiency_projection = Column(Float, nullable=True)
    trap_sensitivity = Column(JSON, nullable=True)
    precision_ratio = Column(Float, nullable=True)
    decision_volatility = Column(String(50), nullable=True)
    cognitive_start_speed = Column(Float, nullable=True)
    accuracy_by_difficulty = Column(JSON, nullable=True)
    avg_time_deviation = Column(Float, nullable=True)
    total_score = Column(Integer, default=0)
    attempt = relationship("TestAttempt", back_populates="metrics")
