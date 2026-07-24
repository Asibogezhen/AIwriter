<script setup lang="ts">
import { ref, computed } from "vue";
import { generateAnimation, regenerateScene, renderVideo, generateTTS, renderVideoWithAudio, type GenerateResponse } from "../api/index";

const ASPECTS = [
  { key: "16:9", label: "横屏 16:9", icon: "▭", w: 1920, h: 1080 },
  { key: "9:16", label: "竖屏 9:16", icon: "▯", w: 1080, h: 1920 },
  { key: "1:1", label: "方形 1:1", icon: "□", w: 1080, h: 1080 },
];

const STYLE_PRESETS = [
  { key: "none", label: "自动", hint: "AI 自行判断风格" },
  { key: "tech", label: "科技感", hint: "科普解说、技术演示" },
  { key: "ink", label: "水墨风", hint: "传统文化、诗词朗诵" },
  { key: "cyberpunk", label: "赛博朋克", hint: "科幻故事、未来畅想" },
  { key: "flat", label: "扁平化", hint: "商业汇报、产品介绍" },
  { key: "3d", label: "3D质感", hint: "品牌宣传、高端展示" },
  { key: "handdrawn", label: "手绘风", hint: "儿童科普、趣味故事" },
];

const TTS_VOICES = [
  { key: "none", label: "无语音" },
  { key: "zh-CN-XiaoxiaoNeural", label: "晓晓 (温暖女声)" },
  { key: "zh-CN-YunxiNeural", label: "云希 (活泼男声)" },
  { key: "zh-CN-XiaoyiNeural", label: "晓伊 (活泼女声)" },
  { key: "zh-CN-YunjianNeural", label: "云健 (激情男声)" },
  { key: "zh-CN-YunxiaNeural", label: "云夏 (可爱童声)" },
];

const prompt = ref("");
const ttsMode = ref("none");
const aspect = ref("16:9");
const style = ref("none");
const showSubtitles = ref(true);
const loading = ref(false);
const rendering = ref(false);
const renderingScene = ref(-1);
const error = ref("");
const result = ref<GenerateResponse | null>(null);
const activeScene = ref(0);
const regenerating = ref<Record<number, boolean>>({});
const showRegenInput = ref<Record<number, boolean>>({});
const regenFeedback = ref<Record<number, string>>({});

const aspectCfg = computed(() => ASPECTS.find((a) => a.key === aspect.value) || ASPECTS[0]);

const currentSceneHtml = computed(() => {
  if (!result.value?.scenes_html) return "";
  return result.value.scenes_html[activeScene.value] || "";
});

const canGenerate = computed(() => prompt.value.trim().length > 0 && !loading.value);

function getRenderSize() {
  const a = aspectCfg.value;
  const scale = Math.min(1280 / a.w, 720 / a.h, 1);
  return { w: Math.round(a.w * scale), h: Math.round(a.h * scale) };
}

async function handleGenerate() {
  if (!canGenerate.value) return;
  loading.value = true;
  error.value = "";
  result.value = null;
  try {
    result.value = await generateAnimation(prompt.value, ttsMode.value, aspect.value, style.value, showSubtitles.value);
    activeScene.value = 0;
  } catch (e: any) {
    error.value = e.response?.data?.detail || e.message || "生成失败";
  } finally {
    loading.value = false;
  }
}

function exportTxt(r: GenerateResponse): string {
  let text = `标题：${r.title}\n`;
  text += `完整文案：${r.full_text}\n`;
  text += `总时长：${r.total_duration}秒\n`;
  text += `${"=".repeat(40)}\n\n`;
  let startSec = 0;
  r.scenes.forEach((s, i) => {
    text += `【场景 ${i + 1}】${s.title}  (${s.duration}秒)\n`;
    text += `视觉风格：${s.style_hint}\n`;
    text += `${s.text}\n\n`;
    startSec += s.duration;
  });
  return text;
}

