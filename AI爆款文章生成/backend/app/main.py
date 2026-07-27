"""FastAPI 主应用入口"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.core.database import database, engine, Base
from app.core.redis import init_redis, close_redis
from app.api.v1.auth import router as auth_router
from app.api.v1.articles import router as articles_router
from app.api.v1.vip import router as vip_router
from app.api.v1.admin import router as admin_router
from app.exceptions import BusinessException, ErrorCode

# 确保模型被导入，以便 create_all 能发现它们
import app.models  # noqa: F811


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    # SQLite 兼容：为已有表新增列
    _migrate_sqlite()
    await database.connect()
    await init_redis()
    yield
    await database.disconnect()
    await close_redis()


app = FastAPI(
    title="AI 爆款文章创作器",
    description="基于多智能体编排的 AI 文章创作平台",
    version="0.1.0",
    lifespan=lifespan,
)

# 确保图片目录存在
images_dir = settings.images_dir
if isinstance(images_dir, str) and not os.path.isabs(images_dir):
    images_dir = os.path.join(os.path.dirname(__file__), "..", images_dir)
os.makedirs(images_dir, exist_ok=True)
app.mount("/static/images", StaticFiles(directory=images_dir), name="static_images")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:5276"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException):
    return JSONResponse(
        status_code=200,
        content={"code": exc.error_code.code, "data": None, "message": exc.message},
    )


@app.get("/api/health")
async def health():
    return {"status": "ok"}


app.include_router(auth_router, prefix="/api")
app.include_router(articles_router, prefix="/api")
app.include_router(vip_router, prefix="/api")
app.include_router(admin_router, prefix="/api")


def _migrate_sqlite():
    """SQLite 兼容迁移：为已有表添加新列（如果不存在）"""
    if settings.db_type != "sqlite":
        return
    import logging
    from sqlalchemy import text
    logger = logging.getLogger("migration")
    migrations = [
        "ALTER TABLE articles ADD COLUMN platform VARCHAR(20) DEFAULT 'article'",
    ]
    with engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
                logger.info("迁移成功: %s", sql)
            except Exception as e:
                # 列已存在（SQLite 不支持 IF NOT EXISTS）或其他非致命错误
                logger.warning("迁移跳过: %s, 原因: %s", sql, e)

@app.get("/")
async def root():
    return {"message": "AI 爆款文章创作器", "version": "0.1.0", "docs": "/docs"}
