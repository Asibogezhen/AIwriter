from openai import AsyncOpenAI
from backend.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL

client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

MODEL = "deepseek-v4-pro"

STYLE_PRESETS = {
    "none": "",
    "tech": "科技感——深色背景、霓虹光效、几何线条、电路板纹理、蓝色/青色冷色调、精密机械感。适用：科普解说、技术演示",
    "ink": "水墨风——宣纸纹理底色、墨迹晕染、飞白笔触、黑白灰为主色调、留白美学、可点缀朱红印章。适用：传统文化、诗词朗诵",
    "cyberpunk": "赛博朋克——霓虹网格、故障艺术效果、紫红/品红/青色配色、扫描线、暗黑未来都市、全息投影感。适用：科幻故事、未来畅想",
    "flat": "扁平化——纯色块面、无阴影无渐变、大胆撞色、极简几何图形、清晰无衬线字体、孟菲斯风格。适用：商业汇报、产品介绍",
    "3d": "3D质感——深度投影、透视空间感、写实光照与材质、玻璃拟态、立体几何体、景深模糊。适用：品牌宣传、高端展示",
    "handdrawn": "手绘风——铅笔/蜡笔纹理、不规则描边、有机曲线、温暖色调、涂鸦与速写风格、纸质纹理背景。适用：儿童科普、趣味故事",
}


def _get_system_prompt_enrich(style: str = "none") -> str:
    base = """你是一个专业的视频文案策划师。用户会给你一个主题或简单描述，请你：

1. 将用户的简单想法扩展为一段完整的视频文案（400-800字），确保内容准确、符合事实
2. 将文案拆分为6-10个场景（尽量细致，每个场景聚焦一个要点），每个场景包含：
   - 场景标题
   - 场景文字内容（用于动画展示，每场景1-3句话，必须是简洁有力的展示语句）
   - 建议时长（秒），每个场景时长尽量均匀，控制在4-8秒之间
   - 视觉风格建议（颜色、氛围）

重要：如果用户描述涉及科学、历史、技术等事实性内容，必须确保准确。如果涉及虚构或艺术创作，可以自由发挥。

按以下JSON格式返回（只返回JSON，不要其他内容）：
{
  "title": "视频标题",
  "full_text": "完整文案",
  "scenes": [
    {
      "index": 1,
      "title": "场景标题",
      "text": "展示文字内容",
      "duration": 5,
      "style_hint": "深蓝色背景，金色文字，科技感"
    }
  ],
  "total_duration": 25
}"""
    style_desc = STYLE_PRESETS.get(style, "")
    if style_desc:
        base += f"\n\n全局视觉风格要求：{style_desc}\n请确保每个场景的 style_hint 充分体现此风格特点，配色和氛围描述中融入此风格的关键视觉元素。"
    return base


def _animate_prompt(width: int, height: int, duration: int, style: str = "none") -> str:
    base = f"""你是顶级动效设计师，用 HTML/CSS 制作 {duration} 秒动画页面。画面必须绚丽丰富、层次分明。

== 文字规则 ==
- 单段文字，放画面正中央，左右留出 {width*0.15:.0f}px 以上安全区
- 字号 {width*0.03:.0f}px ~ {width*0.045:.0f}px，行宽不超过 {width*0.7:.0f}px，加 text-align: center
- 文字加多层 text-shadow 制造发光/描边效果，确保在各种背景上都清晰可读
- z-index: 100，永远在最上层

== 背景规则 ==
- 必须使用多层背景：至少包含一个渐变底色 + 一个径向光晕 + 一个图案纹理（可用 repeating-linear-gradient、radial-gradient 叠加）
- 背景可以缓慢移动/旋转（用 @keyframes 驱动 background-position 或 transform）
- 可添加极光飘带、流动波纹、星空闪烁等动态背景元素

== 粒子/装饰规则（丰富画面的核心）==
- 数量：10~18 个装饰元素，分散在画面各处
- 尺寸：8~50px，大小混合
- 形状多样化：圆形、十字星、菱形、三角、六边形、圆环、长条
- 用百分比定位（top: 5%~95%，left: 5%~95%）
- z-index: 1~10，在文字下方
- 添加 1~3 个大型背景装饰（200~500px，半透明，边缘位置）
- 添加 1~2 条流动光带

== 动画规则（必须多样化）==
- 整体节奏：0~{duration*0.15:.0f}s 渐入，{duration*0.15:.0f}s~{duration*0.85:.0f}s 展示，{duration*0.85:.0f}s~{duration}s 淡出
- 粒子动画不能全是平移，必须混合使用：
  * float（translateY/translateX 来回浮动）
  * pulse（scale 缩放脉冲）
  * rotate（慢速旋转，用于菱形/十字星）
  * drift（对角线缓慢漂移）
  * glow（opacity 闪烁 + box-shadow 光晕脉动）
- 不同粒子使用不同的 animation-duration（2s~6s 不等），错开节奏
- 大型背景装饰缓慢旋转或缩放（10~20s 周期），不要静止
"""
    style_guidance = _get_style_animation_guidance(style, width, height)
    base += style_guidance
    base += f"""

== 禁止事项 ==
- 禁止 JavaScript
- 禁止 body/html/* 选择器
- 页面 {width}x{height}，overflow: hidden
- 所有内容必须在 {width}x{height} 范围内

返回完整 HTML，代码放在```html代码块中。"""
    return base


