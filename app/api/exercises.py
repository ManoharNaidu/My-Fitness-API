from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db import Client, get_supabase
from app.deps import get_current_user
from app.schemas import ExerciseCreate, ExercisePublic, ExerciseUpdate

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("", response_model=list[ExercisePublic])
def list_exercises(
    query: str | None = Query(default=None),
    muscle: str | None = Query(default=None),
    equipment: str | None = Query(default=None),
    supabase: Client = Depends(get_supabase),
    current_user: dict = Depends(get_current_user),
):
    q = (
        supabase.table("exercises")
        .select("id,owner_user_id,name,primary_muscle,equipment,is_custom")
        .or_(f"owner_user_id.is.null,owner_user_id.eq.{current_user['id']}")
    )
    if query:
        q = q.ilike("name", f"%{query}%")
    if muscle:
        q = q.ilike("primary_muscle", f"%{muscle}%")
    if equipment:
        q = q.ilike("equipment", f"%{equipment}%")
    response = q.order("name").execute()
    return [ExercisePublic.model_validate(x, from_attributes=False) for x in (response.data or [])]


@router.get("/{exercise_id}", response_model=ExercisePublic)
def get_exercise(
    exercise_id: int,
    supabase: Client = Depends(get_supabase),
    current_user: dict = Depends(get_current_user),
):
    response = (
        supabase.table("exercises")
        .select("id,owner_user_id,name,primary_muscle,equipment,is_custom")
        .eq("id", exercise_id)
        .limit(1)
        .execute()
    )
    exercise = response.data[0] if response.data else None
    if not exercise or (
        exercise["owner_user_id"] is not None and exercise["owner_user_id"] != current_user["id"]
    ):
        raise HTTPException(status_code=404, detail="Exercise not found")
    return ExercisePublic.model_validate(exercise, from_attributes=False)


@router.post("", response_model=ExercisePublic, status_code=status.HTTP_201_CREATED)
def create_exercise(
    payload: ExerciseCreate,
    supabase: Client = Depends(get_supabase),
    current_user: dict = Depends(get_current_user),
):
    response = (
        supabase.table("exercises")
        .insert(
            {
                "owner_user_id": current_user["id"],
                "name": payload.name,
                "primary_muscle": payload.primary_muscle,
                "equipment": payload.equipment,
                "is_custom": True,
            }
        )
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create exercise")
    return ExercisePublic.model_validate(response.data[0], from_attributes=False)


@router.patch("/{exercise_id}", response_model=ExercisePublic)
def update_exercise(
    exercise_id: int,
    payload: ExerciseUpdate,
    supabase: Client = Depends(get_supabase),
    current_user: dict = Depends(get_current_user),
):
    existing = (
        supabase.table("exercises")
        .select("id,owner_user_id,name,primary_muscle,equipment,is_custom")
        .eq("id", exercise_id)
        .limit(1)
        .execute()
    )
    exercise = existing.data[0] if existing.data else None
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    if exercise["owner_user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Cannot edit global exercise")

    update_data = payload.model_dump(exclude_unset=True)
    updated = (
        supabase.table("exercises")
        .update(update_data)
        .eq("id", exercise_id)
        .eq("owner_user_id", current_user["id"])
        .execute()
    )
    if not updated.data:
        raise HTTPException(status_code=500, detail="Failed to update exercise")
    return ExercisePublic.model_validate(updated.data[0], from_attributes=False)


@router.delete("/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exercise(
    exercise_id: int,
    supabase: Client = Depends(get_supabase),
    current_user: dict = Depends(get_current_user),
):
    existing = (
        supabase.table("exercises")
        .select("id,owner_user_id")
        .eq("id", exercise_id)
        .limit(1)
        .execute()
    )
    exercise = existing.data[0] if existing.data else None
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    if exercise["owner_user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Cannot delete global exercise")
    supabase.table("exercises").delete().eq("id", exercise_id).eq("owner_user_id", current_user["id"]).execute()
