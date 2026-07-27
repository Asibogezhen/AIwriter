"""大纲生成 Agent"""

import json
import logging
from app.agents.base import BaseAgent, ArticleState
from app.core.llm_client import chat
from app.core.sse_manager import send_progress
from app.utils.prompt_templates import PromptTemplates

logger = logging.getLogger(__name__)


class OutlineAgent(BaseAgent):
    async def execute(self, state: ArticleState) -> ArticleState:
        # 小红书模式跳过提纲，直接用标题生成正文
        if state.platform == "xiaohongshu":
            logger.info("Agent2 XHS模式跳过提纲生成")
            await send_progress(state.article_id, "OUTLINE_DONE", 15)
            return state

        logger.info("Agent2 大纲生成开始, articleId=%s", state.article_id)
        await send_progress(state.article_id, "OUTLINE_GENERATING", 20)

        prompt = (
            PromptTemplates.OUTLINE_PROMPT
            .replace("{mainTitle}", state.title)
            .replace("{subTitle}", state.sub_title)
            .replace("{wordCount}", str(state.word_count))
        )
        prompt += PromptTemplates.get_style_prompt(state.style)

        try:
            content = await chat(prompt)
            data = json.loads(content)
            state.outline = data.get("sections", [])
            if not state.outline:
                raise ValueError("大纲为空")

            await send_progress(state.article_id, "OUTLINE_DONE", 30)
            logger.info("Agent2 大纲生成完成, sections=%d", len(state.outline))
            return state
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # 降级：生成简单大纲
            state.outline = [
                {"section": 1, "title": "引言", "points": ["背景介绍", "问题引入"]},
                {"section": 2, "title": "核心内容", "points": ["主要观点", "案例分析"]},
                {"section": 3, "title": "总结", "points": ["要点回顾", "行动建议"]},
            ]
            logger.warning("Agent2 降级使用默认大纲")
            await send_progress(state.article_id, "OUTLINE_DONE", 30)
            return state
