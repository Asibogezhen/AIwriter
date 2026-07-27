"""FastAPI 依赖注入"""

from fastapi import Depends, Header
from app.core.database import database
from app.core.security import decode_token
from app.exceptions import BusinessException, ErrorCode
from app.models.user import User


async def get_db():
    yield database


async def get_current_user(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise BusinessException(ErrorCode.UNAUTHORIZED)

    token = authorization.split(" ")[1]
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise BusinessException(ErrorCode.UNAUTHORIZED)

    user_id = payload.get("sub")
    query = "SELECT id, email, nickname, is_vip, free_quota, is_admin FROM users WHERE id = :id"
    row = await database.fetch_one(query, {"id": user_id})
    if not row:
        raise BusinessException(ErrorCode.UNAUTHORIZED, "用户不存在")

    return dict(row)


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if not user.get("is_admin"):
        raise BusinessException(ErrorCode.FORBIDDEN, "需要管理员权限")
    return user
