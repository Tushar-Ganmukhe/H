from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.models.user import UserRegister, UserLogin, AuthResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=AuthResponse)
async def register(request: UserRegister):
    """Register a new user (phone-based for regular users, shop_id-based for admins)"""
    
    # Determine role based on what was provided
    if request.phone:
        role = "user"
        result = UserService.register_user(
            name=request.name,
            phone=request.phone,
            shop_id=None,
            password=request.password,
            age=request.age,
            role=role
        )
    elif request.shop_id:
        role = "admin"
        result = UserService.register_user(
            name=request.name,
            phone=None,
            shop_id=request.shop_id,
            password=request.password,
            age=None,
            role=role
        )
    else:
        return AuthResponse(
            success=False,
            message="Either phone or shop_id is required"
        )
    
    if result["success"]:
        return AuthResponse(
            success=True,
            message=result["message"],
            user=result["user"],
            session_id=result["user"]["id"]
        )
    else:
        return AuthResponse(success=False, message=result["message"])

@router.post("/login", response_model=AuthResponse)
async def login(request: UserLogin):
    """Login a user using phone/shop_id and password"""
    
    if request.phone:
        role = "user"
        result = UserService.login_user(
            phone=request.phone,
            shop_id=None,
            password=request.password,
            role=role
        )
    elif request.shop_id:
        role = "admin"
        result = UserService.login_user(
            phone=None,
            shop_id=request.shop_id,
            password=request.password,
            role=role
        )
    else:
        return AuthResponse(
            success=False,
            message="Either phone or shop_id is required"
        )
    
    if result["success"]:
        return AuthResponse(
            success=True,
            message=result["message"],
            user=result["user"],
            session_id=result["user"]["id"]
        )
    else:
        return AuthResponse(success=False, message=result["message"])
