from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(120))
    units: Mapped[str] = mapped_column(String(8), default="kg")
    default_rest_seconds: Mapped[int] = mapped_column(Integer, default=90)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(150), index=True)
    primary_muscle: Mapped[str] = mapped_column(String(80))
    equipment: Mapped[str] = mapped_column(String(80))
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WorkoutTemplate(Base):
    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    exercises: Mapped[list["TemplateExercise"]] = relationship(
        back_populates="template", cascade="all, delete-orphan"
    )


class TemplateExercise(Base):
    __tablename__ = "template_exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("templates.id", ondelete="CASCADE"))
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    template: Mapped[WorkoutTemplate] = relationship(back_populates="exercises")
    sets: Mapped[list["TemplateSet"]] = relationship(
        back_populates="template_exercise", cascade="all, delete-orphan"
    )


class TemplateSet(Base):
    __tablename__ = "template_sets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_exercise_id: Mapped[int] = mapped_column(
        ForeignKey("template_exercises.id", ondelete="CASCADE")
    )
    set_order: Mapped[int] = mapped_column(Integer)
    target_reps: Mapped[int] = mapped_column(Integer)
    target_weight: Mapped[float] = mapped_column(Float)
    set_type: Mapped[str] = mapped_column(String(16), default="normal")

    template_exercise: Mapped[TemplateExercise] = relationship(back_populates="sets")


class WorkoutSessionDB(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    template_id: Mapped[int | None] = mapped_column(ForeignKey("templates.id"), nullable=True)
    template_name_snapshot: Mapped[str] = mapped_column(String(120), default="Quick Workout")
    status: Mapped[str] = mapped_column(String(16), default="active")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    exercises: Mapped[list["SessionExercise"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class SessionExercise(Base):
    __tablename__ = "session_exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"))
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    session: Mapped[WorkoutSessionDB] = relationship(back_populates="exercises")
    sets: Mapped[list["SessionSet"]] = relationship(
        back_populates="session_exercise", cascade="all, delete-orphan"
    )


class SessionSet(Base):
    __tablename__ = "session_sets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_exercise_id: Mapped[int] = mapped_column(
        ForeignKey("session_exercises.id", ondelete="CASCADE")
    )
    set_order: Mapped[int] = mapped_column(Integer)
    reps: Mapped[int] = mapped_column(Integer)
    weight: Mapped[float] = mapped_column(Float)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    set_type: Mapped[str] = mapped_column(String(16), default="normal")

    session_exercise: Mapped[SessionExercise] = relationship(back_populates="sets")


class MealLog(Base):
    __tablename__ = "meal_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    meal_name: Mapped[str] = mapped_column(String(150))
    calories: Mapped[int] = mapped_column(Integer)
    protein_g: Mapped[float] = mapped_column(Float, default=0)
    carbs_g: Mapped[float] = mapped_column(Float, default=0)
    fats_g: Mapped[float] = mapped_column(Float, default=0)
    eaten_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
