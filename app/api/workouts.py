from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db import Client, get_supabase
from app.deps import get_current_user
from app.schemas import (
    SessionExerciseOut,
    SessionSetOut,
    WorkoutCreate,
    WorkoutExerciseAdd,
    WorkoutPublic,
)

router = APIRouter(prefix="/workouts", tags=["workouts"])


def _normalize_session(session_obj: dict) -> dict:
    session_obj["exercises"] = [
        {**ex, "sets": ex.get("session_sets") or []}
        for ex in (session_obj.get("session_exercises") or [])
    ]
    return session_obj


def _to_workout_public(session_obj: dict) -> WorkoutPublic:
    exercises = []
    for ex in sorted(session_obj.get("exercises") or [], key=lambda x: x.get("sort_order", 0)):
        sets = [
            SessionSetOut(
                id=s["id"],
                set_order=s["set_order"],
                reps=s["reps"],
                weight=s["weight"],
                completed=s["completed"],
                set_type=s["set_type"],
            )
            for s in sorted(ex.get("sets") or [], key=lambda x: x.get("set_order", 0))
        ]
        exercises.append(
            SessionExerciseOut(
                id=ex["id"],
                exercise_id=ex["exercise_id"],
                sort_order=ex.get("sort_order", 0),
                sets=sets,
            )
        )

    return WorkoutPublic(
        id=session_obj["id"],
        user_id=session_obj["user_id"],
        name=session_obj["template_name_snapshot"],
        date=session_obj["started_at"],
        notes=session_obj.get("notes"),
        status=session_obj["status"],
        duration_seconds=session_obj.get("duration_seconds"),
        exercises=exercises,
    )


def _fetch_workout(supabase: Client, workout_id: int, user_id: int) -> dict | None:
    response = (
        supabase.table("sessions")
        .select(
            "id,user_id,template_name_snapshot,status,started_at,ended_at,duration_seconds,notes,session_exercises(id,exercise_id,sort_order,session_sets(id,set_order,reps,weight,completed,set_type))"
        )
        .eq("id", workout_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    if not response.data:
        return None
    return _normalize_session(response.data[0])


@router.post("", response_model=WorkoutPublic, status_code=status.HTTP_201_CREATED)
def create_workout(
    payload: WorkoutCreate,
    supabase: Client = Depends(get_supabase),
    current_user: dict = Depends(get_current_user),
):
    created = (
        supabase.table("sessions")
        .insert(
            {
                "user_id": current_user["id"],
                "template_name_snapshot": payload.name,
                "started_at": payload.date.isoformat(),
                "notes": payload.notes,
                "status": "active",
            }
        )
        .execute()
    )
    if not created.data:
        raise HTTPException(status_code=500, detail="Failed to create workout")
    workout = _fetch_workout(supabase, created.data[0]["id"], current_user["id"])
    return _to_workout_public(workout)


@router.get("", response_model=list[WorkoutPublic])
def list_workouts(
    date: str | None = Query(default=None),
    muscle_group: str | None = Query(default=None),
    exercise_id: int | None = Query(default=None),
    supabase: Client = Depends(get_supabase),
    current_user: dict = Depends(get_current_user),
):
    response = (
        supabase.table("sessions")
        .select(
            "id,user_id,template_name_snapshot,status,started_at,ended_at,duration_seconds,notes,session_exercises(id,exercise_id,sort_order,session_sets(id,set_order,reps,weight,completed,set_type))"
        )
        .eq("user_id", current_user["id"])
        .order("started_at", desc=True)
        .execute()
    )
    sessions = [_normalize_session(s) for s in (response.data or [])]

    if date:
        sessions = [
            s
            for s in sessions
            if datetime.fromisoformat(str(s["started_at"]).replace("Z", "+00:00")).date().isoformat()
            == date
        ]

    if exercise_id is not None:
        sessions = [
            s
            for s in sessions
            if any(ex.get("exercise_id") == exercise_id for ex in (s.get("exercises") or []))
        ]

    if muscle_group:
        exercise_ids = {
            ex.get("exercise_id")
            for s in sessions
            for ex in (s.get("exercises") or [])
            if ex.get("exercise_id") is not None
        }
        muscle_map: dict[int, str] = {}
        if exercise_ids:
            exercises_res = (
                supabase.table("exercises")
                .select("id,primary_muscle")
                .in_("id", list(exercise_ids))
                .execute()
            )
            muscle_map = {
                int(row["id"]): str(row.get("primary_muscle") or "")
                for row in (exercises_res.data or [])
            }

        mg = muscle_group.lower()
        sessions = [
            s
            for s in sessions
            if any(
                mg in muscle_map.get(int(ex.get("exercise_id")), "").lower()
                for ex in (s.get("exercises") or [])
                if ex.get("exercise_id") is not None
            )
        ]

    return [_to_workout_public(s) for s in sessions]


@router.get("/{workout_id}", response_model=WorkoutPublic)
def get_workout(
    workout_id: int,
    supabase: Client = Depends(get_supabase),
    current_user: dict = Depends(get_current_user),
):
    workout = _fetch_workout(supabase, workout_id, current_user["id"])
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return _to_workout_public(workout)


@router.post("/{workout_id}/exercises", response_model=WorkoutPublic)
def add_exercise_to_workout(
    workout_id: int,
    payload: WorkoutExerciseAdd,
    supabase: Client = Depends(get_supabase),
    current_user: dict = Depends(get_current_user),
):
    workout = _fetch_workout(supabase, workout_id, current_user["id"])
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")

    supabase.table("session_exercises").insert(
        {
            "session_id": workout_id,
            "exercise_id": payload.exercise_id,
            "sort_order": payload.sort_order,
        }
    ).execute()

    workout = _fetch_workout(supabase, workout_id, current_user["id"])
    return _to_workout_public(workout)


@router.delete("/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout(
    workout_id: int,
    supabase: Client = Depends(get_supabase),
    current_user: dict = Depends(get_current_user),
):
    workout = _fetch_workout(supabase, workout_id, current_user["id"])
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    supabase.table("sessions").delete().eq("id", workout_id).eq(
        "user_id", current_user["id"]
    ).execute()
