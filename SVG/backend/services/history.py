"""生成历史持久化存储。每次生成自动保存为 JSON 文件。"""
import json
import os
import uuid
from datetime import datetime, timezone, timedelta

HISTORY_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "history"))
MAX_ENTRIES = 50  # 最多保留条数

_tz = timezone(timedelta(hours=8))  # 北京时间


def _ensure_dir():
    os.makedirs(HISTORY_DIR, exist_ok=True)


def save_generation(data: dict) -> str:
    """保存一次生成结果，返回 ID。自动清理超量旧记录。"""
    _ensure_dir()
    gid = uuid.uuid4().hex[:12]
    entry = {
        "id": gid,
        "created_at": datetime.now(_tz).isoformat(),
        "prompt": data.get("prompt", ""),
        "title": data.get("title", ""),
        "full_text": data.get("full_text", ""),
        "scenes": data.get("scenes", []),
        "total_duration": data.get("total_duration", 0),
        "combined_html": data.get("combined_html", ""),
        "scenes_html": data.get("scenes_html", []),
        "width": data.get("width", 1920),
        "height": data.get("height", 1080),
        "aspect": data.get("aspect", "16:9"),
        "style": data.get("style", "none"),
    }
    path = os.path.join(HISTORY_DIR, f"{gid}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entry, f, ensure_ascii=False)
    _prune()
    return gid


def list_history() -> list[dict]:
    """列出所有历史记录（不含 HTML，仅摘要）。"""
    _ensure_dir()
    entries = []
    for name in os.listdir(HISTORY_DIR):
        if not name.endswith(".json"):
            continue
        path = os.path.join(HISTORY_DIR, name)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            entries.append({
                "id": data["id"],
                "created_at": data.get("created_at", ""),
                "prompt": data.get("prompt", ""),
                "title": data.get("title", ""),
                "scene_count": len(data.get("scenes", [])),
                "total_duration": data.get("total_duration", 0),
                "style": data.get("style", "none"),
                "aspect": data.get("aspect", "16:9"),
            })
        except Exception:
            pass
    entries.sort(key=lambda e: e["created_at"], reverse=True)
    return entries


def get_history(gid: str) -> dict | None:
    """获取完整历史记录（含 HTML）。"""
    path = os.path.join(HISTORY_DIR, f"{gid}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def delete_history(gid: str) -> bool:
    """删除一条历史记录。"""
    path = os.path.join(HISTORY_DIR, f"{gid}.json")
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


def _prune():
    """保留最近 MAX_ENTRIES 条记录。"""
    entries = []
    for name in os.listdir(HISTORY_DIR):
        if name.endswith(".json"):
            p = os.path.join(HISTORY_DIR, name)
            entries.append((os.path.getmtime(p), p))
    entries.sort(reverse=True)
    for _, p in entries[MAX_ENTRIES:]:
        try:
            os.remove(p)
        except Exception:
            pass
