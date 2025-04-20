from fastapi import APIRouter, HTTPException, Depends
from app.schemas.auth import UserSignup
from app.services.auth import verify_token
from app.db.queries.auth_queries import get_user, get_user_by_email
from app.core.security import oauth2_scheme

router = APIRouter()

@router.get("/me")
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user profile"""
    try:
        user_data = await verify_token(token)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
        return user_data
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.get("/{username}")
async def get_user_profile(username: str):
    """Get user profile by username"""
    try:
        user = await get_user(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "username": user["username"],
            "email": user["email"],
            "name": user["name"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/email/{email}")
async def get_user_by_email_route(email: str):
    """Get user by email"""
    try:
        user = await get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "username": user["username"],
            "email": user["email"],
            "name": user["name"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
