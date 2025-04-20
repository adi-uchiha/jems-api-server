from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.schemas.auth import UserLogin, UserSignup, PasswordReset, Token
from app.services.auth import (
    authenticate_user,
    create_user,
    handle_password_reset,
    verify_token,
    invalidate_token
)
from app.services.google_auth import handle_google_auth
from pydantic import BaseModel
from app.db.queries.auth_queries import reset_user_password
from app.core.security import get_password_hash

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

class GoogleAuthRequest(BaseModel):
    token: str

@router.post("/login")
async def login(user_data: UserLogin):
    try:
        return await authenticate_user(user_data)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/signup")
async def signup(user_data: UserSignup):
    try:
        return await create_user(user_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/forgot-password")
async def forgot_password(data: PasswordReset):
    try:
        return await handle_password_reset(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reset-password")
async def reset_password(data: PasswordReset):
    """Reset user password"""
    try:
        hashed_password = get_password_hash(data.newPassword)
        await reset_user_password(data.email, hashed_password)
        return {"message": "Password reset successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/verify")
async def verify_token_endpoint(token: str = Depends(oauth2_scheme)):
    try:
        user = await verify_token(token)
        if not user.get('id'):
            raise HTTPException(status_code=401, detail="Invalid token")
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/logout")
async def logout_endpoint(token: str = Depends(oauth2_scheme)):
    try:
        return await invalidate_token(token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/google")
async def google_auth(request: GoogleAuthRequest):
    try:
        return await handle_google_auth(request.token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
