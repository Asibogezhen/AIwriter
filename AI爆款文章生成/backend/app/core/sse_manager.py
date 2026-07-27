"""SSE 事件队列管理"""

import asyncio
import json
from typing import Optional

# 全局队列注册表: article_id → asyncio.Queue
_queues: dict[str, asyncio.Queue] = {}


def register_queue(article_id: str) -> asyncio.Queue:
    queue: asyncio.Queue = asyncio.Queue()
    _queues[article_id] = queue
    return queue


def get_queue(article_id: str) -> Optional[asyncio.Queue]:
    return _queues.get(article_id)


def remove_queue(article_id: str):
    _queues.pop(article_id, None)


async def send_event(article_id: str, event_type: str, data: dict | None = None):
    """向指定 article 的 SSE 连接推送事件"""
    queue = _queues.get(article_id)
    if queue:
        payload = {"event": event_type, "data": json.dumps(data or {}, ensure_ascii=False)}
        await queue.put(payload)


async def send_progress(article_id: str, stage: str, percent: int):
    """快捷推送进度事件"""
    await send_event(article_id, "progress", {"stage": stage, "percent": percent})
