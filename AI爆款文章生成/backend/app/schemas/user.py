"""用户请求/响应模型"""

from typing import Optional
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=6, max_length=100)
    nickname: str = Field(default="", max_length=100)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    id: str
    email: str
    nickname: str
    is_vip: bool = Field(alias="isVip")
    free_quota: int = Field(alias="freeQuota")
    is_admin: bool = Field(alias="isAdmin")

    class Config:
        populate_by_name = True


class TokenResponse(BaseModel):
    token: str
    refresh_token: str = Field(alias="refreshToken")
    user: UserResponse

    class Config:
        populate_by_name = True
