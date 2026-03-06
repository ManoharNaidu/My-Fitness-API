from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserPublic(BaseModel):
    id: int
    email: EmailStr
    display_name: str
    units: str
    default_rest_seconds: int

    model_config = ConfigDict(from_attributes=True)


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    display_name: str = Field(min_length=2, max_length=120)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class UserPreferencesUpdate(BaseModel):
    units: Literal["kg", "lb"] | None = None
    default_rest_seconds: int | None = Field(default=None, ge=15, le=600)


class ExerciseCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    primary_muscle: str = Field(min_length=2, max_length=80)
    equipment: str = Field(min_length=2, max_length=80)


class ExerciseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    primary_muscle: str | None = Field(default=None, min_length=2, max_length=80)
    equipment: str | None = Field(default=None, min_length=2, max_length=80)


class ExercisePublic(BaseModel):
    id: int
    owner_user_id: int | None
    name: str
    primary_muscle: str
    equipment: str
    is_custom: bool

    model_config = ConfigDict(from_attributes=True)


class TemplateSetIn(BaseModel):
    set_order: int
    target_reps: int = Field(ge=1, le=100)
    target_weight: float = Field(ge=0)
    set_type: str = "normal"


class TemplateExerciseIn(BaseModel):
    exercise_id: int
    sort_order: int = 0
    sets: list[TemplateSetIn] = Field(default_factory=list)


class TemplateCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    notes: str | None = None
    exercises: list[TemplateExerciseIn] = Field(default_factory=list)


class TemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    notes: str | None = None
    exercises: list[TemplateExerciseIn] | None = None


class TemplateSetOut(BaseModel):
    id: int
    set_order: int
    target_reps: int
    target_weight: float
    set_type: str


class TemplateExerciseOut(BaseModel):
    id: int
    exercise_id: int
    sort_order: int
    sets: list[TemplateSetOut]


class TemplatePublic(BaseModel):
    id: int
    user_id: int
    name: str
    notes: str | None
    created_at: datetime
    exercises: list[TemplateExerciseOut]


class SessionSetIn(BaseModel):
    set_order: int
    reps: int = Field(ge=0, le=200)
    weight: float = Field(ge=0)
    completed: bool = False
    set_type: str = "normal"


class SessionExerciseIn(BaseModel):
    exercise_id: int
    sort_order: int = 0
    sets: list[SessionSetIn] = Field(default_factory=list)


class SessionStartRequest(BaseModel):
    template_id: int | None = None
    template_name_snapshot: str | None = None
    notes: str | None = None
    exercises: list[SessionExerciseIn] = Field(default_factory=list)


class SessionUpdateRequest(BaseModel):
    notes: str | None = None
    exercises: list[SessionExerciseIn] | None = None


class SessionSetOut(BaseModel):
    id: int
    set_order: int
    reps: int
    weight: float
    completed: bool
    set_type: str


class SessionExerciseOut(BaseModel):
    id: int
    exercise_id: int
    sort_order: int
    sets: list[SessionSetOut]


class SessionPublic(BaseModel):
    id: int
    user_id: int
    template_id: int | None
    template_name_snapshot: str
    status: str
    started_at: datetime
    ended_at: datetime | None
    duration_seconds: int | None
    notes: str | None
    exercises: list[SessionExerciseOut]


class WorkoutCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    date: datetime
    notes: str | None = None


class WorkoutPublic(BaseModel):
    id: int
    user_id: int
    name: str
    date: datetime
    notes: str | None
    status: str
    duration_seconds: int | None
    exercises: list[SessionExerciseOut]


class WorkoutExerciseAdd(BaseModel):
    exercise_id: int
    sort_order: int = 0


class SetCreate(BaseModel):
    exercise_id: int
    weight: float = Field(ge=0)
    reps: int = Field(ge=0, le=200)
    set_number: int | None = Field(default=None, ge=1)
    rest_time: int | None = Field(default=None, ge=0)
    rpe: float | None = Field(default=None, ge=0, le=10)


class SetPublic(BaseModel):
    id: int
    exercise_id: int
    weight: float
    reps: int
    set_number: int
    created_at: datetime


class MealCreate(BaseModel):
    meal_name: str = Field(min_length=2, max_length=150)
    calories: int = Field(ge=0, le=5000)
    protein_g: float = Field(default=0, ge=0, le=500)
    carbs_g: float = Field(default=0, ge=0, le=1000)
    fats_g: float = Field(default=0, ge=0, le=500)
    eaten_at: datetime | None = None


class MealPublic(BaseModel):
    id: int
    user_id: int
    meal_name: str
    calories: int
    protein_g: float
    carbs_g: float
    fats_g: float
    eaten_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OverviewStats(BaseModel):
    range: str
    completed_workouts: int
    total_volume: float
    average_duration_minutes: float
    total_calories: int


class ProgressPoint(BaseModel):
    label: str
    value: float