def _get_style_animation_guidance(style: str, w: int, h: int) -> str:
    if style == "tech":
        return """
== 科技感风格指导 ==
- 配色：以深蓝#0a0e27为底，霓虹蓝#0a84ff和青色#00e5ff为主色调，白色文字
- 背景：添加CSS网格线图案（repeating-linear-gradient做细线网格），模拟电路板/数据界面
- 粒子：使用方形、菱形等几何体，带霓虹光晕（box-shadow发光）
- 装饰：添加类似数据流动的线条、节点圆点、HUD元素
- 文字：等宽或科技感无衬线字体，多层蓝色光晕text-shadow"""
    elif style == "ink":
        return f"""
== 水墨风格指导 ==
- 配色：以宣纸白#f5f0e8或淡黄为底，墨黑#1a1a1a为主色，可点缀朱红#c41e3a印章色
- 背景：模拟宣纸纹理（repeating-radial-gradient做细小墨点），淡雅渐变
- 粒子：使用不规则圆形模拟墨迹晕染，椭圆/水滴形状
- 装饰：大型半透明墨色团块（filter: blur），飞白效果的长条
- 文字：仿宋或楷体风格（serif），文字颜色墨黑，text-shadow用淡墨扩散效果
- 动画：缓慢柔和，如墨在水中扩散（transform: scale + opacity）"""
    elif style == "cyberpunk":
        return """
== 赛博朋克风格指导 ==
- 配色：暗黑底#0a0a0a，品红#ff00ff和青色#00ffff为主，黄色#ffff00点缀
- 背景：CSS扫描线效果（repeating-linear-gradient做横纹），霓虹网格
- 粒子：矩形、十字星，带强烈霓虹光晕
- 装饰：故障艺术效果（clip-path偏移），全息投影风格的几何环
- 文字：无衬线粗体，品红+青色双层text-shadow，类似霓虹灯牌"""
    elif style == "flat":
        return """
== 扁平化风格指导 ==
- 配色：高饱和纯色——珊瑚红#ff6b6b、青绿#4ecdc4、明黄#ffe66d、紫罗兰#6c5ce7
- 背景：纯色或简单双色渐变，无纹理无噪点
- 粒子：大色块几何形（圆形、方形、三角），无阴影无渐变
- 装饰：孟菲斯风格的波点、粗线条、色块组合
- 文字：粗体无衬线，纯色无阴影，与背景形成高对比度
- 禁止：阴影、渐变、模糊、发光效果"""
    elif style == "3d":
        return """
== 3D质感风格指导 ==
- 配色：深色背景带聚光灯光源，金色/白色强调色
- 背景：径向渐变模拟聚光灯，深色到浅色的空间过渡
- 粒子：立体几何体（用多层box-shadow模拟3D厚度），玻璃拟态元素
- 装饰：perspective + transform: rotateX/Y 营造深度感，大尺寸模糊光斑模拟景深
- 文字：多层text-shadow模拟3D浮雕效果，或玻璃拟态半透明面板
- 光照：模拟单一光源从上方照射（所有高光方向一致）"""
    elif style == "handdrawn":
        return """
== 手绘风格指导 ==
- 配色：温暖柔和色调——奶油色底#fff8e7，蜡笔粉#f7a8b8、淡蓝#a8d8ea、草绿#c3e8a0、土黄#e8d5a0
- 背景：纸质纹理（噪点渐变），轻微不规则边框
- 粒子：不规则圆形（border-radius不对称）、星形涂鸦、曲线条，边缘略带模糊模拟手绘笔触
- 装饰：铅笔线条风格的波浪线、锯齿线，蜡笔涂抹色块
- 文字：略带不规则感的圆体，可用text-shadow模拟铅笔描边
- 动画：轻微晃动（小幅度rotate），模拟手绘的不完美感"""
    return ""


