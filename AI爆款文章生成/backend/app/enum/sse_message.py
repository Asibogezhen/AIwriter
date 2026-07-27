"""SSE 消息类型与图片来源枚举"""

from enum import Enum


class SseMessageTypeEnum(str, Enum):
    TITLE_DONE = "title_done"
    OUTLINE_DONE = "outline_done"
    SEARCH_START = "search_start"
    SEARCH_CHUNK = "search_chunk"
    SEARCH_DONE = "search_done"
    CONTENT_START = "content_start"
    CONTENT_CHUNK = "content_chunk"
    CONTENT_DONE = "content_done"
    IMAGE_PROMPT_DONE = "image_prompt_done"
    IMAGE_GEN_PROGRESS = "image_gen_progress"
    IMAGE_GEN_DONE = "image_gen_done"
    RENDER_DONE = "render_done"
    PROGRESS = "progress"
    ERROR = "error"
    DONE = "done"


class ImageSourceEnum(str, Enum):
    PEXELS = "PEXELS"
    SVG = "SVG"
    QWEN_IMAGE = "QWEN_IMAGE"
