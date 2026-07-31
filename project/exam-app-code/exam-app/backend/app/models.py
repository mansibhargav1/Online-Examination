import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey, Integer,
    String, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def gen_uuid() -> str:
    return str(uuid.uuid4())


class Role(str, enum.Enum):
    admin = "admin"
    candidate = "candidate"


class ApplicationStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class AttemptStatus(str, enum.Enum):
    in_progress = "in_progress"
    submitted = "submitted"


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    full_name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20))
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(Role), nullable=False, default=Role.candidate)
    is_active = Column(Boolean, default=True, nullable=False)
    verification_code = Column(String(12))
    created_at = Column(DateTime(timezone=True), default=now_utc)

    attempts = relationship("Attempt", back_populates="user")


class Application(Base):
    __tablename__ = "applications"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    full_name = Column(String(120), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(20), nullable=False)
    dob = Column(String(20))
    address = Column(Text)
    qualification = Column(String(120))
    id_proof_type = Column(String(50))
    id_proof_number = Column(String(60))
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.pending, nullable=False)
    admin_note = Column(Text)
    created_at = Column(DateTime(timezone=True), default=now_utc)


class Exam(Base):
    __tablename__ = "exams"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    instructions = Column(Text)
    seconds_per_question = Column(Integer, default=120, nullable=False)
    marks_correct = Column(Integer, default=4, nullable=False)
    marks_wrong = Column(Integer, default=-1, nullable=False)
    marks_unattempted = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    questions = relationship(
        "Question", back_populates="exam",
        cascade="all, delete-orphan", order_by="Question.order_index",
    )


class Question(Base):
    __tablename__ = "questions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    exam_id = Column(String(36), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    order_index = Column(Integer, default=0, nullable=False)

    exam = relationship("Exam", back_populates="questions")
    options = relationship(
        "Option", back_populates="question",
        cascade="all, delete-orphan", order_by="Option.order_index",
    )


class Option(Base):
    __tablename__ = "options"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    question_id = Column(String(36), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False, nullable=False)
    order_index = Column(Integer, default=0, nullable=False)

    question = relationship("Question", back_populates="options")


class Attempt(Base):
    __tablename__ = "attempts"
    __table_args__ = (UniqueConstraint("user_id", "exam_id", name="uq_user_exam"),)

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    exam_id = Column(String(36), ForeignKey("exams.id"), nullable=False)
    status = Column(Enum(AttemptStatus), default=AttemptStatus.in_progress, nullable=False)
    verified_at = Column(DateTime(timezone=True))
    started_at = Column(DateTime(timezone=True), default=now_utc)
    finished_at = Column(DateTime(timezone=True))
    current_index = Column(Integer, default=0, nullable=False)
    total_score = Column(Integer, default=0, nullable=False)

    user = relationship("User", back_populates="attempts")
    exam = relationship("Exam")
    answers = relationship("Answer", back_populates="attempt", cascade="all, delete-orphan")


class Answer(Base):
    __tablename__ = "answers"
    __table_args__ = (UniqueConstraint("attempt_id", "question_id", name="uq_attempt_question"),)

    id = Column(String(36), primary_key=True, default=gen_uuid)
    attempt_id = Column(String(36), ForeignKey("attempts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    question_id = Column(String(36), ForeignKey("questions.id"), nullable=False)
    selected_option_id = Column(String(36), ForeignKey("options.id"), nullable=True)
    is_correct = Column(Boolean, default=False, nullable=False)
    marks_awarded = Column(Integer, default=0, nullable=False)
    served_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    answered_at = Column(DateTime(timezone=True))
    time_taken_seconds = Column(Integer)

    attempt = relationship("Attempt", back_populates="answers")
    question = relationship("Question")
