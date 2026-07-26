from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.routers.generate import router as generate_router
from backend.routers.history import router as history_router

app = FastAPI(title="AI动画视频生成器")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate_router, prefix="/api")
app.include_router(history_router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
