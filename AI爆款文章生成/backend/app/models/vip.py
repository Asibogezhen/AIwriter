"""兑换码与订单模型"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.user import make_pk


class RedeemCode(Base):
    __tablename__ = "redeem_codes"

    id = Column(String(36), primary_key=True, default=make_pk)
    code = Column(String(64), unique=True, nullable=False, index=True)
    used_by = Column(String(36), nullable=True)
    used_at = Column(DateTime, nullable=True)
    is_used = Column(Boolean, default=False)
    created_by = Column(String(36), nullable=True)
    batch = Column(String(50), default="")
    note = Column(Text, default="")
    created_at = Column(DateTime, server_default=func.now())


class Order(Base):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=make_pk)
    user_id = Column(String(36), nullable=False, index=True)
    order_no = Column(String(32), unique=True, nullable=False, index=True)
    plan_type = Column(String(20), nullable=False)   # monthly / yearly / lifetime
    amount = Column(Integer, nullable=False)           # 分
    status = Column(String(20), default="pending")    # pending / paid / cancelled
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
