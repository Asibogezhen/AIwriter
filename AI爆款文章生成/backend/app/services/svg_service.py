"""SVG 示意图生成（使用 DeepSeek LLM）"""

import logging
import os
import re
import base64
import subprocess
from app.core.llm_client import chat
from app.utils.prompt_templates import PromptTemplates

logger = logging.getLogger(__name__)


class SvgService:
    async def generate(self, requirement: str, output_path: str) -> str:
        """生成 SVG 示意图并转换为 PNG"""
        prompt = PromptTemplates.SVG_PROMPT.replace("{requirement}", requirement)

        try:
            svg_code = await chat(prompt)
            svg_code = self._extract_svg(svg_code)
            if not svg_code:
                raise ValueError("未能提取 SVG 代码")

            # 保存 SVG
            svg_path = output_path.replace(".png", ".svg")
            with open(svg_path, "w", encoding="utf-8") as f:
                f.write(svg_code)

            # 尝试用 rsvg-convert 转 PNG
            try:
                subprocess.run(
                    ["rsvg-convert", "-w", "800", "-o", output_path, svg_path],
                    timeout=15,
                    check=True,
                    capture_output=True,
                )
                return f"/static/images/{self._relative_path(output_path)}"
            except (FileNotFoundError, subprocess.CalledProcessError):
                # rsvg-convert 不可用，返回 SVG 的 data URI
                logger.warning("rsvg-convert 不可用，返回 SVG data URI")
                svg_b64 = base64.b64encode(svg_code.encode()).decode()
                return f"data:image/svg+xml;base64,{svg_b64}"
        except Exception as e:
            logger.error("SVG 生成失败: %s", e)
            return f"https://picsum.photos/800/500?random={hash(requirement) % 1000}"

    @staticmethod
    def _extract_svg(text: str) -> str:
        match = re.search(r"<svg[\s\S]*?</svg>", text, re.IGNORECASE)
        if match:
            return match.group(0)
        return ""

    @staticmethod
    def _relative_path(abs_path: str) -> str:
        import os as _os
        path = abs_path.replace("\\", "/")
        if "/data/images/" in path:
            parts = path.rsplit("/data/images/", 1)
            return parts[-1]
        return _os.path.basename(abs_path)
