"""应用配置管理"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    # 服务器
    server_port: int = 8000
    server_host: str = "0.0.0.0"

    # 数据库类型: postgres / sqlite
    db_type: str = "sqlite"

    # PostgreSQL（当 db_type=postgres 时使用）
    db_host: str = "db"
    db_port: int = 5432
    db_name: str = "ai_article"
    db_user: str = "postgres"
    db_password: str = "postgres"

    # Redis（可选）
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    use_redis: bool = False

    # JWT
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 15
    jwt_refresh_expire_days: int = 7

    # AI
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # Qwen-Image（阿里云 DashScope）
    dashscope_api_key: str = ""
    dashscope_model: str = "qwen-image-max-2025-12-30"

    # Pexels
    pexels_api_key: str = ""

    # Tavily Search
    tavily_api_key: str = ""

    # 存储
    images_dir: str = "./data/images"

    # 密码加密盐值
    password_salt: str = "ai-passage-creator-salt"

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        if self.db_type == "sqlite":
            db_path = BASE_DIR / "data" / "app.db"
            db_path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite+aiosqlite:///{db_path}"
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def database_url_sync(self) -> str:
        if self.db_type == "sqlite":
            db_path = BASE_DIR / "data" / "app.db"
            db_path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite:///{db_path}"
        return f"postgresql+psycopg2://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


settings = Settings()
