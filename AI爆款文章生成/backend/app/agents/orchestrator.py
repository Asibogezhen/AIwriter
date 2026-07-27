"""多 Agent 编排器"""

import logging
import json
from app.agents.base import ArticleState
from app.agents.title_agent import TitleAgent
from app.agents.outline_agent import OutlineAgent
from app.agents.search_agent import SearchAgent
from app.agents.content_agent import ContentAgent
from app.agents.image_prompt_agent import ImagePromptAgent
from app.agents.image_gen_agent import ImageGenAgent
from app.agents.render_agent import RenderAgent
from app.core.database import database
from app.core.sse_manager import send_event, send_progress
from app.enum.sse_message import SseMessageTypeEnum

logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(self):
        self.agents = [
            ("title", TitleAgent()),
            ("outline", OutlineAgent()),
            ("search", SearchAgent()),
            ("content", ContentAgent()),
            ("image_prompt", ImagePromptAgent()),
            ("image_gen", ImageGenAgent()),
            ("render", RenderAgent()),
        ]

    async def run(self, state: ArticleState):
        logger.info("编排器开始执行, articleId=%s", state.article_id)
        await self._update_db(state.article_id, {"status": "generating"})

        try:
            for name, agent in self.agents:
                state = await agent.execute(state)
                if state.error:
                    raise Exception(state.error)
                await self._save_stage(state.article_id, name, state)

            await send_event(state.article_id, "done", {"articleId": state.article_id})
            await self._update_db(state.article_id, {
                "status": "completed",
                "title": state.title,
                "markdown": state.content,
                "outline": json.dumps(state.outline, ensure_ascii=False),
                "images": json.dumps(state.image_urls, ensure_ascii=False),
                "rendered_html": state.full_content,
                "progress": json.dumps({"stage": "done", "percent": 100}),
            })
            logger.info("编排器执行完成, articleId=%s", state.article_id)
        except Exception as e:
            logger.error("编排器执行失败, articleId=%s: %s", state.article_id, e)
            await send_event(state.article_id, "error", {"message": str(e)})
            await self._update_db(state.article_id, {
                "status": "failed",
                "error_message": str(e),
            })

    async def _save_stage(self, article_id: str, stage: str, state: ArticleState):
        save_data = {}
        if stage == "title":
            save_data["title"] = state.title
        elif stage == "outline":
            save_data["outline"] = json.dumps(state.outline, ensure_ascii=False)
        elif stage == "content":
            save_data["markdown"] = state.content

        if save_data:
            await self._update_db(article_id, save_data)

    async def _update_db(self, article_id: str, data: dict):
        if not data:
            return
        set_clause = ", ".join(f"{k} = :{k}" for k in data)
        query = f"UPDATE articles SET {set_clause} WHERE id = :article_id"
        params = {**data, "article_id": article_id}
        try:
            await database.execute(query, params)
        except Exception as e:
            logger.error("更新数据库失败: %s", e)