ASPECT_RESOLUTION = {
    "16:9": (1920, 1080),
    "9:16": (1080, 1920),
    "1:1": (1080, 1080),
}


async def enrich_prompt(user_prompt: str, style: str = "none") -> dict:
    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": _get_system_prompt_enrich(style)},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        response_format={"type": "json_object"},
    )
    import json
    return json.loads(response.choices[0].message.content)


async def generate_scene_html(scene: dict, title: str, aspect: str = "16:9", feedback: str = "", style: str = "none") -> str:
    w, h = ASPECT_RESOLUTION.get(aspect, (1920, 1080))

    parts = [
        f"视频主题：{title}",
        f"场景{scene['index']}：{scene['title']}",
        f"展示文字：{scene['text']}",
        f"时长：{scene['duration']}秒",
        f"风格：{scene.get('style_hint', '现代简约')}",
        f"画布尺寸：{w}x{h}",
    ]
    if feedback:
        parts.append(f"用户修改意见（必须按此调整）：{feedback}")

    scene_desc = "\n".join(parts)

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": _animate_prompt(w, h, scene['duration'], style)},
            {"role": "user", "content": scene_desc},
        ],
        temperature=0.8,
        max_tokens=65536,
    )
    content = response.choices[0].message.content
    html = _extract_html(content)

    # 检测截断：HTML 不完整则用精简 prompt 重试
    if not _is_html_complete(html):
        import logging
        logging.getLogger(__name__).warning(f"场景{scene['index']} HTML 被截断，重试中...")
        short_prompt = f"""用 HTML/CSS 制作 {scene['duration']}s 动画页面 {w}x{h}。
展示文字：「{scene['text']}」
风格：{scene.get('style_hint', '现代简约')}
要求：10-15个装饰粒子、完整CSS动画、淡入淡出节奏、z-index文字最上层、禁止JS、禁止body/html/*选择器。
必须输出完整的 </html> 闭合标签。代码放```html```中。"""
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": short_prompt},
                {"role": "user", "content": f"视频主题：{title}，场景：{scene['title']}。确保HTML完整闭合。"},
            ],
            temperature=0.7,
            max_tokens=65536,
        )
        content = response.choices[0].message.content
        html = _extract_html(content)

        # 二次重试：再失败就用更简短的 prompt
        if not _is_html_complete(html):
            logging.getLogger(__name__).warning(f"场景{scene['index']} 二次重试...")
            response = await client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": f"生成{w}x{h}的{scene['duration']}秒HTML动画页面。禁止JS。完整闭合</html>。"},
                    {"role": "user", "content": f"展示文字：「{scene['text']}」。代码放```html中，必须</html>结束。"},
                ],
                temperature=0.6,
                max_tokens=65536,
            )
            content = response.choices[0].message.content
            html = _extract_html(content)

    return html


def _is_html_complete(html: str) -> bool:
    """检查 HTML 是否完整：有 </html> 闭合标签，没有明显截断。"""
    if not html:
        return False
    if not html.rstrip().endswith("</html>"):
        return False
    # CSS 规则不应该在中途截断（检查最后 50 字符）
    tail = html[-50:].strip()
    if tail and tail[-1] not in "}>;\n ":
        return False
    return True


def _extract_html(content: str) -> str:
    if "```html" in content:
        start = content.index("```html") + 7
        end = content.find("```", start)
        if end == -1:
            return content[start:].strip()
        return content[start:end].strip()
    if "```" in content:
        start = content.index("```") + 3
        end = content.find("```", start)
        if end == -1:
            return content[start:].strip()
        return content[start:end].strip()
    return content.strip()
