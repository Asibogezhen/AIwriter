import asyncio
import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from backend.services.deepseek import enrich_prompt, generate_scene_html
from backend.services.tts import generate_tts
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


def assemble_video_html(scenes_html: list[str], plan: dict, width: int = 1920, height: int = 1080, show_subtitles: bool = True) -> str:
    durations_json = str([s["duration"] for s in plan["scenes"]])

    scene_containers = []
    for i, html in enumerate(scenes_html):
        styles = _extract_head_styles(html)
        body = _extract_body(html)
        scene_containers.append(
            f'<div class="scene-box" id="scene-{i}">\n{styles}\n{body}\n</div>'
        )

    subtitles_json = "[]"
    subtitle_html = ""
    if show_subtitles:
        subs = []
        cumulative = 0
        for s in plan["scenes"]:
            subs.append({"text": s["text"], "start": cumulative, "end": cumulative + s["duration"]})
            cumulative += s["duration"]
        subtitles_json = str(subs)
        bottom_margin = int(height * 0.06)
        pad_v = int(height * 0.015)
        pad_h = int(width * 0.04)
        font_sz = int(width * 0.022)
        max_w = int(width * 0.78)
        subtitle_html = f"""<div id="subtitle-overlay" style="
  position:absolute; bottom:{bottom_margin}px; left:50%; transform:translateX(-50%);
  background:rgba(0,0,0,0.72); color:#fff; padding:{pad_v}px {pad_h}px;
  border-radius:10px; font-size:{font_sz}px; line-height:1.4; max-width:{max_w}px;
  text-align:center; z-index:999; pointer-events:none;
  font-family:'PingFang SC','Microsoft YaHei','Noto Sans CJK SC',sans-serif;
  word-break:break-word;
"> </div>"""

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
{subtitle_html}
{''.join(scene_containers)}
</div>
<script>
var __durations = {durations_json};
var __totalDuration = __durations.reduce(function(a,b){{return a+b;}}, 0);
var __currentScene = -1;
var __startTime = null;
var __subtitles = {subtitles_json};

function __showScene(idx) {{
  var boxes = document.querySelectorAll('.scene-box');
  boxes.forEach(function(b){{ b.classList.remove('active'); }});
  if (boxes[idx]) boxes[idx].classList.add('active');
  __currentScene = idx;
  var subEl = document.getElementById('subtitle-overlay');
  if (subEl && __subtitles[idx]) {{
    subEl.textContent = __subtitles[idx].text;
  }}
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
        start = html.index(">", start) + 1
        end = html.find("</body>", start)
        if end == -1:
            end = html.find("</html>", start)
        if end == -1:
            end = len(html)
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
    combined = assemble_video_html(scenes_html, plan, w, h, req.subtitles)

    return GenerateResponse(
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
    """生成 TTS 音频并渲染带音轨的 MP4。"""
    import base64
    import os

    audio_path = None
    try:
        audio_data_b64 = ""
        if req.tts_text.strip():
            tts_result = await generate_tts(req.tts_text, req.tts_voice)
            audio_path = tts_result["audio_path"]
            with open(audio_path, "rb") as f:
                audio_data_b64 = base64.b64encode(f.read()).decode("utf-8")

        async with httpx.AsyncClient(timeout=900.0) as client:
            resp = await client.post(
                f"{RENDER_SERVICE_URL}/render",
                json={
                    "html": req.html,
                    "width": req.width,
                    "height": req.height,
                    "fps": req.fps,
                    "audio_base64": audio_data_b64,
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
