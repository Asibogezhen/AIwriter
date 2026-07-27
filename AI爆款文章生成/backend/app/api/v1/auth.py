"""认证路由"""

from fastapi import APIRouter, Depends
from app.schemas.common import BaseResponse
from app.schemas.user import RegisterRequest, LoginRequest, UserResponse, TokenResponse
from app.dependencies import get_current_user
from app.services import auth_service

router = APIRouter(prefix="/v1/auth", tags=["认证"])


@router.post("/register", response_model=BaseResponse[TokenResponse])
async def register(request: RegisterRequest):
    result = await auth_service.register_user(
        request.email, request.password, request.nickname
    )
    return BaseResponse.success(data=result)


@router.post("/login", response_model=BaseResponse[TokenResponse])
async def login(request: LoginRequest):
    result = await auth_service.login_user(request.email, request.password)
    return BaseResponse.success(data=result)


@router.get("/me", response_model=BaseResponse[UserResponse])
async def me(user: dict = Depends(get_current_user)):
    result = await auth_service.get_user_by_id(user["id"])
    return BaseResponse.success(data=result)
