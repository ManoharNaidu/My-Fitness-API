from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload

from app.api.utils import serialize_session
from app.db import get_db
from app.deps import get_current_user
from app.models import SessionExercise, SessionSet, User, WorkoutSessionDB
from app.schemas import SessionPublic, SessionStartRequest, SessionUpdateRequest

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _apply_session_exercises(session_obj: WorkoutSessionDB, exercises_in: list):
    session_obj.exercises.clear()
    for ex in exercises_in:
        ex_db = SessionExercise(exercise_id=ex.exercise_id, sort_order=ex.sort_order)
        ex_db.sets = [
            SessionSet(
                set_order=s.set_order,
                reps=s.reps,
                weight=s.weight,
                completed=s.completed,
                set_type=s.set_type,
            )
            for s in ex.sets
        ]
        session_obj.exercises.append(ex_db)


@router.post("/start", response_model=SessionPublic, status_code=status.HTTP_201_CREATED)
def start_session(
    payload: SessionStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session_obj = WorkoutSessionDB(
        user_id=current_user.id,
        template_id=payload.template_id,
        template_name_snapshot=payload.template_name_snapshot or "Quick Workout",
        notes=payload.notes,
        status="active",
    )
    _apply_session_exercises(session_obj, payload.exercises)
    db.add(session_obj)
    db.commit()
    db.refresh(session_obj)
    session_obj = (
        db.query(WorkoutSessionDB)
        .options(selectinload(WorkoutSessionDB.exercises).selectinload(SessionExercise.sets))
        .filter(WorkoutSessionDB.id == session_obj.id)
        .first()
    )
    return serialize_session(session_obj)


@router.patch("/{session_id}", response_model=SessionPublic)
def update_session(
    session_id: int,
    payload: SessionUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session_obj = (
        db.query(WorkoutSessionDB)
        .options(selectinload(WorkoutSessionDB.exercises).selectinload(SessionExercise.sets))
        .filter(WorkoutSessionDB.id == session_id, WorkoutSessionDB.user_id == current_user.id)
        .first()
    )
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    if session_obj.status != "active":
        raise HTTPException(status_code=400, detail="Only active session can be updated")

    if payload.notes is not None:
        session_obj.notes = payload.notes
    if payload.exercises is not None:
        _apply_session_exercises(session_obj, payload.exercises)

    db.add(session_obj)
    db.commit()
    db.refresh(session_obj)
    return serialize_session(session_obj)


@router.post("/{session_id}/finish", response_model=SessionPublic)
def finish_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session_obj = (
        db.query(WorkoutSessionDB)
        .options(selectinload(WorkoutSessionDB.exercises).selectinload(SessionExercise.sets))
        .filter(WorkoutSessionDB.id == session_id, WorkoutSessionDB.user_id == current_user.id)
        .first()
    )
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    if session_obj.status != "active":
        raise HTTPException(status_code=400, detail="Session already completed/cancelled")

    session_obj.status = "completed"
    session_obj.ended_at = datetime.utcnow()
    session_obj.duration_seconds = int(
        (session_obj.ended_at - session_obj.started_at).total_seconds()
    )
    db.add(session_obj)
    db.commit()
    db.refresh(session_obj)
    return serialize_session(session_obj)


@router.get("", response_model=list[SessionPublic])
def list_sessions(
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    template_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = (
        db.query(WorkoutSessionDB)
        .options(selectinload(WorkoutSessionDB.exercises).selectinload(SessionExercise.sets))
        .filter(WorkoutSessionDB.user_id == current_user.id)
    )
    if from_date:
        q = q.filter(WorkoutSessionDB.started_at >= from_date)
    if to_date:
        q = q.filter(WorkoutSessionDB.started_at <= to_date)
    if template_id:
        q = q.filter(WorkoutSessionDB.template_id == template_id)
    sessions = q.order_by(WorkoutSessionDB.started_at.desc()).all()
    return [serialize_session(s) for s in sessions]


@router.get("/{session_id}", response_model=SessionPublic)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session_obj = (
        db.query(WorkoutSessionDB)
        .options(selectinload(WorkoutSessionDB.exercises).selectinload(SessionExercise.sets))
        .filter(WorkoutSessionDB.id == session_id, WorkoutSessionDB.user_id == current_user.id)
        .first()
    )
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    return serialize_session(session_obj)
