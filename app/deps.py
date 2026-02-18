from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.core.security import decode_access_token
from app.db import Client, get_supabase

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), supabase: Client = Depends(get_supabase)
) -> dict:
    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    response = (
        supabase.table("users")
        .select("id,email,display_name,units,default_rest_seconds,password_hash")
        .eq("id", int(user_id))
        .limit(1)
        .execute()
    )
    user = response.data[0] if response.data else None
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user
