from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import create_access_token, get_password_hash, verify_password
from app.db import Client, get_supabase
from app.schemas import TokenResponse, UserLogin, UserPublic, UserRegister

router = APIRouter(prefix="/auth", tags=["auth"])


def _supabase_error_detail(exc: Exception) -> str:
    return (
        "Supabase operation failed. "
        "Ensure backend is configured with SUPABASE_SERVICE_ROLE_KEY "
        "(recommended) and your database/RLS policies allow this operation. "
        f"Original error: {exc}"
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, supabase: Client = Depends(get_supabase)):
    normalized_email = payload.email.strip().lower()
    display_name = payload.display_name.strip()

    try:
        created = (
            supabase.table("users")
            .insert(
                {
                    "email": normalized_email,
                    "password_hash": get_password_hash(payload.password),
                    "display_name": display_name,
                    "units": "kg",
                    "default_rest_seconds": 90,
                }
            )
            .execute()
        )

        # Some Supabase setups can return an empty data payload on insert.
        if created.data:
            user = created.data[0]
        else:
            lookup = (
                supabase.table("users")
                .select("id,email,display_name,units,default_rest_seconds")
                .eq("email", normalized_email)
                .limit(1)
                .execute()
            )
            if not lookup.data:
                raise HTTPException(status_code=500, detail="Failed to create user")
            user = lookup.data[0]
    except Exception as exc:
        msg = str(exc)
        if "duplicate key" in msg.lower() or "23505" in msg:
            raise HTTPException(status_code=400, detail="Email already registered") from exc

        raise HTTPException(
            status_code=500,
            detail=_supabase_error_detail(exc),
        ) from exc

    token = create_access_token(str(user["id"]))
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user, from_attributes=False))


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, supabase: Client = Depends(get_supabase)):
    normalized_email = payload.email.strip().lower()

    try:
        response = (
            supabase.table("users")
            .select("id,email,display_name,units,default_rest_seconds,password_hash")
            .eq("email", normalized_email)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=_supabase_error_detail(exc)) from exc

    user = response.data[0] if response.data else None
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(str(user["id"]))
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user, from_attributes=False))
