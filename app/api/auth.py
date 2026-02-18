from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import create_access_token, get_password_hash, verify_password
from app.db import Client, get_supabase
from app.schemas import TokenResponse, UserLogin, UserPublic, UserRegister

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, supabase: Client = Depends(get_supabase)):
    existing = (
        supabase.table("users")
        .select("id")
        .eq("email", payload.email)
        .limit(1)
        .execute()
    )
    if existing.data:
        raise HTTPException(status_code=400, detail="Email already registered")

    created = (
        supabase.table("users")
        .insert(
            {
                "email": payload.email,
                "password_hash": get_password_hash(payload.password),
                "display_name": payload.display_name,
                "units": "kg",
                "default_rest_seconds": 90,
            }
        )
        .execute()
    )
    if not created.data:
        raise HTTPException(status_code=500, detail="Failed to create user")

    user = created.data[0]

    token = create_access_token(str(user["id"]))
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user, from_attributes=False))


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, supabase: Client = Depends(get_supabase)):
    response = (
        supabase.table("users")
        .select("id,email,display_name,units,default_rest_seconds,password_hash")
        .eq("email", payload.email)
        .limit(1)
        .execute()
    )
    user = response.data[0] if response.data else None
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(str(user["id"]))
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user, from_attributes=False))
