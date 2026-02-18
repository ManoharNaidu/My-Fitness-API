from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db import Client, get_supabase
from app.deps import get_current_user
from app.schemas import MealCreate, MealPublic

router = APIRouter(prefix="/nutrition", tags=["nutrition"])


@router.get("/meals", response_model=list[MealPublic])
def list_meals(
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    supabase: Client = Depends(get_supabase),
    current_user: dict = Depends(get_current_user),
):
    q = supabase.table("meal_logs").select("id,user_id,meal_name,calories,protein_g,carbs_g,fats_g,eaten_at").eq("user_id", current_user["id"])
    if from_date:
        q = q.gte("eaten_at", from_date.isoformat())
    if to_date:
        q = q.lte("eaten_at", to_date.isoformat())
    response = q.order("eaten_at", desc=True).execute()
    return [MealPublic.model_validate(x, from_attributes=False) for x in (response.data or [])]


@router.post("/meals", response_model=MealPublic, status_code=status.HTTP_201_CREATED)
def add_meal(
    payload: MealCreate,
    supabase: Client = Depends(get_supabase),
    current_user: dict = Depends(get_current_user),
):
    response = (
        supabase.table("meal_logs")
        .insert(
            {
                "user_id": current_user["id"],
                "meal_name": payload.meal_name,
                "calories": payload.calories,
                "protein_g": payload.protein_g,
                "carbs_g": payload.carbs_g,
                "fats_g": payload.fats_g,
                "eaten_at": (payload.eaten_at or datetime.utcnow()).isoformat(),
            }
        )
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create meal")
    return MealPublic.model_validate(response.data[0], from_attributes=False)
