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


def _clean_text(text: str) -> str:
    """移除中文标点和空白，得到纯净的朗读文本。词边界不含标点，需要对齐。"""
    return re.sub(r'[。！？；，、：""''「」『』【】\s\n\r　]', '', text)


def align_scenes_to_audio(full_text: str, scenes: list[dict], word_boundaries: list[dict]) -> list[dict]:
    """
    将 TTS 词级时间戳对齐到场景，返回每个场景的精确起止时间。
    按场景文本在全文中的去标点字符占比分配时长，确保总和等于音频时长。
    """
    if not word_boundaries:
        cumulative = 0.0
        result = []
        for s in scenes:
            result.append({"start": cumulative, "end": cumulative + s["duration"]})
            cumulative += s["duration"]
        return result

    audio_dur = word_boundaries[-1]["offset_sec"] + 0.3
    clean_full = _clean_text(full_text)
    total_clean = max(len(clean_full), 1)

    alignments = []
    search_start = 0
    for scene in scenes:
        scene_text = scene["text"].strip()
        # 在全文（无标点版）中定位场景文本
        clean_scene = _clean_text(scene_text)
        pos = clean_full.find(clean_scene, search_start)
        if pos == -1:
            pos = search_start

        start_sec = (pos / total_clean) * audio_dur
        end_pos = pos + len(clean_scene)
        end_sec = (end_pos / total_clean) * audio_dur

        # 用词边界精修开始时间
        wb_pos = 0
        for wb in word_boundaries:
            if wb_pos >= pos:
                start_sec = wb["offset_sec"]
                break
            wb_pos += len(wb["text"])

        alignments.append({
            "start": round(start_sec, 2),
            "end": round(min(end_sec, audio_dur), 2),
        })
        search_start = end_pos

    return alignments


def generate_ass(word_boundaries: list[dict], full_text: str) -> str:
    """
    根据 TTS 词级时间戳生成 ASS 字幕（单行、底部居中、无自动换行）。
    用 ASS 而非 SRT：ASS 原生控制 WrapStyle，不依赖 FFmpeg force_style 解析。
    """
    if not word_boundaries:
        return ""

    sentences = _split_sentences(full_text)

    header = """[Script Info]
Title: 字幕
ScriptType: v4.00+
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Microsoft YaHei,24,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,3,2,2,10,10,50,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    dialogues = []
    seq = 0
    clean_pos = 0
    wb_idx = 0
    wb_char_pos = 0

    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        clean_sent = _clean_text(sent)
        if not clean_sent:
            continue

        # 跳过当前句子之前的词
        while wb_idx < len(word_boundaries) and wb_char_pos + len(word_boundaries[wb_idx]["text"]) <= clean_pos:
            wb_char_pos += len(word_boundaries[wb_idx]["text"])
            wb_idx += 1

        if wb_idx >= len(word_boundaries):
            break

        wb_start = word_boundaries[wb_idx]["offset_sec"]

        # 推进到句子末尾，并消耗末尾词（避免下一句重复使用）
        clean_end = clean_pos + len(clean_sent)
        while wb_idx < len(word_boundaries) and wb_char_pos + len(word_boundaries[wb_idx]["text"]) < clean_end:
            wb_char_pos += len(word_boundaries[wb_idx]["text"])
            wb_idx += 1

        if wb_idx < len(word_boundaries):
            wb_end = word_boundaries[wb_idx]["offset_sec"] + 0.15
            # 消耗末尾词，下一句从下一个词开始
            wb_char_pos += len(word_boundaries[wb_idx]["text"])
            wb_idx += 1
        else:
            wb_end = word_boundaries[-1]["offset_sec"] + 0.3

        if wb_start and wb_end and wb_end > wb_start:
            dialogues.append(_format_ass_dialogue(wb_start, wb_end, sent))
            seq += 1

        clean_pos = clean_end

    if not dialogues:
        return ""

    return header + "\n".join(dialogues) + "\n"


def _split_sentences(text: str) -> list[str]:
    """
    按句末标点断句，每句 ≤16 字，保证单行字幕。
    长句在逗号处拆分，超长无逗号句则按 16 字硬切。
    """
    raw = re.split(r'(?<=[。！？\n])', text)
    result = []

    for segment in raw:
        segment = segment.strip()
        if not segment:
            continue

        if len(segment) <= 16:
            result.append(segment)
        else:
            sub_parts = re.split(r'(?<=[，；、])', segment)
            buffer = ""
            for part in sub_parts:
                part = part.strip()
                if not part:
                    continue
                if len(buffer + part) <= 16:
                    buffer += part
                else:
                    if buffer.strip():
                        result.append(buffer.strip())
                    if len(part) > 16:
                        for i in range(0, len(part), 16):
                            chunk = part[i:i+16]
                            if chunk.strip():
                                result.append(chunk.strip())
                        buffer = ""
                    else:
                        buffer = part
            if buffer.strip():
                result.append(buffer.strip())

    return [s for s in result if s.strip()]


def _format_ass_dialogue(start: float, end: float, text: str) -> str:
    """格式化单条 ASS Dialogue。时间格式 H:MM:SS.cc（百分秒）。"""
    def _fmt_ass(sec: float) -> str:
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = int(sec % 60)
        cs = int((sec % 1) * 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    return f"Dialogue: 0,{_fmt_ass(start)},{_fmt_ass(end)},Default,,0,0,0,,{text}"