function downloadTextFile(content: string, filename: string, mimeType = "text/plain;charset=utf-8") {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function downloadHtml(html: string, filename: string) {
  const blob = new Blob([html], { type: "text/html" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function downloadAllHtml() {
  if (!result.value) return;
  downloadHtml(result.value.combined_html, `${result.value.title}.html`);
}

function downloadSceneHtml(idx: number) {
  if (!result.value) return;
  const s = result.value.scenes[idx];
  downloadHtml(result.value.scenes_html[idx], `场景${idx + 1}-${s.title}.html`);
}

async function downloadVideo(html: string, filename: string) {
  if (!result.value) return;
  const { w, h } = getRenderSize();
  try {
    const blob = await renderVideo(html, w, h, 15);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  } catch (e: any) {
    error.value = e.response?.data?.detail || e.message || "视频渲染失败";
  }
}

async function downloadAllVideo() {
  if (!result.value) return;
  rendering.value = true;
  error.value = "";
  const { w, h } = getRenderSize();
  try {
    const blob = ttsMode.value !== "none"
      ? await renderVideoWithAudio(result.value.combined_html, w, h, 15, result.value.full_text, ttsMode.value)
      : await renderVideo(result.value.combined_html, w, h, 15);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${result.value.title}.mp4`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (e: any) {
    error.value = e.response?.data?.detail || e.message || "视频渲染失败";
  }
  rendering.value = false;
}

async function downloadSceneVideo(idx: number) {
  if (!result.value) return;
  renderingScene.value = idx;
  error.value = "";
  const s = result.value.scenes[idx];
  const { w, h } = getRenderSize();
  try {
    const blob = ttsMode.value !== "none"
      ? await renderVideoWithAudio(result.value.scenes_html[idx], w, h, 15, s.text, ttsMode.value)
      : await renderVideo(result.value.scenes_html[idx], w, h, 15);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `场景${idx + 1}-${s.title}.mp4`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (e: any) {
    error.value = e.response?.data?.detail || e.message || "视频渲染失败";
  }
  renderingScene.value = -1;
}

const ttsPreviewing = ref(false);

async function previewTTS() {
  if (!result.value || ttsMode.value === "none") return;
  ttsPreviewing.value = true;
  try {
    const blob = await generateTTS(result.value.full_text, ttsMode.value);
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    await audio.play();
    URL.revokeObjectURL(url);
  } catch (e: any) {
    error.value = "TTS 预览失败: " + (e.message || e);
  } finally {
    ttsPreviewing.value = false;
  }
}

function toggleRegenInput(idx: number) {
  showRegenInput.value[idx] = !showRegenInput.value[idx];
  if (!showRegenInput.value[idx]) regenFeedback.value[idx] = "";
}

async function handleRegenerate(idx: number) {
  if (!result.value) return;
  const scene = result.value.scenes[idx];
  regenerating.value[idx] = true;
  error.value = "";
  try {
    const res = await regenerateScene(
      result.value.title,
      { index: scene.index, title: scene.title, text: scene.text, duration: scene.duration, style_hint: scene.style_hint },
      result.value.scenes,
      result.value.scenes_html,
      aspect.value,
      regenFeedback.value[idx] || "",
      style.value
    );
    result.value.scenes_html[idx] = res.html;
    if (res.combined_html) {
      result.value.combined_html = res.combined_html;
    }
    showRegenInput.value[idx] = false;
    regenFeedback.value[idx] = "";
  } catch (e: any) {
    error.value = e.response?.data?.detail || e.message || "重新生成失败";
  } finally {
    regenerating.value[idx] = false;
  }
}
</script>

<template>
  <div class="home">
    <header class="header">
      <div class="logo">
        <svg width="28" height="28" viewBox="0 0 32 32" fill="none">
          <rect width="32" height="32" rx="8" fill="url(#logo-grad)" />
          <path d="M8 20l5-8 4 6 5-10" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
          <defs><linearGradient id="logo-grad" x1="0" y1="0" x2="32" y2="32"><stop stop-color="#6366f1"/><stop offset="1" stop-color="#a855f7"/></linearGradient></defs>
        </svg>
        <span class="logo-text">SVG AI 动画生成器</span>
      </div>
    </header>

    <main class="main">
      <!-- Hero / Input -->
      <section class="hero" :class="{ compact: !!result }">
        <h1 v-if="!result">一句话，生成动画视频</h1>
        <p v-if="!result" class="subtitle">输入你的想法，AI 自动生成 HTML 动画，一键导出视频</p>

        <div class="input-card">
          <textarea v-model="prompt" class="prompt-input" placeholder="描述你想要生成的动画内容..." rows="3"
            @keydown.ctrl.enter="handleGenerate" />

          <div class="input-actions">
            <div class="left-actions">
              <div class="aspect-select">
                <span class="label">比例</span>
                <button v-for="a in ASPECTS" :key="a.key" class="aspect-btn"
                  :class="{ active: aspect === a.key }" :title="a.label" @click="aspect = a.key">
                  {{ a.icon }}
                </button>
              </div>
              <div class="style-select">
                <span class="label">风格</span>
                <button v-for="s in STYLE_PRESETS" :key="s.key" class="style-btn"
                  :class="{ active: style === s.key }" :title="s.hint" @click="style = s.key">
                  {{ s.label }}
                </button>
              </div>
              <div class="tts-select">
                <span class="label">语音</span>
                <select v-model="ttsMode">
                  <option v-for="v in TTS_VOICES" :key="v.key" :value="v.key">{{ v.label }}</option>
                </select>
              </div>
              <div class="subtitle-toggle">
                <span class="label">字幕</span>
                <button class="toggle-btn" :class="{ on: showSubtitles }" @click="showSubtitles = !showSubtitles"
                  :title="showSubtitles ? '已开启字幕' : '已关闭字幕'">
                  {{ showSubtitles ? '开' : '关' }}
                </button>
              </div>
            </div>
            <button class="btn-generate" :disabled="!canGenerate" @click="handleGenerate">
              <span v-if="loading" class="spinner" />
              {{ loading ? "生成中..." : result ? "重新生成" : "生成动画" }}
            </button>
          </div>
        </div>

        <div v-if="!result" class="examples">
          <span class="examples-label">试试：</span>
          <button v-for="(ep, i) in ['用动画解释量子纠缠', '粒子汇聚成爱心', '太阳系行星公转', '二分查找算法演示', '水墨山水动画', 'DNA双螺旋复制']"
            :key="i" class="example-chip" @click="prompt = ep">{{ ep }}</button>
        </div>
      </section>

      <!-- Error -->
      <div v-if="error" class="error-msg">
        <span>{{ error }}</span>
        <button @click="error = ''">✕</button>
      </div>

      <!-- Result -->
      <section v-if="result" class="result-section">
        <div class="result-header">
          <h2>{{ result.title }}</h2>
          <div class="result-actions">
            <button class="btn-secondary" @click="downloadTextFile(
              exportTxt(result!), `${result!.title}-分镜脚本.txt`
            )">导出分镜 TXT</button>
            <button class="btn-secondary" @click="downloadAllHtml">下载全部 HTML</button>
            <button v-if="ttsMode !== 'none'" class="btn-secondary" :disabled="ttsPreviewing" @click="previewTTS">
              <span v-if="ttsPreviewing" class="spinner-small" />
              {{ ttsPreviewing ? "预览中..." : "预览语音" }}
            </button>
            <button class="btn-primary" :disabled="rendering" @click="downloadAllVideo">
              <span v-if="rendering" class="spinner" />
              {{ rendering ? "渲染中..." : "下载全部 MP4" }}
            </button>
          </div>
        </div>

        <p class="full-text">{{ result.full_text }}</p>

        <!-- Scene list -->
        <div class="scene-list">
          <div v-for="(scene, i) in result.scenes" :key="i" class="scene-card"
            :class="{ active: activeScene === i }" @click="activeScene = i">
            <div class="scene-card-header">
              <span class="scene-num">场景{{ i + 1 }}</span>
              <span class="scene-dur">{{ scene.duration }}s</span>
            </div>
            <div class="scene-card-title">{{ scene.title }}</div>

            <!-- 工具栏 -->
            <div class="scene-tools" @click.stop>
              <button class="tool-btn" title="下载此场景 HTML" @click="downloadSceneHtml(i)">⬇ HTML</button>
              <button class="tool-btn" title="下载此场景 MP4" :disabled="renderingScene === i"
                @click="downloadSceneVideo(i)">
                <span v-if="renderingScene === i" class="spinner-small" />
                {{ renderingScene === i ? "..." : "⬇ MP4" }}
              </button>
              <button class="tool-btn" title="重新生成此场景" @click="toggleRegenInput(i)">🔄 重生成</button>
            </div>

            <!-- 重新生成输入 -->
            <div v-if="showRegenInput[i]" class="regen-box" @click.stop>
              <input v-model="regenFeedback[i]" placeholder="修改意见（可选）" class="regen-input"
                @keydown.enter="handleRegenerate(i)" />
              <button class="btn-regen-go" :disabled="regenerating[i]" @click="handleRegenerate(i)">
                <span v-if="regenerating[i]" class="spinner-small" /> 确认
              </button>
            </div>
          </div>
        </div>

        <!-- Preview -->
        <div class="preview-container" :style="{ aspectRatio: aspectCfg.w + '/' + aspectCfg.h }">
          <iframe :key="activeScene" class="preview-frame" :srcdoc="currentSceneHtml"
            sandbox="allow-scripts" scrolling="no" />
        </div>
        <p class="preview-hint">点击场景卡片切换预览 · 支持单场景下载和重新生成</p>
      </section>
    </main>
  </div>
</template>

<style scoped>
.home { min-height: 100vh; background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3e 50%, #0d0d2b 100%); }
.header { display: flex; align-items: center; padding: 14px 28px; border-bottom: 1px solid rgba(255,255,255,0.06); }
.logo { display: flex; align-items: center; gap: 8px; }
.logo-text { font-size: 17px; font-weight: 600; background: linear-gradient(135deg,#6366f1,#a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.main { max-width: 960px; margin: 0 auto; padding: 32px 20px; }
.hero { text-align: center; padding-top: 40px; }
.hero.compact { padding-top: 0; }
h1 { font-size: 36px; font-weight: 700; background: linear-gradient(135deg,#e0e0ff,#c4b5fd); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 10px; }
.subtitle { color: #9ca3af; font-size: 15px; margin-bottom: 32px; }

.input-card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 18px; }
.prompt-input { width: 100%; background: transparent; border: none; color: #e0e0e0; font-size: 15px; line-height: 1.6; resize: none; outline: none; font-family: inherit; }
.prompt-input::placeholder { color: #6b7280; }

.input-actions { display: flex; align-items: center; justify-content: space-between; margin-top: 14px; padding-top: 14px; border-top: 1px solid rgba(255,255,255,0.06); }
.left-actions { display: flex; align-items: center; gap: 16px; }

.aspect-select, .tts-select { display: flex; align-items: center; gap: 6px; }
.label { font-size: 12px; color: #6b7280; }

.aspect-btn { padding: 4px 10px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08); border-radius: 6px; color: #9ca3af; font-size: 14px; cursor: pointer; transition: all 0.2s; }
.aspect-btn:hover { background: rgba(139,92,246,0.1); }
.aspect-btn.active { background: rgba(139,92,246,0.2); border-color: rgba(139,92,246,0.3); color: #c4b5fd; }

.style-select { display: flex; align-items: center; gap: 4px; }
.style-btn { padding: 4px 8px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08); border-radius: 6px; color: #9ca3af; font-size: 11px; cursor: pointer; transition: all 0.2s; white-space: nowrap; }
.style-btn:hover { background: rgba(139,92,246,0.1); }
.style-btn.active { background: rgba(139,92,246,0.2); border-color: rgba(139,92,246,0.3); color: #c4b5fd; }

.tts-select select { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; color: #e0e0e0; padding: 4px 10px; font-size: 13px; outline: none; cursor: pointer; }

.subtitle-toggle { display: flex; align-items: center; gap: 6px; }
.toggle-btn { padding: 3px 10px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; color: #9ca3af; font-size: 12px; cursor: pointer; transition: all 0.2s; }
.toggle-btn.on { background: rgba(34,197,94,0.15); border-color: rgba(34,197,94,0.3); color: #4ade80; }

.btn-generate { display: inline-flex; align-items: center; gap: 6px; padding: 9px 24px; background: linear-gradient(135deg,#6366f1,#8b5cf6); color: #fff; border: none; border-radius: 9px; font-size: 14px; font-weight: 600; cursor: pointer; white-space: nowrap; }
.btn-generate:hover:not(:disabled) { opacity: 0.9; transform: translateY(-1px); }
.btn-generate:disabled { opacity: 0.5; cursor: not-allowed; }

.spinner, .spinner-small { border-radius: 50%; animation: spin 0.6s linear infinite; display: inline-block; }
.spinner { width: 15px; height: 15px; border: 2px solid rgba(255,255,255,0.3); border-top-color: #fff; }
.spinner-small { width: 10px; height: 10px; border: 2px solid rgba(255,255,255,0.3); border-top-color: #c4b5fd; }
@keyframes spin { to { transform: rotate(360deg); } }

.examples { margin-top: 20px; display: flex; flex-wrap: wrap; align-items: center; gap: 8px; justify-content: center; }
.examples-label { font-size: 12px; color: #6b7280; }
.example-chip { padding: 5px 12px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; color: #c4b5fd; font-size: 12px; cursor: pointer; transition: background 0.2s; }
.example-chip:hover { background: rgba(139,92,246,0.12); }

.error-msg { display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.2); border-radius: 8px; color: #fca5a5; margin-bottom: 20px; font-size: 13px; }
.error-msg button { background: none; border: none; color: #fca5a5; cursor: pointer; }

.result-section { animation: fadeIn 0.4s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

.result-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 12px; }
.result-header h2 { font-size: 22px; color: #e0e0ff; }
.result-actions { display: flex; gap: 6px; flex-shrink: 0; }
.btn-primary { padding: 7px 16px; background: linear-gradient(135deg,#6366f1,#8b5cf6); color: #fff; border: none; border-radius: 7px; font-size: 13px; font-weight: 500; cursor: pointer; white-space: nowrap; display: inline-flex; align-items: center; gap: 4px; }
.btn-secondary { padding: 7px 16px; background: rgba(255,255,255,0.06); color: #e0e0e0; border: 1px solid rgba(255,255,255,0.1); border-radius: 7px; font-size: 13px; cursor: pointer; white-space: nowrap; }
.btn-primary:disabled, .btn-secondary:disabled { opacity: 0.5; cursor: not-allowed; }

.full-text { color: #9ca3af; font-size: 13px; line-height: 1.6; margin-bottom: 20px; padding: 14px; background: rgba(255,255,255,0.02); border-radius: 8px; }

/* Scene cards */
.scene-list { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
.scene-card { flex: 1; min-width: 150px; padding: 12px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; cursor: pointer; transition: all 0.2s; }
.scene-card:hover { background: rgba(255,255,255,0.05); }
.scene-card.active { background: rgba(139,92,246,0.1); border-color: rgba(139,92,246,0.25); }
.scene-card-header { display: flex; justify-content: space-between; margin-bottom: 4px; }
.scene-num { font-size: 12px; color: #c4b5fd; font-weight: 600; }
.scene-dur { font-size: 11px; color: #6b7280; }
.scene-card-title { font-size: 13px; color: #e0e0e0; margin-bottom: 8px; }

.scene-tools { display: flex; gap: 4px; flex-wrap: wrap; }
.tool-btn { padding: 3px 8px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06); border-radius: 5px; color: #9ca3af; font-size: 11px; cursor: pointer; transition: all 0.15s; white-space: nowrap; display: inline-flex; align-items: center; gap: 2px; }
.tool-btn:hover { background: rgba(139,92,246,0.1); color: #c4b5fd; border-color: rgba(139,92,246,0.2); }
.tool-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.regen-box { display: flex; gap: 4px; margin-top: 8px; }
.regen-input { flex: 1; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 5px; color: #e0e0e0; padding: 4px 8px; font-size: 12px; outline: none; font-family: inherit; }
.btn-regen-go { padding: 4px 12px; background: rgba(139,92,246,0.2); border: 1px solid rgba(139,92,246,0.3); border-radius: 5px; color: #c4b5fd; font-size: 12px; cursor: pointer; white-space: nowrap; display: inline-flex; align-items: center; gap: 4px; }
.btn-regen-go:disabled { opacity: 0.5; }

/* Preview */
.preview-container { position: relative; width: 100%; background: #000; border-radius: 10px; overflow: hidden; border: 1px solid rgba(255,255,255,0.06); }
.preview-frame { width: 100%; height: 100%; border: none; }
.preview-hint { text-align: center; color: #6b7280; font-size: 11px; margin-top: 8px; }
</style>
