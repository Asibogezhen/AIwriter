"""搜索 Agent — 根据大纲各章节搜索最新资料"""

import logging
from app.agents.base import BaseAgent, ArticleState
from app.core.sse_manager import send_event, send_progress
from app.services.search_service import search

logger = logging.getLogger(__name__)


class SearchAgent(BaseAgent):
    async def execute(self, state: ArticleState) -> ArticleState:
        # 小红书模式跳过搜索（小红书重个人经验，不重资料引用）
        if state.platform == "xiaohongshu":
            logger.info("Agent2.5 XHS模式跳过搜索")
            await send_progress(state.article_id, "SEARCH_DONE", 20)
            return state

        logger.info("Agent2.5 搜索开始, articleId=%s", state.article_id)
        await send_progress(state.article_id, "SEARCHING", 32)
        await send_event(state.article_id, "search_start")

        # 取前 4 个章节 + 用主标题作为全局搜索
        queries = [state.title]
        for s in state.outline[:4]:
            queries.append(f"{state.topic} {s.get('title', '')}")

        all_results: list[dict] = []
        for i, q in enumerate(queries):
            results = await search(q, max_results=3)
            section_title = "全局概述" if i == 0 else state.outline[i - 1].get("title", q)
            all_results.append({
                "sectionTitle": section_title,
                "results": results,
            })
            await send_event(state.article_id, "search_chunk", {
                "sectionTitle": section_title,
                "results": results,
            })
            logger.info("搜索完成: %s, results=%d", section_title, len(results))

        state.search_results = all_results
        await send_event(state.article_id, "search_done", {"totalSections": len(all_results)})
        await send_progress(state.article_id, "SEARCH_DONE", 35)
        logger.info("Agent2.5 搜索完成, queries=%d", len(queries))
        return state
