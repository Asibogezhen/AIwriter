"""Qwen-Image AI 生图服务（DashScope multimodal-generation）"""

import logging
import os
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

ENDPOINT = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"


class ImageService:
    async def generate(self, prompt: str, output_path: str) -> str:
        """文生图，返回本地 /static/images/... URL"""
        if not settings.dashscope_api_key:
            logger.warning("DashScope API key 未配置")
            return self._fallback(prompt)

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    ENDPOINT,
                    headers={
                        "Authorization": f"Bearer {settings.dashscope_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": settings.dashscope_model,
                        "input": {
                            "messages": [
                                {"role": "user", "content": [{"text": prompt}]}
                            ]
                        },
                        "parameters": {"size": "1664*928"},
                    },
                )
                if resp.status_code != 200:
                    logger.error("Qwen-Image 返回 %s: %s", resp.status_code, resp.text[:300])
                    return self._fallback(prompt)

                data = resp.json()
                image_url = data["output"]["choices"][0]["message"]["content"][0]["image"]

                await self._download(image_url, output_path, client)
                return f"/static/images/{self._relative_path(output_path)}"

        except Exception as e:
            logger.error("Qwen-Image 生成失败: %s", e)
            return self._fallback(prompt)

    def _fallback(self, prompt: str) -> str:
        return f"https://picsum.photos/800/450?random={hash(prompt) % 1000}"

    async def _download(self, url: str, path: str, client: httpx.AsyncClient):
        resp = await client.get(url, follow_redirects=True)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(resp.content)

    @staticmethod
    def _relative_path(abs_path: str) -> str:
        import os
        path = abs_path.replace("\\", "/")
        if "/data/images/" in path:
            parts = path.rsplit("/data/images/", 1)
            return parts[-1]
        return os.path.basename(abs_path)
