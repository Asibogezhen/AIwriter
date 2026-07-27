"""用户模型"""

import uuid
from sqlalchemy import Column, String, Boolean, Integer, DateTime
from sqlalchemy.sql import func
from app.config import settings
from app.core.database import Base


def make_pk():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=make_pk)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(100), default="")
    is_vip = Column(Boolean, default=False)
    vip_expires_at = Column(DateTime, nullable=True)
    free_quota = Column(Integer, default=1)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
