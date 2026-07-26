import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  timeout: 900000,
});

export interface GenerateResponse {
  id: string;
  title: string;
  full_text: string;
  scenes: Array<{
    index: number;
    title: string;
    text: string;
    duration: number;
    style_hint: string;
  }>;
  total_duration: number;
  combined_html: string;
  scenes_html: string[];
  width: number;
  height: number;
  style: string;
  aspect?: string;
  prompt?: string;
}

export async function generateAnimation(prompt: string, tts = "none", aspect = "16:9", style = "none", subtitles = true) {
  const { data } = await api.post<GenerateResponse>("/generate", { prompt, tts, aspect, style, subtitles });
  return data;
}

export async function regenerateScene(
  title: string,
  scene: object,
  scenes: object[],
  scenesHtml: string[],
  aspect: string,
  feedback = "",
  style = "none",
) {
  const { data } = await api.post<{ index: number; html: string; combined_html?: string }>("/regenerate-scene", {
    title, scene, scenes, scenes_html: scenesHtml, aspect, feedback, style,
  });
  return data;
}

export async function renderVideo(html: string, width = 1280, height = 720, fps = 15): Promise<Blob> {
  const { data } = await api.post(
    "/render",
    { html, width, height, fps },
    { responseType: "blob", timeout: 600000 }
  );
  return data;
}

export async function generateTTS(text: string, voice = "zh-CN-XiaoxiaoNeural"): Promise<Blob> {
  const { data } = await api.post(
    "/generate-tts",
    { text, voice },
    { responseType: "blob", timeout: 120000 }
  );
  return data;
}

export interface HistoryEntry {
  id: string;
  created_at: string;
  prompt: string;
  title: string;
  scene_count: number;
  total_duration: number;
  style: string;
  aspect: string;
}

export async function getHistory() {
  const { data } = await api.get<HistoryEntry[]>("/history");
  return data;
}

export async function getHistoryEntry(id: string) {
  const { data } = await api.get<GenerateResponse>(`/history/${id}`);
  return data;
}

export async function deleteHistoryEntry(id: string) {
  await api.delete(`/history/${id}`);
}

export async function renderVideoWithAudio(
  html: string,
  width = 1280,
  height = 720,
  fps = 15,
  ttsText = "",
  ttsVoice = "zh-CN-XiaoxiaoNeural",
  scenes: object[] = [],
  scenesHtml: string[] = [],
  subtitles = true,
): Promise<Blob> {
  const { data } = await api.post(
    "/render-with-audio",
    { html, width, height, fps, tts_text: ttsText, tts_voice: ttsVoice, scenes, scenes_html: scenesHtml, subtitles },
    { responseType: "blob", timeout: 600000 }
  );
  return data;
}

export async function renderAllScenes(
  scenesHtml: string[],
  width = 1280,
  height = 720,
  fps = 24,
  durations: number[] = [],
): Promise<Blob> {
  const { data } = await api.post(
    "/render-all",
    { scenes_html: scenesHtml, width, height, fps, durations },
    { responseType: "blob", timeout: 900000 }
  );
  return data;
}
