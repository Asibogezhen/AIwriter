"""管理后台路由"""

import uuid
import string
import secrets
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from app.core.database import database
from app.dependencies import require_admin
from app.schemas.common import BaseResponse

router = APIRouter(prefix="/v1/admin", tags=["管理"])


class GenerateCodesRequest(BaseModel):
    count: int = Field(default=10, ge=1, le=500)
    batch: str = Field(default="")
    note: str = Field(default="")


def _generate_code() -> str:
    """生成 VIP-XXXX-XXXX-XXXX 格式的兑换码"""
    chars = string.ascii_uppercase + string.digits
    parts = ["".join(secrets.choice(chars) for _ in range(4)) for _ in range(3)]
    return "VIP-" + "-".join(parts)


@router.post("/codes/generate")
async def generate_codes(request: GenerateCodesRequest, admin: dict = Depends(require_admin)):
    codes = []
    for _ in range(request.count):
        code = _generate_code()
        await database.execute(
            """INSERT INTO redeem_codes (id, code, created_by, batch, note)
               VALUES (:id, :code, :uid, :batch, :note)""",
            {
                "id": str(uuid.uuid4()),
                "code": code,
                "uid": admin["id"],
                "batch": request.batch,
                "note": request.note,
            },
        )
        codes.append(code)

    return BaseResponse.success(data={"count": len(codes), "batch": request.batch, "codes": codes})


@router.get("/codes")
async def list_codes(
    page: int = 1,
    page_size: int = 20,
    batch: str = "",
    admin: dict = Depends(require_admin),
):
    offset = (page - 1) * page_size
    if batch:
        rows = await database.fetch_all(
            """SELECT code, is_used, used_at, batch, note, created_at
               FROM redeem_codes WHERE batch = :batch
               ORDER BY created_at DESC LIMIT :limit OFFSET :offset""",
            {"batch": batch, "limit": page_size, "offset": offset},
        )
        total_row = await database.fetch_one(
            "SELECT COUNT(*) as cnt FROM redeem_codes WHERE batch = :batch",
            {"batch": batch},
        )
    else:
        rows = await database.fetch_all(
            """SELECT code, is_used, used_at, batch, note, created_at
               FROM redeem_codes ORDER BY created_at DESC LIMIT :limit OFFSET :offset""",
            {"limit": page_size, "offset": offset},
        )
        total_row = await database.fetch_one("SELECT COUNT(*) as cnt FROM redeem_codes")

    total = total_row["cnt"] if total_row else 0
    records = [dict(r) for r in rows]
    for rec in records:
        if rec.get("used_at"):
            rec["used_at"] = str(rec["used_at"])
        if rec.get("created_at"):
            rec["created_at"] = str(rec["created_at"])

    return BaseResponse.success(data={"records": records, "total": total, "page": page, "pageSize": page_size})


@router.get("/stats")
async def get_stats(admin: dict = Depends(require_admin)):
    users = await database.fetch_one("SELECT COUNT(*) as cnt FROM users")
    articles = await database.fetch_one("SELECT COUNT(*) as cnt FROM articles")
    vip = await database.fetch_one("SELECT COUNT(*) as cnt FROM users WHERE is_vip = TRUE")
    completed = await database.fetch_one("SELECT COUNT(*) as cnt FROM articles WHERE status = 'completed'")

    return BaseResponse.success(data={
        "totalUsers": users["cnt"] if users else 0,
        "totalArticles": articles["cnt"] if articles else 0,
        "vipUsers": vip["cnt"] if vip else 0,
        "completedArticles": completed["cnt"] if completed else 0,
    })
