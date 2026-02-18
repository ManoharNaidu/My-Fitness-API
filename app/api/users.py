from fastapi import APIRouter, Depends

from app.db import Client, get_supabase
from app.deps import get_current_user
from app.schemas import UserPreferencesUpdate, UserPublic

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserPublic)
def get_me(current_user: dict = Depends(get_current_user)):
    return UserPublic.model_validate(current_user, from_attributes=False)


@router.patch("/me/preferences", response_model=UserPublic)
def update_preferences(
    payload: UserPreferencesUpdate,
    supabase: Client = Depends(get_supabase),
    current_user: dict = Depends(get_current_user),
):
    update_data: dict = {}
    if payload.units is not None:
        update_data["units"] = payload.units
    if payload.default_rest_seconds is not None:
        update_data["default_rest_seconds"] = payload.default_rest_seconds

    if update_data:
        updated = (
            supabase.table("users")
            .update(update_data)
            .eq("id", current_user["id"])
            .execute()
        )
        if updated.data:
            current_user = updated.data[0]

    return UserPublic.model_validate(current_user, from_attributes=False)
