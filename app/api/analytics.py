from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query

from app.db import Client, get_supabase
from app.deps import get_current_user
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
    supabase: Client = Depends(get_supabase),
    current_user: dict = Depends(get_current_user),
):
    from_dt = _range_to_start(range)
    session_response = (
        supabase.table("sessions")
        .select(
            "id,duration_seconds,session_exercises(exercise_id,session_sets(reps,weight,completed))"
        )
        .eq("user_id", current_user["id"])
        .eq("status", "completed")
        .gte("started_at", from_dt.isoformat())
        .execute()
    )
    sessions = session_response.data or []

    total_volume = 0.0
    durations = []
    for s in sessions:
        if s.get("duration_seconds"):
            durations.append(s["duration_seconds"])
        for ex in s.get("session_exercises") or []:
            for set_ in ex.get("session_sets") or []:
                total_volume += float(set_["weight"]) * int(set_["reps"])

    meal_response = (
        supabase.table("meal_logs")
        .select("calories")
        .eq("user_id", current_user["id"])
        .gte("eaten_at", from_dt.isoformat())
        .execute()
    )
    meals = meal_response.data or []

    avg_minutes = (sum(durations) / len(durations) / 60) if durations else 0.0
    return OverviewStats(
        range=range,
        completed_workouts=len(sessions),
        total_volume=round(total_volume, 2),
        average_duration_minutes=round(avg_minutes, 2),
        total_calories=sum(int(m["calories"]) for m in meals),
    )


@router.get("/progression", response_model=list[ProgressPoint])
def progression(
    exercise_id: int,
    metric: str = Query(default="weight", pattern="^(1rm|volume|weight)$"),
    range: str = Query(default="30d", pattern="^(7d|30d|12w)$"),
    supabase: Client = Depends(get_supabase),
    current_user: dict = Depends(get_current_user),
):
    from_dt = _range_to_start(range)
    response = (
        supabase.table("sessions")
        .select("started_at,session_exercises(exercise_id,session_sets(reps,weight,completed))")
        .eq("user_id", current_user["id"])
        .eq("status", "completed")
        .gte("started_at", from_dt.isoformat())
        .order("started_at", desc=False)
        .execute()
    )
    sessions = response.data or []

    points: list[ProgressPoint] = []
    for s in sessions:
        exercise_entries = [
            x for x in (s.get("session_exercises") or []) if x.get("exercise_id") == exercise_id
        ]
        if not exercise_entries:
            continue
        sets = [st for ex in exercise_entries for st in (ex.get("session_sets") or [])]
        if not sets:
            continue

        if metric == "volume":
            value = sum(int(st["reps"]) * float(st["weight"]) for st in sets)
        elif metric == "1rm":
            value = max((float(st["weight"]) * (1 + int(st["reps"]) / 30)) for st in sets)
        else:
            value = max(float(st["weight"]) for st in sets)

        started_at = datetime.fromisoformat(str(s["started_at"]).replace("Z", "+00:00"))
        points.append(ProgressPoint(label=started_at.strftime("%Y-%m-%d"), value=value))

    return points
