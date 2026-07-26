from fastapi import APIRouter, HTTPException
from backend.services.history import list_history, get_history, delete_history

router = APIRouter()


@router.get("/history")
async def api_list_history():
    """列出所有历史记录（摘要）。"""
    return list_history()


@router.get("/history/{gid}")
async def api_get_history(gid: str):
    """获取一条完整历史记录。"""
    entry = get_history(gid)
    if entry is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    return entry


@router.delete("/history/{gid}")
async def api_delete_history(gid: str):
    """删除一条历史记录。"""
    if not delete_history(gid):
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"status": "ok"}
