"""文章模型"""

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.config import settings
from app.core.database import Base
from app.models.user import make_pk


class Article(Base):
    __tablename__ = "articles"

    id = Column(String(36), primary_key=True, default=make_pk)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), default="")
    topic = Column(String(500), nullable=False)
    style = Column(String(100), default="")
    platform = Column(String(20), default="article")
    word_count = Column(Integer, default=2000)
    status = Column(String(20), default="pending")
    markdown = Column(Text, default="")
    outline = Column(Text, nullable=True)  # JSON string
    images = Column(Text, nullable=True)   # JSON string
    rendered_html = Column(Text, default="")
    progress = Column(Text, default="{}")  # JSON string
    error_message = Column(Text, default="")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
