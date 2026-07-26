import asyncio
import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from backend.services.deepseek import enrich_prompt, generate_scene_html
from backend.services.tts import generate_tts, align_scenes_to_audio, generate_ass
from backend.services.history import save_generation
from backend.config import RENDER_SERVICE_URL

router = APIRouter()

ASPECTS = {
    "16:9": (1920, 1080),
    "9:16": (1080, 1920),
    "1:1": (1080, 1080),
}


class GenerateRequest(BaseModel):
    prompt: str
    tts: str = "none"
    aspect: str = "16:9"
    style: str = "none"
    subtitles: bool = True


class GenerateResponse(BaseModel):
    id: str = ""
    title: str
    full_text: str
    scenes: list[dict]
    total_duration: int
    combined_html: str
    scenes_html: list[str]
    width: int
    height: int
    style: str = "none"


class RegenerateSceneRequest(BaseModel):
    title: str
    scene: dict
    scenes: list[dict] = []
    scenes_html: list[str] = []
    feedback: str = ""
    aspect: str = "16:9"
    style: str = "none"


class RenderRequest(BaseModel):
    html: str
    width: int = 1280
    height: int = 720
    fps: int = 15


class RenderAllRequest(BaseModel):
    scenes_html: list[str]
    durations: list[float] = []
    width: int = 1280
    height: int = 720
    fps: int = 24


class TTSRequest(BaseModel):
    text: str
    voice: str = "zh-CN-XiaoxiaoNeural"


class RenderWithAudioRequest(BaseModel):
    html: str
    width: int = 1280
    height: int = 720
    fps: int = 15
    tts_text: str = ""
    tts_voice: str = "zh-CN-XiaoxiaoNeural"
    scenes: list[dict] = []
    scenes_html: list[str] = []
    subtitles: bool = True


def assemble_video_html(scenes_html: list[str], plan: dict, width: int = 1920, height: int = 1080, tts_durations: list[float] | None = None, total_duration_override: float | None = None) -> str:
    if tts_durations:
        durations_json = str(tts_durations)
    else:
        durations_json = str([s["duration"] for s in plan["scenes"]])

    scene_containers = []
    for i, html in enumerate(scenes_html):
        styles = _extract_head_styles(html)
        body = _extract_body(html)
        scene_containers.append(
            f'<div class="scene-box" id="scene-{i}">\n{styles}\n{body}\n</div>'
        )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{plan['title']}</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:#000; display:flex; justify-content:center; align-items:center; min-height:100vh; overflow:hidden; }}
.stage {{ position:relative; width:{width}px; height:{height}px; overflow:hidden; }}
.scene-box {{ position:absolute; top:0; left:0; width:100%; height:100%; display:none; }}
.scene-box.active {{ display:block; }}
</style>
</head>
<body>
<div class="stage">
{''.join(scene_containers)}
</div>
<script>
var __durations = {durations_json};
var __totalDuration = {"total_duration_override" if total_duration_override else "__durations.reduce(function(a,b){{return a+b;}}, 0)"};
var __currentScene = -1;
var __startTime = null;

function __showScene(idx) {{
  var boxes = document.querySelectorAll('.scene-box');
  boxes.forEach(function(b){{ b.classList.remove('active'); }});
  if (boxes[idx]) boxes[idx].classList.add('active');
  __currentScene = idx;
}}

function __seekTo(t) {{
  var acc = 0;
  for (var i = 0; i < __durations.length; i++) {{
    if (t < acc + __durations[i]) {{
      if (i !== __currentScene) __showScene(i);
      return;
    }}
    acc += __durations[i];
  }}
  if (__currentScene !== __durations.length - 1) __showScene(__durations.length - 1);
}}

window.__hf = {{
  duration: __totalDuration,
  seek: function(t) {{ __seekTo(t); }},
}};

