"""Agent 基类与共享状态"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class ArticleState:
    """Agent 间共享状态"""
    article_id: str = ""
    topic: str = ""
    style: str = ""
    word_count: int = 2000
    image_preference: str = "smart"  # smart / free_only / all_ai
    is_vip: bool = False

    # 平台维度
    platform: str = "article"  # article / xiaohongshu
    xhs_category: str = ""    # 小红书赛道
    xhs_persona: str = ""     # 小红书人设
    xhs_image_style: str = "" # 小红书配图风格 ID

    # 产品信息（防幻觉）
    product_name: str = ""
    product_description: str = ""

    # 阶段1 产出
    title: str = ""
    sub_title: str = ""
    title_alternatives: list = field(default_factory=list)

    # 阶段2 产出
    outline: list = field(default_factory=list)  # [{section, title, points}]

    # 阶段2.5 产出
    search_results: list = field(default_factory=list)  # [{sectionTitle, results: [{title, url, content}]}]

    # 阶段3 产出
    content: str = ""

    # 阶段4 产出
    image_requirements: list = field(default_factory=list)
    content_with_placeholders: str = ""

    # 阶段5 产出
    image_urls: list = field(default_factory=list)  # [{position, url, method}]

    # 阶段6 产出
    full_content: str = ""

    error: str = ""


class BaseAgent(ABC):
    @abstractmethod
    async def execute(self, state: ArticleState) -> ArticleState:
        """执行 Agent 逻辑，返回更新后的 state"""
        ...
