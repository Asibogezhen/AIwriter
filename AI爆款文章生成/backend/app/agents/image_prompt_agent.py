"""配图需求分析 Agent"""

import json
import logging
from app.agents.base import BaseAgent, ArticleState
from app.core.llm_client import chat
from app.core.sse_manager import send_progress
from app.utils.prompt_templates import PromptTemplates

logger = logging.getLogger(__name__)


class ImagePromptAgent(BaseAgent):
    async def execute(self, state: ArticleState) -> ArticleState:
        logger.info("Agent4 配图分析开始, articleId=%s platform=%s", state.article_id, state.platform)
        await send_progress(state.article_id, "IMAGE_ANALYZING", 55 if state.platform != "xiaohongshu" else 40)

        if state.platform == "xiaohongshu":
            return await self._xhs_images(state)

        is_free_only = (state.image_preference == "free_only") or (not state.is_vip)
        free_hint = PromptTemplates.get_free_only_hint(is_free_only)

        prompt = (
            PromptTemplates.IMAGE_PROMPT
            .replace("{mainTitle}", state.title)
            .replace("{content}", state.content)
            .replace("{imagePreference}", state.image_preference)
            .replace("{freeOnlyHint}", free_hint)
        )

        try:
            content = await chat(prompt)
            data = self._parse_json(content)
            requirements = data.get("imageRequirements", []) if data else []

            if is_free_only:
                requirements = [r for r in requirements if r.get("imageSource") != "QWEN_IMAGE"]

            # 降级：LLM 返回空或解析失败，生成默认配图
            if not requirements:
                requirements = self._default_requirements(state.content, state.is_vip)

            # 后处理：强制配图多样性
            requirements = self._ensure_diversity(requirements, state.is_vip)

            # 确定性插入占位符
            state.content_with_placeholders = self._insert_placeholders(
                state.content, requirements
            )

            state.image_requirements = requirements
            await send_progress(state.article_id, "IMAGE_PROMPT_DONE", 65)
            logger.info("Agent4 配图分析完成, requirements=%d", len(requirements))
            return state
        except Exception as e:
            logger.warning("Agent4 配图分析失败: %s", e)
            requirements = self._default_requirements(state.content, state.is_vip)
            state.content_with_placeholders = self._insert_placeholders(
                state.content, requirements
            )
            state.image_requirements = requirements
            await send_progress(state.article_id, "IMAGE_PROMPT_DONE", 65)
            return state

    async def _xhs_images(self, state: ArticleState) -> ArticleState:
        """小红书配图：全 AI 生图，竖版 3:4，风格感知"""
        from app.utils.xiaohongshu_styles import get_style_by_id

        style = get_style_by_id(state.xhs_image_style) or get_style_by_id("bold")
        prompt = (
            PromptTemplates.XHS_IMAGE_PROMPT
            .replace("{title}", state.title)
            .replace("{content}", state.content[:2000])
            .replace("{styleName}", style["name"])
            .replace("{styleDescription}", style["description"])
            .replace("{palette}", style["palette"])
            .replace("{stylePrompt}", style["prompt_style"])
        )

        try:
            content = await chat(prompt)
            data = self._parse_json(content)
            requirements = data.get("imageRequirements", []) if data else []

            if not requirements:
                requirements = self._xhs_default_requirements(state, style)

            # 全部强制 QWEN_IMAGE
            for r in requirements:
                r["imageSource"] = "QWEN_IMAGE"

            state.content_with_placeholders = self._insert_placeholders(
                state.content, requirements
            )
            state.image_requirements = requirements
            await send_progress(state.article_id, "IMAGE_PROMPT_DONE", 50)
            logger.info("Agent4 XHS配图分析完成, requirements=%d", len(requirements))
            return state
        except Exception as e:
            logger.warning("Agent4 XHS配图分析失败: %s", e)
            requirements = self._xhs_default_requirements(state, style)
            state.content_with_placeholders = self._insert_placeholders(
                state.content, requirements
            )
            state.image_requirements = requirements
            await send_progress(state.article_id, "IMAGE_PROMPT_DONE", 50)
            return state

    def _xhs_default_requirements(self, state: ArticleState, style: dict) -> list[dict]:
        """小红书默认配图方案：封面 + 2-3 张内容配图"""
        style_prompt = style["prompt_style"]
        reqs = [
            {
                "position": 1,
                "type": "cover",
                "sectionTitle": "",
                "imageSource": "QWEN_IMAGE",
                "keywords": "",
                "prompt": (
                    f"Xiaohongshu cover image, vertical 3:4 aspect ratio, "
                    f"{style_prompt}, "
                    f"editorial layout with clean area for text overlay on upper half, "
                    f"inspired by the theme '{state.title}', "
                    f"eye-catching composition, magazine cover style"
                ),
            }
        ]

        import re
        sections = re.findall(r"^##\s+(.+)$", state.content, re.MULTILINE)
        titles = [s for s in sections[:3]] if sections else ["内容配图"]

        for i, section_title in enumerate(titles):
            reqs.append({
                "position": i + 2,
                "type": "photo",
                "sectionTitle": section_title,
                "imageSource": "QWEN_IMAGE",
                "keywords": "",
                "prompt": (
                    f"Xiaohongshu content illustration, vertical 3:4, "
                    f"{style_prompt}, "
                    f"inspired by '{section_title}', aesthetic editorial photography, "
                    f"soft natural lighting, high quality"
                ),
            })

        return reqs

    @staticmethod
    def _parse_json(raw: str) -> dict | None:
        """从 LLM 返回中提取 JSON，容错处理"""
        import re
        raw = raw.strip()
        # 尝试提取 markdown 代码块中的 JSON
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
        if m:
            raw = m.group(1).strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # 尝试修复常见问题：缺少最外层大括号
            if not raw.startswith("{"):
                raw = "{" + raw
            if not raw.endswith("}"):
                raw = raw + "}"
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return None

    def _default_requirements(self, content: str, is_vip: bool) -> list[dict]:
        """当 LLM 无法返回有效配图方案时，生成默认配图"""
        import re
        sections = re.findall(r"^##\s+(.+)$", content, re.MULTILINE)

        reqs = [
            {
                "position": 1,
                "type": "cover",
                "sectionTitle": "",
                "imageSource": "QWEN_IMAGE" if is_vip else "PEXELS",
                "keywords": "technology abstract cover" if not is_vip else "",
                "prompt": "A stunning futuristic editorial illustration, modern clean design, vibrant colors" if is_vip else "",
            }
        ]

        # 为每个章节生成配图需求
        for i, title in enumerate(sections[:4]):
            if i == 0:
                source = "SVG"
                prompt = f"概念示意图：{title}"
                keywords = ""
            elif i == 1:
                source = "PEXELS"
                prompt = ""
                keywords = " ".join(title.split()[:3]) if title else "technology"
            else:
                source = "PEXELS"
                prompt = ""
                keywords = "business technology"

            reqs.append({
                "position": i + 2,
                "type": "diagram" if source == "SVG" else "photo",
                "sectionTitle": title,
                "imageSource": source,
                "keywords": keywords,
                "prompt": prompt,
            })

        return reqs

    def _insert_placeholders(self, content: str, requirements: list[dict]) -> str:
        """在每个章节末尾（下一个 ## 之前）插入配图占位符"""
        import re
        # 找到所有 ## 标题的位置
        sections = list(re.finditer(r"^##\s+.+$", content, re.MULTILINE))
        # 过滤掉封面图（position=1）
        in_content = [r for r in requirements if r.get("position", 0) > 1]
        if not in_content or not sections:
            return content

        # 从后往前插入，避免位置偏移
        result = content
        for i, req in enumerate(reversed(in_content)):
            placeholder = f"\n\n{{{{IMAGE_PLACEHOLDER_{i + 1}}}}}\n\n"
            # 找到对应的章节位置（从后往前对应章节）
            section_idx = len(sections) - 1 - i
            if section_idx >= 0:
                pos = sections[section_idx].end()
                result = result[:pos] + placeholder + result[pos:]
                req["placeholderId"] = f"{{{{IMAGE_PLACEHOLDER_{i + 1}}}}}"

        return result

    def _ensure_diversity(self, reqs: list[dict], is_vip: bool) -> list[dict]:
        """确保配图来源多样性：封面优先 AI 生图，至少 1 张 SVG"""
        if len(reqs) < 2:
            return reqs

        has_svg = any(r.get("imageSource") == "SVG" for r in reqs)
        has_pexels = any(r.get("imageSource") == "PEXELS" for r in reqs)

        # 封面强制 AI 生图（VIP）
        if is_vip and reqs and reqs[0].get("type") == "cover":
            reqs[0]["imageSource"] = "QWEN_IMAGE"

        # 没有 SVG → 找一张非封面图改成 SVG
        if not has_svg:
            for r in reqs[1:]:
                if r.get("imageSource") != "QWEN_IMAGE":
                    r["imageSource"] = "SVG"
                    r["prompt"] = f"示意图：{r.get('sectionTitle', '内容说明')}"
                    r["keywords"] = ""
                    break

        # 没有 PEXELS → 找一张非封面非 SVG 的改成 PEXELS
        if not has_pexels:
            for r in reqs[1:]:
                if r.get("imageSource") == "SVG":
                    r["imageSource"] = "PEXELS"
                    r["keywords"] = r.get("prompt", "illustration")[:50]
                    r["prompt"] = ""
                    break

        return reqs
