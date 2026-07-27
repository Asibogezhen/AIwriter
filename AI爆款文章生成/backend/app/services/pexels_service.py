"""Pexels 免费图库搜索"""

import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class PexelsService:
    BASE_URL = "https://api.pexels.com/v1/search"

    async def search(self, keywords: str) -> str:
        """搜索图片，返回最匹配的 URL"""
        if not settings.pexels_api_key:
            logger.warning("Pexels API key 未配置，使用占位图")
            return f"https://picsum.photos/800/450?random={hash(keywords) % 1000}"

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    self.BASE_URL,
                    params={"query": keywords or "article", "per_page": 1},
                    headers={"Authorization": settings.pexels_api_key},
                )
                data = resp.json()
                photos = data.get("photos", [])
                if photos:
                    return photos[0]["src"]["large"]
        except Exception as e:
            logger.error("Pexels 搜索失败: %s", e)

        return f"https://picsum.photos/800/450?random={hash(keywords) % 1000}"
