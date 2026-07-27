"""标题生成 Agent"""

import json
import logging
from app.agents.base import BaseAgent, ArticleState
from app.core.llm_client import chat
from app.core.sse_manager import send_progress
from app.utils.prompt_templates import PromptTemplates

logger = logging.getLogger(__name__)


class TitleAgent(BaseAgent):
    async def execute(self, state: ArticleState) -> ArticleState:
        logger.info("Agent1 标题生成开始, articleId=%s platform=%s", state.article_id, state.platform)
        await send_progress(state.article_id, "TITLE_GENERATING", 5)

        if state.platform == "xiaohongshu":
            return await self._xhs_title(state)

        prompt = PromptTemplates.TITLE_PROMPT.replace("{topic}", state.topic)
        style_prompt = PromptTemplates.get_style_prompt(state.style)
        if style_prompt:
            prompt += style_prompt

        try:
            content = await chat(prompt)
            titles = json.loads(content)
            if not isinstance(titles, list) or len(titles) == 0:
                raise ValueError("标题生成结果格式错误")

            state.title = titles[0]["mainTitle"]
            state.sub_title = titles[0]["subTitle"]
            state.title_alternatives = titles[1:] if len(titles) > 1 else []

            await send_progress(state.article_id, "TITLE_DONE", 15)
            logger.info("Agent1 标题生成完成, title=%s", state.title)
            return state
        except (json.JSONDecodeError, KeyError) as e:
            state.title = state.topic
            state.sub_title = ""
            state.title_alternatives = []
            logger.warning("Agent1 降级使用原始选题作为标题")
            await send_progress(state.article_id, "TITLE_DONE", 15)
            return state

    async def _xhs_title(self, state: ArticleState) -> ArticleState:
        """小红书标题生成：使用少样本 Prompt"""
        category = state.xhs_category or "默认"
        persona = state.xhs_persona or "生活博主"
        prompt = (
            PromptTemplates.XHS_TITLE_PROMPT
            .replace("{topic}", state.topic)
            .replace("{category}", category)
            .replace("{persona}", persona)
        )

        try:
            content = await chat(prompt)
            titles = json.loads(content)
            if not isinstance(titles, list) or len(titles) == 0:
                raise ValueError("标题生成结果格式错误")

            state.title = titles[0]["title"]
            state.sub_title = titles[0].get("hook", "")
            state.title_alternatives = [
                {"mainTitle": t["title"], "subTitle": t.get("hook", "")}
                for t in titles[1:]
            ] if len(titles) > 1 else []

            await send_progress(state.article_id, "TITLE_DONE", 10)
            logger.info("Agent1 XHS标题生成完成, title=%s", state.title)
            return state
        except (json.JSONDecodeError, KeyError) as e:
            state.title = state.topic
            state.sub_title = ""
            state.title_alternatives = []
            logger.warning("Agent1 XHS降级使用原始选题作为标题")
            await send_progress(state.article_id, "TITLE_DONE", 10)
            return state
