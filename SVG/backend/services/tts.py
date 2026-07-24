"""Edge TTS 语音合成服务。使用 Microsoft Edge 免费 TTS API。"""
import asyncio
import tempfile
import os
import subprocess
import logging
import re

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
    """生成 TTS 语音，返回音频文件路径、时长和词级时间戳。"""
    if output_path is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        output_path = tmp.name
        tmp.close()

    communicate = edge_tts.Communicate(text, voice)
    sub_maker = edge_tts.SubMaker()

    with open(output_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                sub_maker.feed(chunk)

    word_boundaries = _extract_word_boundaries(sub_maker)
    duration_sec = _probe_audio_duration(output_path)

    return {
        "audio_path": output_path,
        "duration_sec": duration_sec,
        "word_boundaries": word_boundaries,
        "voice": voice,
    }


def _extract_word_boundaries(sub_maker) -> list[dict]:
    """从 edge_tts SubMaker 提取词级时间戳。"""
    boundaries = []
    if hasattr(sub_maker, "offset") and hasattr(sub_maker, "text"):
        offsets = sub_maker.offset if hasattr(sub_maker, "offset") else []
        texts = sub_maker.text if hasattr(sub_maker, "text") else []
        for i in range(min(len(offsets), len(texts))):
            boundaries.append({
                "text": texts[i],
                "offset_sec": offsets[i] / 10_000_000.0,
            })
    return boundaries


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


def align_scenes_to_audio(full_text: str, scenes: list[dict], word_boundaries: list[dict]) -> list[dict]:
    """
    将 TTS 词级时间戳对齐到场景，返回每个场景的精确起止时间。
    用于让字幕切换与语音同步。
    """
    if not word_boundaries:
        # 无词边界时用场景时长估算
        cumulative = 0.0
        result = []
        for s in scenes:
            result.append({"start": cumulative, "end": cumulative + s["duration"]})
            cumulative += s["duration"]
        return result

    total_chars = len(full_text)
    total_duration = word_boundaries[-1]["offset_sec"] + 0.3 if word_boundaries else sum(s["duration"] for s in scenes)

    alignments = []
    search_start = 0
    for scene in scenes:
        scene_text = scene["text"].strip()
        pos = full_text.find(scene_text, search_start)
        if pos == -1:
            # 模糊匹配：取前几个字
            pos = full_text.find(scene_text[:6].strip(), search_start)
        if pos == -1:
            pos = search_start

        # 按字符比例估算时间
        start_sec = (pos / max(total_chars, 1)) * total_duration
        end_pos = pos + len(scene_text)
        end_sec = (end_pos / max(total_chars, 1)) * total_duration

        # 用词边界精细化：找最近词的时间戳
        if word_boundaries:
            char_pos = 0
            for wb in word_boundaries:
                if char_pos >= pos and start_sec == (pos / max(total_chars, 1)) * total_duration:
                    start_sec = wb["offset_sec"]
                    break
                char_pos += len(wb["text"])

        alignments.append({
            "start": round(start_sec, 2),
            "end": round(min(end_sec, total_duration), 2),
        })
        search_start = pos + len(scene_text)

    return alignments
