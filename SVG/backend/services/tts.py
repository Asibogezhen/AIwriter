"""Edge TTS 语音合成服务。使用 Microsoft Edge 免费 TTS API。"""
import asyncio
import tempfile
import os
import subprocess
import logging

import edge_tts

logger = logging.getLogger(__name__)

VOICE_MAP = {
    "zh-CN-XiaoxiaoNeural": "晓晓 (温暖女声)",
    "zh-CN-YunxiNeural": "云希 (活泼男声)",
    "zh-CN-XiaoyiNeural": "晓伊 (活泼女声)",
    "zh-CN-YunjianNeural": "云健 (激情男声)",
    "zh-CN-YunxiaNeural": "云夏 (可爱童声)",
}

DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"


async def generate_tts(
    text: str,
    voice: str = DEFAULT_VOICE,
    output_path: str | None = None,
) -> dict:
    """生成 TTS 语音，返回音频文件路径和时长信息。"""
    if output_path is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        output_path = tmp.name
        tmp.close()

    communicate = edge_tts.Communicate(text, voice)

    with open(output_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])

    duration_sec = _probe_audio_duration(output_path)

    return {
        "audio_path": output_path,
        "duration_sec": duration_sec,
        "voice": voice,
    }


def _probe_audio_duration(filepath: str) -> float:
    """用 FFprobe 获取音频实际时长。"""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                filepath,
            ],
            capture_output=True, text=True, timeout=10,
        )
        return float(result.stdout.strip())
    except Exception as e:
        logger.warning(f"获取音频时长失败: {e}")
        return 0.0
