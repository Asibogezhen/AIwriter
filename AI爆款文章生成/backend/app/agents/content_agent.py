"""正文生成 Agent（流式输出）"""

import json
import logging
from app.agents.base import BaseAgent, ArticleState
from app.core.llm_client import stream_chat
from app.core.sse_manager import send_event, send_progress
from app.utils.prompt_templates import PromptTemplates

logger = logging.getLogger(__name__)


class ContentAgent(BaseAgent):
    async def execute(self, state: ArticleState) -> ArticleState:
        logger.info("Agent3 正文生成开始, articleId=%s platform=%s", state.article_id, state.platform)
        await send_progress(state.article_id, "CONTENT_GENERATING", 38 if state.platform != "xiaohongshu" else 20)
        await send_event(state.article_id, "content_start")

        if state.platform == "xiaohongshu":
            prompt = self._build_xhs_prompt(state)
        elif state.search_results:
            prompt = self._build_prompt_with_search(state, json.dumps(state.outline, ensure_ascii=False))
            prompt += PromptTemplates.get_style_prompt(state.style)
        else:
            prompt = self._build_prompt_basic(state, json.dumps(state.outline, ensure_ascii=False))
            prompt += PromptTemplates.get_style_prompt(state.style)

        # 注入产品信息（防幻觉）- XHS 路径已在 _build_xhs_prompt 中注入
        if state.platform != "xiaohongshu" and (state.product_name or state.product_description):
            prompt = self._inject_product_info(prompt, state)

        full_text = ""
        chunk_buffer = ""
        chunk_counter = 0

        try:
            async for token in stream_chat(prompt):
                full_text += token
                chunk_buffer += token
                chunk_counter += 1
                if chunk_counter >= 10 or "\n" in chunk_buffer:
                    await send_event(state.article_id, "content_chunk", {"text": chunk_buffer})
                    chunk_buffer = ""
                    chunk_counter = 0

            if chunk_buffer:
                await send_event(state.article_id, "content_chunk", {"text": chunk_buffer})

            state.content = full_text
            await send_event(state.article_id, "content_done")
            pct = 35 if state.platform == "xiaohongshu" else 50
            await send_progress(state.article_id, "CONTENT_DONE", pct)
            logger.info("Agent3 正文生成完成, length=%d", len(full_text))
            return state
        except Exception as e:
            logger.error("Agent3 正文生成失败: %s", e)
            raise

    def _build_xhs_prompt(self, state: ArticleState) -> str:
        category = state.xhs_category or "默认"
        persona = state.xhs_persona or "生活博主"
        examples = PromptTemplates.get_xhs_examples(category)
        prompt = (
            PromptTemplates.XHS_CONTENT_PROMPT
            .replace("{category}", category)
            .replace("{persona}", persona)
            .replace("{examples}", examples)
            .replace("{title}", state.title)
            .replace("{topic}", state.topic)
        )
        return self._inject_product_info(prompt, state)

    def _inject_product_info(self, prompt: str, state: ArticleState) -> str:
        """如果用户提供了产品信息，注入到 prompt 中防止 LLM 幻觉"""
        if not state.product_name and not state.product_description:
            return prompt

        parts = ["\n\n⚠️ 重要：你正在介绍一个真实产品，请基于以下信息写作，不要编造任何规格、价格、效果：\n"]
        if state.product_name:
            parts.append(f"产品名称：{state.product_name}")
        if state.product_description:
            parts.append(f"产品信息：{state.product_description}")
        parts.append("\n注意：只写你确定的信息，不确定的不要编。如果某些信息缺失，就跳过不写。")
        return prompt + "\n".join(parts)

    def _build_prompt_with_search(self, state: ArticleState, outline_json: str) -> str:
        context_parts = []
        for sr in state.search_results:
            if not sr["results"]:
                continue
            lines = [f"### {sr['sectionTitle']}"]
            for r in sr["results"]:
                lines.append(f"- [{r['title']}]({r['url']})\n  {r['content']}")
            context_parts.append("\n".join(lines))
        search_context = "\n\n".join(context_parts)

        return (
            PromptTemplates.CONTENT_WITH_SEARCH_PROMPT
            .replace("{mainTitle}", state.title)
            .replace("{subTitle}", state.sub_title)
            .replace("{outline}", outline_json)
            .replace("{wordCount}", str(state.word_count))
            .replace("{style}", self._style_label(state.style))
            .replace("{searchContext}", search_context)
        )

    def _build_prompt_basic(self, state: ArticleState, outline_json: str) -> str:
        return (
            PromptTemplates.CONTENT_PROMPT
            .replace("{mainTitle}", state.title)
            .replace("{subTitle}", state.sub_title)
            .replace("{outline}", outline_json)
            .replace("{wordCount}", str(state.word_count))
            .replace("{style}", self._style_label(state.style))
        )

    @staticmethod
    def _style_label(style: str) -> str:
        labels = {"tech": "科技专业", "emotional": "情感故事", "educational": "教育科普", "humorous": "轻松幽默"}
        return labels.get(style, "新媒体")
