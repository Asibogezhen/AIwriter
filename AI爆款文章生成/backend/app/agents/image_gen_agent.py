"""配图生成 Agent（并行路由分发）"""

import asyncio
import logging
import os
from app.agents.base import BaseAgent, ArticleState
from app.config import settings
from app.core.sse_manager import send_event, send_progress
from app.services.pexels_service import PexelsService
from app.services.svg_service import SvgService
from app.services.image_service import ImageService

logger = logging.getLogger(__name__)


class ImageGenAgent(BaseAgent):
    def __init__(self):
        self.pexels = PexelsService()
        self.svg = SvgService()
        self.qwen = ImageService()

    async def execute(self, state: ArticleState) -> ArticleState:
        if not state.image_requirements:
            logger.info("Agent5 无配图需求，跳过")
            await send_progress(state.article_id, "IMAGE_GEN_DONE", 85)
            return state

        logger.info("Agent5 配图生成开始, count=%d", len(state.image_requirements))
        await send_progress(state.article_id, "IMAGE_GENERATING", 70)

        # 确保图片目录存在
        img_dir = os.path.join(settings.images_dir, state.article_id)
        os.makedirs(img_dir, exist_ok=True)

        # 并行生成所有配图
        tasks = []
        for req in state.image_requirements:
            tasks.append(self._generate_one(req, img_dir))

        results = []
        for coro in asyncio.as_completed(tasks):
            try:
                result = await coro
                if result:
                    results.append(result)
                    await send_event(state.article_id, "image_gen_done", result)
            except Exception as e:
                logger.error("单张配图生成失败: %s", e)

        # 按 position 排序
        results.sort(key=lambda r: r.get("position", 0))
        state.image_urls = results

        await send_progress(state.article_id, "IMAGE_GEN_DONE", 85)
        logger.info("Agent5 配图生成完成, success=%d/%d", len(results), len(state.image_requirements))
        return state

    async def _generate_one(self, req: dict, img_dir: str) -> dict | None:
        pos = req.get("position", 0)
        source = req.get("imageSource", "PEXELS")
        output_path = os.path.join(img_dir, f"{pos:02d}.png")

        try:
            match source:
                case "PEXELS":
                    url = await self.pexels.search(req.get("keywords", ""))
                    static_url = url
                case "SVG":
                    static_url = await self.svg.generate(
                        req.get("prompt", ""), output_path
                    )
                case "QWEN_IMAGE":
                    static_url = await self.qwen.generate(
                        req.get("prompt", ""), output_path
                    )
                case _:
                    url = await self.pexels.search(req.get("keywords", ""))
                    static_url = url

            return {
                "position": pos,
                "url": static_url,
                "method": source,
                "sectionTitle": req.get("sectionTitle", ""),
                "placeholderId": req.get("placeholderId", ""),
            }
        except Exception as e:
            logger.error("配图生成失败 position=%d source=%s: %s", pos, source, e)
            return None
