from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.utils import serialize_session
from app.db import Client, get_supabase
from app.deps import get_current_user
from app.schemas import SessionPublic, SessionStartRequest, SessionUpdateRequest

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _insert_session_exercises(supabase: Client, session_id: int, exercises_in: list):
    for ex in exercises_in:
        ex_row = (
            supabase.table("session_exercises")
            .insert(
                {
                    "session_id": session_id,
                    "exercise_id": ex.exercise_id,
                    "sort_order": ex.sort_order,
                }
            )
            .execute()
        )
        if not ex_row.data:
            continue
        session_exercise_id = ex_row.data[0]["id"]
        if ex.sets:
            supabase.table("session_sets").insert(
                [
                    {
                        "session_exercise_id": session_exercise_id,
                        "set_order": s.set_order,
                        "reps": s.reps,
                        "weight": s.weight,
                        "completed": s.completed,
                        "set_type": s.set_type,
                    }
                    for s in ex.sets
                ]
            ).execute()


def _fetch_session(supabase: Client, session_id: int, user_id: int) -> dict | None:
    response = (
        supabase.table("sessions")
        .select(
            "id,user_id,template_id,template_name_snapshot,status,started_at,ended_at,duration_seconds,notes,session_exercises(id,exercise_id,sort_order,session_sets(id,set_order,reps,weight,completed,set_type))"
        )
        .eq("id", session_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    session_obj = response.data[0] if response.data else None
    if not session_obj:
        return None
    session_obj["exercises"] = [
        {**ex, "sets": ex.get("session_sets") or []}
        for ex in (session_obj.get("session_exercises") or [])
    ]
    return session_obj


@router.post("/start", response_model=SessionPublic, status_code=status.HTTP_201_CREATED)
def start_session(
    payload: SessionStartRequest,
    supabase: Client = Depends(get_supabase),
    current_user: dict = Depends(get_current_user),
):
    created = (
        supabase.table("sessions")
        .insert(
            {
                "user_id": current_user["id"],
                "template_id": payload.template_id,
                "template_name_snapshot": payload.template_name_snapshot
                or "Quick Workout",
                "notes": payload.notes,
                "status": "active",
            }
        )
        .execute()
    )
    if not created.data:
        raise HTTPException(status_code=500, detail="Failed to start session")
    session_id = created.data[0]["id"]
    _insert_session_exercises(supabase, session_id, payload.exercises)
    session_obj = _fetch_session(supabase, session_id, current_user["id"])
    return serialize_session(session_obj)


@router.patch("/{session_id}", response_model=SessionPublic)
def update_session(
    session_id: int,
    payload: SessionUpdateRequest,
    supabase: Client = Depends(get_supabase),
    current_user: dict = Depends(get_current_user),
):
    session_obj = _fetch_session(supabase, session_id, current_user["id"])
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    if session_obj["status"] != "active":
        raise HTTPException(status_code=400, detail="Only active session can be updated")

    updates: dict = {}
    if payload.notes is not None:
        updates["notes"] = payload.notes

    if updates:
        supabase.table("sessions").update(updates).eq("id", session_id).eq(
            "user_id", current_user["id"]
        ).execute()

    if payload.exercises is not None:
        existing_ex = (
            supabase.table("session_exercises")
            .select("id")
            .eq("session_id", session_id)
            .execute()
        )
        for ex in (existing_ex.data or []):
            supabase.table("session_sets").delete().eq(
                "session_exercise_id", ex["id"]
            ).execute()
        supabase.table("session_exercises").delete().eq("session_id", session_id).execute()
        _insert_session_exercises(supabase, session_id, payload.exercises)

    session_obj = _fetch_session(supabase, session_id, current_user["id"])
    return serialize_session(session_obj)


@router.post("/{session_id}/finish", response_model=SessionPublic)
def finish_session(
    session_id: int,
    supabase: Client = Depends(get_supabase),
    current_user: dict = Depends(get_current_user),
):
    session_obj = _fetch_session(supabase, session_id, current_user["id"])
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    if session_obj["status"] != "active":
        raise HTTPException(status_code=400, detail="Session already completed/cancelled")

    ended_at = datetime.utcnow()
    started_at = datetime.fromisoformat(str(session_obj["started_at"]).replace("Z", "+00:00"))
    duration_seconds = int((ended_at - started_at).total_seconds())
    supabase.table("sessions").update(
        {
            "status": "completed",
            "ended_at": ended_at.isoformat(),
            "duration_seconds": duration_seconds,
        }
    ).eq("id", session_id).eq("user_id", current_user["id"]).execute()
    session_obj = _fetch_session(supabase, session_id, current_user["id"])
    return serialize_session(session_obj)


@router.get("", response_model=list[SessionPublic])
def list_sessions(
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    template_id: int | None = Query(default=None),
    supabase: Client = Depends(get_supabase),
    current_user: dict = Depends(get_current_user),
):
    q = (
        supabase.table("sessions")
        .select(
            "id,user_id,template_id,template_name_snapshot,status,started_at,ended_at,duration_seconds,notes,session_exercises(id,exercise_id,sort_order,session_sets(id,set_order,reps,weight,completed,set_type))"
        )
        .eq("user_id", current_user["id"])
    )
    if from_date:
        q = q.gte("started_at", from_date.isoformat())
    if to_date:
        q = q.lte("started_at", to_date.isoformat())
    if template_id:
        q = q.eq("template_id", template_id)
    response = q.order("started_at", desc=True).execute()
    sessions = []
    for s in (response.data or []):
        s["exercises"] = [
            {**ex, "sets": ex.get("session_sets") or []}
            for ex in (s.get("session_exercises") or [])
        ]
        sessions.append(s)
    return [serialize_session(s) for s in sessions]


@router.get("/{session_id}", response_model=SessionPublic)
def get_session(
    session_id: int,
    supabase: Client = Depends(get_supabase),
    current_user: dict = Depends(get_current_user),
):
    session_obj = _fetch_session(supabase, session_id, current_user["id"])
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    return serialize_session(session_obj)
