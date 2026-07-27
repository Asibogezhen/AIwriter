"""Redis 连接管理（可选，开发时不启用）"""

from app.config import settings

_redis = None


async def init_redis():
    if not settings.use_redis:
        return
    global _redis
    import redis.asyncio as aioredis
    _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    await _redis.ping()


async def close_redis():
    if _redis:
        await _redis.close()


async def get_redis():
    return _redis
