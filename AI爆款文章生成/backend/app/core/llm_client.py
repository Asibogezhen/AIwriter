"""DeepSeek LLM 客户端 (OpenAI 兼容接口)"""

from typing import AsyncGenerator
from openai import AsyncOpenAI
from app.config import settings

_client = AsyncOpenAI(
    api_key=settings.deepseek_api_key,
    base_url=settings.deepseek_base_url,
)


async def chat(prompt: str, system_prompt: str = "") -> str:
    """非流式调用"""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = await _client.chat.completions.create(
        model=settings.deepseek_model,
        messages=messages,
        temperature=0.8,
    )
    return response.choices[0].message.content


async def stream_chat(prompt: str, system_prompt: str = "") -> AsyncGenerator[str, None]:
    """流式调用"""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    stream = await _client.chat.completions.create(
        model=settings.deepseek_model,
        messages=messages,
        temperature=0.8,
        stream=True,
    )

    async for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
