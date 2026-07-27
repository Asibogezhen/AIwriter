"""认证服务"""

import uuid
from app.core.database import database
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.exceptions import BusinessException, ErrorCode, throw_if


async def register_user(email: str, password: str, nickname: str) -> dict:
    # 检查邮箱是否已存在
    existing = await database.fetch_one(
        "SELECT id FROM users WHERE email = :email", {"email": email}
    )
    throw_if(existing is not None, ErrorCode.CONFLICT, "该邮箱已注册")

    user_id = str(uuid.uuid4())
    password_hash = hash_password(password)
    await database.execute(
        """INSERT INTO users (id, email, password_hash, nickname, is_vip, free_quota, is_admin)
           VALUES (:id, :email, :password_hash, :nickname, 0, 1, 0)""",
        {"id": user_id, "email": email, "password_hash": password_hash, "nickname": nickname or email.split("@")[0]},
    )
    row = await database.fetch_one(
        "SELECT id, email, nickname, is_vip, free_quota, is_admin FROM users WHERE id = :id",
        {"id": user_id},
    )
    user = _build_user_dict(row)
    token = create_access_token(user["id"])
    refresh_token = create_refresh_token(user["id"])
    return {"token": token, "refresh_token": refresh_token, "user": user}


async def login_user(email: str, password: str) -> dict:
    row = await database.fetch_one(
        "SELECT id, email, nickname, password_hash, is_vip, free_quota, is_admin FROM users WHERE email = :email",
        {"email": email},
    )
    throw_if(row is None, ErrorCode.PARAMS_ERROR, "邮箱或密码错误")
    throw_if(not verify_password(password, row["password_hash"]), ErrorCode.PARAMS_ERROR, "邮箱或密码错误")

    user = _build_user_dict(row)
    token = create_access_token(user["id"])
    refresh_token = create_refresh_token(user["id"])
    return {"token": token, "refresh_token": refresh_token, "user": user}


async def get_user_by_id(user_id: str) -> dict:
    row = await database.fetch_one(
        "SELECT id, email, nickname, is_vip, free_quota, is_admin FROM users WHERE id = :id",
        {"id": user_id},
    )
    throw_if(row is None, ErrorCode.NOT_FOUND, "用户不存在")
    return _build_user_dict(row)


def _build_user_dict(row) -> dict:
    return {
        "id": str(row["id"]),
        "email": row["email"],
        "nickname": row["nickname"] or "",
        "is_vip": row["is_vip"],
        "free_quota": row["free_quota"],
        "is_admin": row["is_admin"],
    }
