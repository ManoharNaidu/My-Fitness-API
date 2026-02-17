from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import Exercise, User
from app.schemas import ExerciseCreate, ExercisePublic, ExerciseUpdate

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("", response_model=list[ExercisePublic])
def list_exercises(
    query: str | None = Query(default=None),
    muscle: str | None = Query(default=None),
    equipment: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Exercise).filter(
        or_(Exercise.owner_user_id.is_(None), Exercise.owner_user_id == current_user.id)
    )
    if query:
        q = q.filter(Exercise.name.ilike(f"%{query}%"))
    if muscle:
        q = q.filter(Exercise.primary_muscle.ilike(f"%{muscle}%"))
    if equipment:
        q = q.filter(Exercise.equipment.ilike(f"%{equipment}%"))
    return [ExercisePublic.model_validate(x) for x in q.order_by(Exercise.name).all()]


@router.get("/{exercise_id}", response_model=ExercisePublic)
def get_exercise(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exercise = db.get(Exercise, exercise_id)
    if not exercise or (
        exercise.owner_user_id is not None and exercise.owner_user_id != current_user.id
    ):
        raise HTTPException(status_code=404, detail="Exercise not found")
    return ExercisePublic.model_validate(exercise)


@router.post("", response_model=ExercisePublic, status_code=status.HTTP_201_CREATED)
def create_exercise(
    payload: ExerciseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exercise = Exercise(
        owner_user_id=current_user.id,
        name=payload.name,
        primary_muscle=payload.primary_muscle,
        equipment=payload.equipment,
        is_custom=True,
    )
    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    return ExercisePublic.model_validate(exercise)


@router.patch("/{exercise_id}", response_model=ExercisePublic)
def update_exercise(
    exercise_id: int,
    payload: ExerciseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exercise = db.get(Exercise, exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    if exercise.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot edit global exercise")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(exercise, field, value)

    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    return ExercisePublic.model_validate(exercise)


@router.delete("/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exercise(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exercise = db.get(Exercise, exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    if exercise.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot delete global exercise")
    db.delete(exercise)
    db.commit()
