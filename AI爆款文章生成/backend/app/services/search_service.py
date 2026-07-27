"""Tavily 搜索服务"""

from tavily import TavilyClient
from app.config import settings

_client = None


def _get_client() -> TavilyClient | None:
    global _client
    if _client is None and settings.tavily_api_key:
        _client = TavilyClient(api_key=settings.tavily_api_key)
    return _client


async def search(query: str, max_results: int = 5) -> list[dict]:
    """搜索指定关键词，返回 [{title, url, content}]"""
    client = _get_client()
    if client is None:
        return _fallback_results(query)

    try:
        resp = client.search(query=query, max_results=max_results, search_depth="basic")
        return [
            {"title": r["title"], "url": r["url"], "content": r["content"]}
            for r in resp.get("results", [])
        ]
    except Exception:
        return _fallback_results(query)


def _fallback_results(query: str) -> list[dict]:
    return [{"title": f"关于「{query}」的说明", "url": "", "content": f"请基于你对「{query}」的知识撰写相关内容。"}]
