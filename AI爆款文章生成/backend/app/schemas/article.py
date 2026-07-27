"""文章请求/响应模型"""

from typing import Optional
from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=1, description="选题/笔记主题")
    style: Optional[str] = Field(None, description="风格: tech/emotional/educational/humorous")
    word_count: Optional[int] = Field(2000, alias="wordCount", description="目标字数")
    image_preference: Optional[str] = Field("smart", alias="imagePreference", description="配图偏好: smart/free_only/all_ai")

    # 平台维度
    platform: Optional[str] = Field("article", description="平台: article/xiaohongshu")
    xhs_category: Optional[str] = Field("", alias="xhsCategory", description="小红书赛道")
    xhs_persona: Optional[str] = Field("", alias="xhsPersona", description="小红书人设")
    xhs_image_style: Optional[str] = Field("", alias="xhsImageStyle", description="小红书配图风格 ID")

    # 产品信息（防幻觉）
    product_name: Optional[str] = Field("", alias="productName", description="产品名称")
    product_description: Optional[str] = Field("", alias="productDescription", description="产品描述/规格")
    class Config:
        populate_by_name = True
