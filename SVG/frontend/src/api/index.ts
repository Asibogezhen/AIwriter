import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  timeout: 600000,
});

export interface GenerateResponse {
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
