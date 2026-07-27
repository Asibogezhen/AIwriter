"""图文合成 Agent"""

import logging
import os
from app.agents.base import BaseAgent, ArticleState
from app.core.sse_manager import send_event, send_progress

logger = logging.getLogger(__name__)


class RenderAgent(BaseAgent):
    async def execute(self, state: ArticleState) -> ArticleState:
        logger.info("Agent6 图文合成开始, articleId=%s", state.article_id)
        await send_progress(state.article_id, "MERGING", 90)

        # 使用带占位符的正文
        content = state.content_with_placeholders or state.content

        if state.image_urls:
            # 按 position 逆序替换
            sorted_urls = sorted(state.image_urls, key=lambda x: x.get("position", 0), reverse=True)
            for img in sorted_urls:
                pos = img.get("position", 0)
                url = img.get("url", "")
                pid = img.get("placeholderId", "")

                if url:
                    markdown_img = f"![{img.get('sectionTitle', '')}]({url})"
                    if pid and pid in content:
                        content = content.replace(pid, markdown_img)
                    elif pos == 1:
                        # 封面图插入到正文最前面
                        content = f"{markdown_img}\n\n{content}"

        state.full_content = content

        await send_event(state.article_id, "render_done", {"fullContent": content})
        await send_progress(state.article_id, "DONE", 100)
        logger.info("Agent6 图文合成完成")
        return state
