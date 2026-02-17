from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.deps import get_current_user
from app.models import MealLog, SessionExercise, User, WorkoutSessionDB
from app.schemas import OverviewStats, ProgressPoint

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _range_to_start(range_key: str) -> datetime:
    now = datetime.utcnow()
    mapping = {
        "7d": now - timedelta(days=7),
        "30d": now - timedelta(days=30),
        "12w": now - timedelta(weeks=12),
    }
    return mapping.get(range_key, now - timedelta(days=7))


@router.get("/overview", response_model=OverviewStats)
def overview(
    range: str = Query(default="7d", pattern="^(7d|30d|12w)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from_dt = _range_to_start(range)
    sessions = (
        db.query(WorkoutSessionDB)
        .options(selectinload(WorkoutSessionDB.exercises).selectinload(SessionExercise.sets))
        .filter(
            WorkoutSessionDB.user_id == current_user.id,
            WorkoutSessionDB.status == "completed",
            WorkoutSessionDB.started_at >= from_dt,
        )
        .all()
    )

    total_volume = 0.0
    durations = []
    for s in sessions:
        if s.duration_seconds:
            durations.append(s.duration_seconds)
        for ex in s.exercises:
            for set_ in ex.sets:
                total_volume += set_.weight * set_.reps

    meals = (
        db.query(MealLog)
        .filter(MealLog.user_id == current_user.id, MealLog.eaten_at >= from_dt)
        .all()
    )

    avg_minutes = (sum(durations) / len(durations) / 60) if durations else 0.0
    return OverviewStats(
        range=range,
        completed_workouts=len(sessions),
        total_volume=round(total_volume, 2),
        average_duration_minutes=round(avg_minutes, 2),
        total_calories=sum(m.calories for m in meals),
    )


@router.get("/progression", response_model=list[ProgressPoint])
def progression(
    exercise_id: int,
    metric: str = Query(default="weight", pattern="^(1rm|volume|weight)$"),
    range: str = Query(default="30d", pattern="^(7d|30d|12w)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from_dt = _range_to_start(range)
    sessions = (
        db.query(WorkoutSessionDB)
        .options(selectinload(WorkoutSessionDB.exercises).selectinload(SessionExercise.sets))
        .filter(
            WorkoutSessionDB.user_id == current_user.id,
            WorkoutSessionDB.status == "completed",
            WorkoutSessionDB.started_at >= from_dt,
        )
        .order_by(WorkoutSessionDB.started_at.asc())
        .all()
    )

    points: list[ProgressPoint] = []
    for s in sessions:
        exercise_entries = [x for x in s.exercises if x.exercise_id == exercise_id]
        if not exercise_entries:
            continue
        sets = [st for ex in exercise_entries for st in ex.sets]
        if not sets:
            continue

        if metric == "volume":
            value = sum(st.reps * st.weight for st in sets)
        elif metric == "1rm":
            value = max((st.weight * (1 + st.reps / 30)) for st in sets)
        else:
            value = max(st.weight for st in sets)

        points.append(ProgressPoint(label=s.started_at.strftime("%Y-%m-%d"), value=value))

    return points
