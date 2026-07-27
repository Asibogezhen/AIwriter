"""VIP 与兑换码路由"""

import uuid
import secrets
import string
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from app.core.database import database
from app.dependencies import get_current_user
from app.schemas.common import BaseResponse
from app.exceptions import ErrorCode, throw_if

router = APIRouter(prefix="/v1/vip", tags=["VIP"])


class RedeemRequest(BaseModel):
    code: str = Field(..., min_length=1)


class CreateOrderRequest(BaseModel):
    plan_type: str = Field(default="lifetime", pattern="^lifetime$")


# 定价配置 — ¥199 永久买断
PRICING = {
    "lifetime": {"name": "永久会员", "price": 199, "amount": 19900, "duration_days": None},
}

PERKS = [
    "不限次数文章生成",
    "AI 智能生图 (Qwen-Image2)",
    "全部写作风格自由选择",
    "优先体验新功能",
]


def _gen_order_no() -> str:
    chars = string.ascii_uppercase + string.digits
    rand = "".join(secrets.choice(chars) for _ in range(14))
    return f"MP{rand}"  # 墨笔 (Mo Bi) prefix


@router.get("/status")
async def vip_status(user: dict = Depends(get_current_user)):
    return BaseResponse.success(data={
        "isVip": user.get("is_vip", False),
        "freeQuota": user.get("free_quota", 0),
    })


@router.get("/pricing")
async def get_pricing():
    plans = []
    for key, cfg in PRICING.items():
        plans.append({
            "planType": key,
            "name": cfg["name"],
            "price": cfg["price"],
            "amount": cfg["amount"],
            "tag": cfg["tag"],
            "perks": PERKS,
        })
    return BaseResponse.success(data={"plans": plans})


@router.post("/orders")
async def create_order(request: CreateOrderRequest, user: dict = Depends(get_current_user)):
    throw_if(user.get("is_vip"), ErrorCode.CONFLICT, "你已经是 VIP 了")

    cfg = PRICING[request.plan_type]
    order_no = _gen_order_no()
    order_id = str(uuid.uuid4())

    await database.execute(
        """INSERT INTO orders (id, user_id, order_no, plan_type, amount, status)
           VALUES (:id, :uid, :order_no, :plan_type, :amount, 'pending')""",
        {
            "id": order_id,
            "uid": user["id"],
            "order_no": order_no,
            "plan_type": request.plan_type,
            "amount": cfg["amount"],
        },
    )

    return BaseResponse.success(data={
        "orderNo": order_no,
        "planName": cfg["name"],
        "amount": cfg["amount"],
        "price": cfg["price"],
    })


@router.post("/orders/{order_no}/pay")
async def pay_order(order_no: str, user: dict = Depends(get_current_user)):
    row = await database.fetch_one(
        "SELECT id, plan_type, amount, status FROM orders WHERE order_no = :no AND user_id = :uid",
        {"no": order_no, "uid": user["id"]},
    )
    throw_if(row is None, ErrorCode.NOT_FOUND, "订单不存在")
    throw_if(row["status"] != "pending", ErrorCode.CONFLICT, "订单状态异常")

    config = PRICING[row["plan_type"]]
    now = datetime.utcnow()
    expires = None
    if config["duration_days"] is not None:
        expires = now + timedelta(days=config["duration_days"])

    async with database.transaction():
        await database.execute(
            "UPDATE orders SET status = 'paid', paid_at = :now WHERE id = :id",
            {"now": now, "id": str(row["id"])},
        )
        await database.execute(
            "UPDATE users SET is_vip = TRUE, vip_expires_at = :exp WHERE id = :uid",
            {"exp": expires, "uid": user["id"]},
        )

    return BaseResponse.success(message="支付成功！你已成为 VIP")


@router.post("/redeem")
async def redeem_code(request: RedeemRequest, user: dict = Depends(get_current_user)):
    throw_if(user.get("is_vip"), ErrorCode.CONFLICT, "你已经是 VIP 了")

    row = await database.fetch_one(
        "SELECT id, is_used FROM redeem_codes WHERE code = :code",
        {"code": request.code.strip().upper()},
    )
    throw_if(row is None, ErrorCode.NOT_FOUND, "兑换码无效")
    throw_if(row["is_used"], ErrorCode.CONFLICT, "该兑换码已被使用")

    async with database.transaction():
        await database.execute(
            "UPDATE redeem_codes SET is_used = 1, used_by = :uid, used_at = datetime('now') WHERE id = :id",
            {"uid": user["id"], "id": str(row["id"])},
        )
        await database.execute(
            "UPDATE users SET is_vip = TRUE, vip_expires_at = NULL WHERE id = :uid",
            {"uid": user["id"]},
        )

    return BaseResponse.success(message="兑换成功！你已成为永久 VIP")


@router.get("/codes", response_model=BaseResponse[dict])
async def list_my_codes(user: dict = Depends(get_current_user)):
    rows = await database.fetch_all(
        "SELECT code, used_at FROM redeem_codes WHERE used_by = :uid ORDER BY used_at DESC",
        {"uid": user["id"]},
    )
    return BaseResponse.success(data={"records": [dict(r) for r in rows]})
