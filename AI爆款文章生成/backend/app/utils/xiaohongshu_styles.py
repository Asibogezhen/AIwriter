"""小红书配图风格配置 — 从 xiaohongshu-prompts 提炼"""

XHS_IMAGE_STYLES = [
    {
        "id": "bold",
        "name": "多巴胺大胆风",
        "description": "高饱和撞色、Y2K 美学，视觉冲击力极强",
        "palette": "#FF6B6B, #FFE66D, #4ECDC4, #FF0A7B, #7B2FBE",
        "prompt_style": (
            "Dopamine bold aesthetic, Y2K cyberpunk elements, "
            "high saturation color clash, glossy finish, "
            "editorial fashion photography style, vibrant neon colors, "
            "fisheye lens perspective, trendy streetwear vibe"
        ),
    },
    {
        "id": "cute",
        "name": "治愈可爱风",
        "description": "软萌粉嫩、毛绒玩具质感，少女心满满",
        "palette": "#FFD4D4, #FFF0F5, #FFE4E1, #FFB6C1, #E8F4FD",
        "prompt_style": (
            "Kawaii cute aesthetic, soft pastel tones, plush toy texture, "
            "sparkly glitter particles, warm diffused lighting, "
            "dreamy bokeh background, squishy and soft materials, "
            "Japanese shoujo manga inspired, sweet candy colors, "
            "fluffy clouds and star sparkles"
        ),
    },
    {
        "id": "minimalist",
        "name": "极简留白风",
        "description": "侘寂美学、大面积留白、低饱和中性色",
        "palette": "#F5F0EB, #E8E0D5, #D4C9B8, #8B8680, #4A4540",
        "prompt_style": (
            "Wabi-sabi minimalist aesthetic, zen Japanese interior, "
            "large negative space, soft natural morning light from window, "
            "neutral earth tones, clean simple composition, "
            "linen and wood textures, quiet peaceful atmosphere, "
            "architectural photography style, elegant simplicity"
        ),
    },
    {
        "id": "cyberpunk",
        "name": "赛博朋克风",
        "description": "霓虹灯、机械义体、未来都市、高科技低生活",
        "palette": "#FF00FF, #00FFFF, #1A0A2E, #FF2200, #0011FF",
        "prompt_style": (
            "Cyberpunk aesthetic, futuristic neon city at night, "
            "holographic displays, rain-soaked streets with neon reflections, "
            "cybernetic enhancements, volumetric lighting, "
            "blade runner style atmosphere, high tech low life mood, "
            "purple and cyan dominant color grade"
        ),
    },
    {
        "id": "chinese-elegance",
        "name": "新中式国风",
        "description": "水墨留白、非遗工艺、东方意境、宋韵唐风",
        "palette": "#2D1B3D, #C41E3A, #D4A574, #1A3634, #F5E6D0",
        "prompt_style": (
            "New Chinese elegant aesthetic, ink wash painting style, "
            "traditional hanfu silk fabric with embroidery, "
            "soft dreamlike atmospheric fog, poetic oriental composition, "
            "porcelain and jade textures, classical garden with bamboo shadows, "
            "Song dynasty inspired, refined cultural elegance, "
            "muted vermillion and celadon tones"
        ),
    },
    {
        "id": "clay-3d",
        "name": "3D黏土盲盒风",
        "description": "C4D 黏土材质、圆润可爱、泡泡玛特风格",
        "palette": "#FFE4E1, #FFF0F5, #E8F4FD, #FFD4D4, #FFFDD0",
        "prompt_style": (
            "3D C4D clay material render, chubby round character, "
            "matte texture, soft pastel color palette, "
            "POP MART blind box toy aesthetic, studio soft lighting, "
            "big sparkling eyes, rosy cheeks, clean solid color background, "
            "adorable collectible art toy style, 8K ultra HD"
        ),
    },
    {
        "id": "dark",
        "name": "暗黑美学风",
        "description": "哥特浪漫、暗黑学术、高对比、神秘危险的美",
        "palette": "#0A0A0A, #1C1C1C, #8B0000, #2D1B3D, #D4A547",
        "prompt_style": (
            "Dark academia gothic aesthetic, strong chiaroscuro lighting, "
            "Rembrandt lighting style, black and deep red tones, "
            "ancient library with leather-bound books, candlelight glow, "
            "mysterious and hauntingly beautiful, low saturation high contrast, "
            "classical oil painting texture, moody atmospheric shadows"
        ),
    },
    {
        "id": "dreamcore",
        "name": "梦核怀旧风",
        "description": "柔焦发光、胶片颗粒、不真实的梦幻感、怀旧治愈",
        "palette": "#FFD4A3, #4A2800, #B3D9FF, #FFE0F0, #FFF0DC",
        "prompt_style": (
            "Dreamcore nostalgic aesthetic, soft focus glow effect, "
            "film grain texture, warm amber tones with light leaks, "
            "ethereal dreamy atmosphere, vintage film photography, "
            "floating dust particles sparkling in sunlight, "
            "Fuji Superia 400 film color, nostalgic healing summer vibes"
        ),
    },
    {
        "id": "retro-anime",
        "name": "AI旧漫风",
        "description": "80-90年代日本赛璐珞动画、手绘质感、City Pop",
        "palette": "#FFB6C1, #87CEEB, #FF8C42, #4A4A6A, #FFE4B5",
        "prompt_style": (
            "1980s Japanese animation cel style, hand-painted cel shading, "
            "soft watercolor coloring, subtle color fading and film grain, "
            "bold line art with slight imperfections, "
            "retro anime aesthetic character design, City Pop album cover vibes, "
            "VHS tape slight magenta color shift, nostalgic warm tones, "
            "classic anime background art with painted skies"
        ),
    },
    {
        "id": "retro-hongkong",
        "name": "复古港风",
        "description": "王家卫美学、霓虹灯、青橙撞色、胶片质感",
        "palette": "#FF2200, #00FF88, #1A3A4A, #FF8C42, #2A2830",
        "prompt_style": (
            "Wong Kar-wai film aesthetic, 1990s Hong Kong at night, "
            "neon signs reflecting on wet rain-soaked streets, "
            "teal and orange color grade, Kodak Portra 400 film tones, "
            "heavy film grain, soft focus blur, cinematic light leaks, "
            "moody atmospheric night scene, nostalgic retro romance, "
            "traditional Chinese neon characters, red taxi cab"
        ),
    },
]


def get_style_by_id(style_id: str) -> dict | None:
    for s in XHS_IMAGE_STYLES:
        if s["id"] == style_id:
            return s
    return None


def get_all_style_options() -> list[dict]:
    return [{"id": s["id"], "name": s["name"], "description": s["description"]} for s in XHS_IMAGE_STYLES]