__showScene(0);
if (!window.__RENDER_MODE) {{
  __startTime = Date.now();
  (function __autoPlay() {{
    var t = (Date.now() - __startTime) / 1000;
    if (t >= __totalDuration) {{
      __showScene(0);
      __startTime = Date.now();
    }} else {{
      __seekTo(t);
    }}
    requestAnimationFrame(__autoPlay);
  }})();
}}
</script>
</body>
</html>"""


def _extract_body(html: str) -> str:
    if "<body" in html:
        start = html.index("<body")
        try:
            start = html.index(">", start) + 1
        except ValueError:
            # <body 标签可能不完整，尝试跳过
            start = html.find("\n", start)
            if start == -1:
                start = len("<body")
            else:
                start += 1
        end = html.find("</body>", start)
        if end == -1:
            end = html.find("</html>", start)
        if end == -1:
            end = len(html)
        if start < end:
            return html[start:end]
    return html


def _extract_head_styles(html: str) -> str:
    styles = []
    head_end = html.find("</head>")
    if head_end == -1:
        head_end = html.find("<body") if "<body" in html else len(html)
    head = html[:head_end]
    import re
    for m in re.finditer(r"<style[^>]*>(.*?)</style>", head, re.DOTALL):
        inner_css = m.group(1)
        filtered = _filter_global_selectors(inner_css)
        if filtered.strip():
            styles.append(f"<style>\n{filtered}\n</style>")
    return "\n".join(styles)


def _filter_global_selectors(css: str) -> str:
    """过滤掉 body/html/* 全局选择器的 CSS 规则，防止污染 combined HTML 外层布局。"""
    import re
    # 移除 body {...}, html {...}, * {...}, html,body {...} 等全局规则块
    css = re.sub(
        r'(?:^|\})\s*(?:body|html|\*)(?:\s*,\s*(?:body|html|\*|[a-zA-Z_-][^{]*))?\s*\{[^}]*\}',
        '}',
        css,
        flags=re.MULTILINE,
    )
    css = css.strip()
    if css.startswith('}'):
        css = css[1:].strip()
    return css


@router.post("/generate", response_model=GenerateResponse)
async def generate_animation(req: GenerateRequest):
    try:
        plan = await enrich_prompt(req.prompt, req.style)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文案生成失败: {str(e)}")

    async def gen_one(scene):
        try:
            return await generate_scene_html(scene, plan["title"], req.aspect, style=req.style)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"场景{scene['index']}动画生成失败: {str(e)}",
            )
    scenes_html = await asyncio.gather(*[gen_one(s) for s in plan["scenes"]])

    w, h = ASPECTS.get(req.aspect, ASPECTS["16:9"])
    combined = assemble_video_html(scenes_html, plan, w, h)

    # 自动保存到历史记录
    gid = ""
    try:
        gid = save_generation({
            "prompt": req.prompt,
            "title": plan["title"],
            "full_text": plan["full_text"],
            "scenes": plan["scenes"],
            "total_duration": plan["total_duration"],
            "combined_html": combined,
            "scenes_html": scenes_html,
            "width": w,
            "height": h,
            "aspect": req.aspect,
            "style": req.style,
        })
    except Exception as e:
        print(f"[历史] 保存失败: {e}")

    return GenerateResponse(
        id=gid,
        title=plan["title"],
        full_text=plan["full_text"],
        scenes=plan["scenes"],
        total_duration=plan["total_duration"],
        combined_html=combined,
        scenes_html=scenes_html,
        width=w,
        height=h,
        style=req.style,
    )


@router.post("/regenerate-scene")
async def regenerate_scene(req: RegenerateSceneRequest):
    """单独重新生成某个场景，返回新 HTML 和重组后的 combined_html"""
    try:
        html = await generate_scene_html(req.scene, req.title, req.aspect, req.feedback, req.style)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"场景重新生成失败: {str(e)}")

    # 更新对应场景的 HTML，重新组装 combined_html
    idx = req.scene["index"] - 1
    if req.scenes_html and req.scenes:
        scenes_html = list(req.scenes_html)
        if 0 <= idx < len(scenes_html):
            scenes_html[idx] = html
        plan = {"title": req.title, "scenes": req.scenes}
        w, h = ASPECTS.get(req.aspect, ASPECTS["16:9"])
        combined = assemble_video_html(scenes_html, plan, w, h)
        return {"index": req.scene["index"], "html": html, "combined_html": combined}

    return {"index": req.scene["index"], "html": html}


@router.post("/render")
async def render_video(req: RenderRequest):
    try:
        async with httpx.AsyncClient(timeout=900.0) as client:
            resp = await client.post(
                f"{RENDER_SERVICE_URL}/render",
                json={"html": req.html, "width": req.width, "height": req.height, "fps": req.fps},
            )
            if resp.status_code != 200:
                detail = resp.text
                try:
                    detail = resp.json().get("error", resp.text)
                except Exception:
                    pass
                raise HTTPException(status_code=resp.status_code, detail=f"渲染失败: {detail}")
            return Response(content=resp.content, media_type="video/mp4")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="渲染服务未启动")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"渲染异常: {str(e)}")


@router.post("/generate-tts")
async def generate_tts_audio(req: TTSRequest):
    """生成 TTS 预览音频，返回 MP3 字节。"""
    import os

    tts_result = await generate_tts(req.text, req.voice)
    try:
        with open(tts_result["audio_path"], "rb") as f:
            audio_bytes = f.read()

        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "X-Audio-Duration": str(tts_result["duration_sec"]),
                "X-Audio-Voice": tts_result["voice"],
                "Content-Disposition": "attachment; filename=voiceover.mp3",
            },
        )
    finally:
        if os.path.exists(tts_result["audio_path"]):
            os.unlink(tts_result["audio_path"])


@router.post("/render-with-audio")
async def render_video_with_audio(req: RenderWithAudioRequest):
    """独立控制语音/字幕：可纯音频、纯字幕、两者、或纯视频。"""
    import base64
    import os

    audio_path = None
    try:
        render_html = req.html
        audio_data_b64 = ""
        subtitle_content = ""

        needs_audio = bool(req.tts_voice and req.tts_voice not in ("", "none"))
        needs_subs = req.subtitles
        needs_tts = bool(req.tts_text.strip() and (needs_audio or needs_subs))

        if needs_tts:
            # 生成 TTS 获取时间戳（纯字幕模式用默认语音，音频不保留）
            tts_voice = req.tts_voice if needs_audio else "zh-CN-XiaoxiaoNeural"
            tts_result = await generate_tts(req.tts_text, tts_voice)
            audio_path = tts_result["audio_path"]

            if needs_audio:
                with open(audio_path, "rb") as f:
                    audio_data_b64 = base64.b64encode(f.read()).decode("utf-8")
                print(f"[TTS] 语音: {tts_voice}, 时长: {tts_result['duration_sec']:.1f}s")

            if needs_subs:
                subtitle_content = generate_ass(tts_result["word_boundaries"], req.tts_text)
                line_count = subtitle_content.count("Dialogue:") if subtitle_content else 0
                print(f"[ASS] 字幕: {line_count} 条")

            # 用 TTS 时间戳重建 HTML，场景切换与语音对齐
            if req.scenes and req.scenes_html:
                audio_dur = tts_result["duration_sec"]
                alignments = align_scenes_to_audio(
                    req.tts_text, req.scenes, tts_result["word_boundaries"]
                )
                tts_durations = [round(a["end"] - a["start"], 2) for a in alignments]
                total = sum(tts_durations)
                if total > 0 and audio_dur > 0 and abs(total - audio_dur) > 0.1:
                    scale = audio_dur / max(total, 0.01)
                    tts_durations = [round(d * scale, 2) for d in tts_durations]
                    tts_durations[-1] = round(audio_dur - sum(tts_durations[:-1]), 2)

                plan = {"title": "", "scenes": req.scenes}
                w, h = req.width, req.height
                for ratio, (rw, rh) in ASPECTS.items():
                    if rw == req.width and rh == req.height:
                        w, h = rw, rh
                        break
                render_html = assemble_video_html(req.scenes_html, plan, w, h, tts_durations, audio_dur)
                print(f"[对齐] 场景时长={tts_durations}, 总={sum(tts_durations):.1f}s, 参考={audio_dur:.1f}s")

        async with httpx.AsyncClient(timeout=900.0) as client:
            resp = await client.post(
                f"{RENDER_SERVICE_URL}/render",
                json={
                    "html": render_html,
                    "width": req.width,
                    "height": req.height,
                    "fps": req.fps,
                    "audio_base64": audio_data_b64,
                    "subtitle_content": subtitle_content,
                },
            )
            if resp.status_code != 200:
                detail = resp.text
                try:
                    detail = resp.json().get("error", resp.text)
                except Exception:
                    pass
                raise HTTPException(status_code=resp.status_code, detail=f"渲染失败: {detail}")
            return Response(content=resp.content, media_type="video/mp4")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="渲染服务未启动")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"渲染异常: {str(e)}")
    finally:
        if audio_path and os.path.exists(audio_path):
            try:
                os.unlink(audio_path)
            except Exception:
                pass


@router.post("/render-all")
async def render_all_scenes(req: RenderAllRequest):
    """逐场景独立渲染为 MP4，拼接为完整视频（纯视频，无音频字幕）。"""
    async with httpx.AsyncClient(timeout=900.0) as client:
        resp = await client.post(
            f"{RENDER_SERVICE_URL}/render-all",
            json={
                "scenes_html": req.scenes_html,
                "durations": req.durations or None,
                "width": req.width,
                "height": req.height,
                "fps": req.fps,
            },
        )
        if resp.status_code != 200:
            detail = resp.text
            try:
                detail = resp.json().get("error", resp.text)
            except Exception:
                pass
            raise HTTPException(status_code=resp.status_code, detail=f"渲染失败: {detail}")
        return Response(content=resp.content, media_type="video/mp4")
