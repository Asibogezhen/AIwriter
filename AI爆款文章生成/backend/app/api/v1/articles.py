"""文章 API 路由"""

import asyncio
import json
import uuid
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from app.core.database import database
from app.core.sse_manager import register_queue, remove_queue, send_event
from app.dependencies import get_current_user
from app.schemas.common import BaseResponse
from app.schemas.article import GenerateRequest
from app.agents.base import ArticleState
from app.agents.orchestrator import Orchestrator
from app.exceptions import BusinessException, ErrorCode, throw_if

router = APIRouter(prefix="/v1/articles", tags=["文章"])


@router.post("/generate", response_model=BaseResponse[dict])
async def generate_article(request: GenerateRequest, user: dict = Depends(get_current_user)):
    throw_if(not request.topic or not request.topic.strip(), ErrorCode.PARAMS_ERROR, "选题不能为空")

    # 配额检查
    if not user.get("is_vip") and user.get("free_quota", 0) <= 0:
        raise BusinessException(ErrorCode.QUOTA_EXCEEDED, "免费额度已用完，请升级 VIP")

    article_id = str(uuid.uuid4())

    # 非 VIP 扣减免费额度
    if not user.get("is_vip"):
        await database.execute(
            "UPDATE users SET free_quota = free_quota - 1 WHERE id = :uid AND free_quota > 0",
            {"uid": user["id"]},
        )

    # 创建文章记录
    await database.execute(
        """INSERT INTO articles (id, user_id, topic, style, word_count, status, platform)
           VALUES (:id, :uid, :topic, :style, :wc, 'pending', :platform)""",
        {
            "id": article_id,
            "uid": user["id"],
            "topic": request.topic,
            "style": request.style or "",
            "wc": request.word_count or 2000,
            "platform": request.platform or "article",
        },
    )

    # 注册 SSE 队列并异步启动编排器
    register_queue(article_id)
    state = ArticleState(
        article_id=article_id,
        topic=request.topic,
        style=request.style or "",
        word_count=request.word_count or 2000,
        image_preference=request.image_preference or "smart",
        is_vip=user.get("is_vip", False),
        platform=request.platform or "article",
        xhs_category=request.xhs_category or "",
        xhs_persona=request.xhs_persona or "",
        xhs_image_style=request.xhs_image_style or "",
        product_name=request.product_name or "",
        product_description=request.product_description or "",
    )
    asyncio.create_task(Orchestrator().run(state))

    return BaseResponse.success(data={"articleId": article_id})


@router.get("/generate/{article_id}/sse")
async def article_sse(article_id: str, request: Request):
    queue = register_queue(article_id)

    async def event_stream():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"event: {msg['event']}\ndata: {msg['data']}\n\n"
                    if msg["event"] in ("done", "error"):
                        break
                except asyncio.TimeoutError:
                    yield f"event: ping\ndata: {{}}\n\n"
        finally:
            remove_queue(article_id)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("")
async def list_articles(
    page: int = 1,
    page_size: int = 10,
    user: dict = Depends(get_current_user),
):
    offset = (page - 1) * page_size
    rows = await database.fetch_all(
        """SELECT id, title, topic, style, platform, status, created_at, updated_at
           FROM articles WHERE user_id = :uid
           ORDER BY created_at DESC LIMIT :limit OFFSET :offset""",
        {"uid": user["id"], "limit": page_size, "offset": offset},
    )
    total_row = await database.fetch_one(
        "SELECT COUNT(*) as cnt FROM articles WHERE user_id = :uid",
        {"uid": user["id"]},
    )
    total = total_row["cnt"] if total_row else 0
    records = [dict(r) for r in rows]
    for rec in records:
        rec["id"] = str(rec["id"])
        rec["created_at"] = str(rec["created_at"])
        rec["updated_at"] = str(rec["updated_at"])
    return BaseResponse.success(data={"records": records, "total": total, "page": page, "pageSize": page_size})


@router.get("/{article_id}")
async def get_article(article_id: str, user: dict = Depends(get_current_user)):
    row = await database.fetch_one(
        """SELECT id, title, topic, style, platform, word_count, status, markdown,
                  outline, images, rendered_html, error_message, created_at
           FROM articles WHERE id = :id AND user_id = :uid""",
        {"id": article_id, "uid": user["id"]},
    )
    throw_if(row is None, ErrorCode.NOT_FOUND, "文章不存在")
    result = dict(row)
    result["id"] = str(result["id"])
    result["created_at"] = str(result["created_at"])
    result["outline"] = json.loads(result["outline"]) if result["outline"] else []
    result["images"] = json.loads(result["images"]) if result["images"] else []
    return BaseResponse.success(data=result)


@router.delete("/{article_id}")
async def delete_article(article_id: str, user: dict = Depends(get_current_user)):
    await database.execute(
        "DELETE FROM articles WHERE id = :id AND user_id = :uid",
        {"id": article_id, "uid": user["id"]},
    )
    return BaseResponse.success(message="删除成功")
