"""文章状态与阶段枚举"""

from enum import Enum
from typing import Optional


class ArticleStatusEnum(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class ArticlePhaseEnum(str, Enum):
    PENDING = "PENDING"
    TITLE_GENERATING = "TITLE_GENERATING"
    OUTLINE_GENERATING = "OUTLINE_GENERATING"
    CONTENT_GENERATING = "CONTENT_GENERATING"
    IMAGE_ANALYZING = "IMAGE_ANALYZING"
    IMAGE_GENERATING = "IMAGE_GENERATING"
    MERGING = "MERGING"


class ArticleStyleEnum(str, Enum):
    TECH = "tech"
    EMOTIONAL = "emotional"
    EDUCATIONAL = "educational"
    HUMOROUS = "humorous"

    @classmethod
    def is_valid(cls, value: Optional[str]) -> bool:
        if not value:
            return True
        return value in [e.value for e in cls]
