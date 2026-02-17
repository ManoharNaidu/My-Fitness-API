from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import MealLog, User
from app.schemas import MealCreate, MealPublic

router = APIRouter(prefix="/nutrition", tags=["nutrition"])


@router.get("/meals", response_model=list[MealPublic])
def list_meals(
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(MealLog).filter(MealLog.user_id == current_user.id)
    if from_date:
        q = q.filter(MealLog.eaten_at >= from_date)
    if to_date:
        q = q.filter(MealLog.eaten_at <= to_date)
    return [MealPublic.model_validate(x) for x in q.order_by(MealLog.eaten_at.desc()).all()]


@router.post("/meals", response_model=MealPublic, status_code=status.HTTP_201_CREATED)
def add_meal(
    payload: MealCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meal = MealLog(
        user_id=current_user.id,
        meal_name=payload.meal_name,
        calories=payload.calories,
        protein_g=payload.protein_g,
        carbs_g=payload.carbs_g,
        fats_g=payload.fats_g,
        eaten_at=payload.eaten_at or datetime.utcnow(),
    )
    db.add(meal)
    db.commit()
    db.refresh(meal)
    return MealPublic.model_validate(meal)
