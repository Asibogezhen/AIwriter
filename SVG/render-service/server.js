import express from "express";
import puppeteer from "puppeteer";
import { writeFile, mkdir, rm } from "node:fs/promises";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { randomUUID } from "node:crypto";

const app = express();
app.use(express.json({ limit: "10mb" }));
app.use((_req, res, next) => {
  res.setTimeout(900_000);
  next();
});

let browser = null;

async function getBrowser() {
  if (browser && browser.connected) return browser;
  browser = await puppeteer.launch({
    headless: "new",
    args: [
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-gpu",
      "--disable-dev-shm-usage",
      "--run-all-compositor-stages-before-draw",
      "--disable-features=TranslateUI",
    ],
  });
  return browser;
}

async function renderFrames(html, framesDir, { width, height, fps: targetFps, durationOverride = null }) {
  const b = await getBrowser();
  const page = await b.newPage();
  await page.setViewport({ width, height });

  const htmlPath = join(framesDir, "index.html");
  await writeFile(htmlPath, html, "utf-8");
  await page.goto(`file://${htmlPath}`, { waitUntil: "load", timeout: 60000 });

  await page.evaluate(() => new Promise(r => {
    requestAnimationFrame(() => requestAnimationFrame(r));
  }));

  const duration = durationOverride != null ? durationOverride : await page.evaluate(() => {
    return window.__hf ? window.__hf.duration : 5;
  });

  const client = await page.target().createCDPSession();
  const capturedFrames = [];
  client.on("Page.screencastFrame", ({ data, sessionId }) => {
    capturedFrames.push(data);
    client.send("Page.screencastFrameAck", { sessionId }).catch(() => {});
  });

  await client.send("Page.startScreencast", {
    format: "jpeg", quality: 85, maxWidth: width, maxHeight: height,
  });

  // 预热：等第一帧到达
  for (let i = 0; i < 30 && capturedFrames.length === 0; i++) {
    await new Promise(r => setTimeout(r, 100));
  }

  const hasFrames = capturedFrames.length > 0;
  if (hasFrames) {
    capturedFrames.length = 0; // 丢弃预热帧
    await new Promise(r => setTimeout(r, (duration + 0.5) * 1000));
  }

  await client.send("Page.stopScreencast");
  await page.close();

  if (!hasFrames) {
    console.log(`[scene] screencast 无帧，回退截图模式`);
    return renderFramesFallback(html, framesDir, { width, height, fps: targetFps, duration });
  }

  // 保存所有捕捉到的帧，不采样、不丢帧
  for (let i = 0; i < capturedFrames.length; i++) {
    const framePath = join(framesDir, `frame-${String(i).padStart(6, "0")}.jpg`);
    await writeFile(framePath, Buffer.from(capturedFrames[i], "base64"));
  }

  // 用实际捕捉速率作为视频 FPS，保持原速
  const effectiveFps = Math.max(1, Math.round(capturedFrames.length / duration));

  return { duration, totalFrames: capturedFrames.length, fps: effectiveFps };
}

/* 逐帧截图回退：保留 slowFactor 确保 CSS 动画跟得上截图速度 */
async function renderFramesFallback(html, framesDir, { width, height, fps, duration }) {
  const b = await getBrowser();
  const page = await b.newPage();
  await page.setViewport({ width, height });

  const htmlPath = join(framesDir, "index_fallback.html");
  await writeFile(htmlPath, html, "utf-8");
  await page.goto(`file://${htmlPath}`, { waitUntil: "load", timeout: 60000 });

  await page.evaluate(() => new Promise(r => {
    requestAnimationFrame(() => requestAnimationFrame(r));
  }));

  const slowFactor = 3;
  await page.evaluate((factor) => {
    const all = document.querySelectorAll("*");
    for (const el of all) {
      const style = getComputedStyle(el);
      const dur = parseFloat(style.animationDuration);
      if (dur > 0 && isFinite(dur)) {
        el.style.animationDuration = (dur * factor) + "s";
      }
      const delay = parseFloat(style.animationDelay);
      if (delay > 0 && isFinite(delay)) {
        el.style.animationDelay = (delay * factor) + "s";
      }
    }
  }, slowFactor);

  const totalFrames = Math.ceil(duration * fps);
  for (let j = 0; j < totalFrames; j++) {
    const t = j / fps;
    await page.evaluate((time) => {
      if (window.__hf && window.__hf.seek) window.__hf.seek(time);
    }, t);
    await page.evaluate(() => new Promise(r => requestAnimationFrame(r)));
    const framePath = join(framesDir, `frame-${String(j).padStart(6, "0")}.jpg`);
    await page.screenshot({ path: framePath, type: "jpeg", quality: 85 });
  }
  await page.close();
  return { duration, totalFrames, fps };
}

function encodeFrames(framesDir, outputPath, fps, audioPath, subPath) {
  return new Promise((resolve, reject) => {
    let vf = "";
    if (subPath) {
      const subSafe = subPath.replace(/\\/g, "/");
      vf = `subtitles='${subSafe}'`;
    }

    const codecs = ["h264_amf", "h264_nvenc", "h264_qsv", "libx264"];
    const run = (idx) => {
      const args = [
        "-y",
        "-framerate", String(fps),
        "-i", join(framesDir, "frame-%06d.jpg"),
      ];
      if (audioPath) {
        args.push("-i", audioPath);
      }
      if (vf) {
        args.push("-vf", vf);
      }
      args.push(
        "-c:v", codecs[idx],
        "-pix_fmt", "yuv420p",
        "-preset", "ultrafast",
        "-crf", "28",
      );
      if (audioPath) {
        args.push("-c:a", "aac", "-b:a", "128k", "-shortest",
          "-map", "0:v:0", "-map", "1:a:0");
      }
      args.push(outputPath);

      const ffmpeg = spawn("ffmpeg", args, { stdio: "pipe" });
      let stderr = "";
      ffmpeg.stderr.on("data", (d) => { stderr += d.toString(); });
      ffmpeg.on("close", (code) => {
        if (code === 0) { resolve(); }
        else if (idx < codecs.length - 1) { run(idx + 1); }
        else { reject(new Error(`FFmpeg exit ${code}: ${stderr.slice(-300)}`)); }
      });
      ffmpeg.on("error", () => {
        if (idx < codecs.length - 1) run(idx + 1);
        else reject(new Error("无可用编码器"));
      });
    };
    run(0);
  });
}

async function renderSceneVideo(html, workDir, { width, height, fps, duration }) {
  const framesDir = join(workDir, "frames");
  await mkdir(framesDir);
  const outPath = join(workDir, "scene.mp4");

  const result = await renderFrames(html, framesDir, {
    width, height, fps, durationOverride: duration,
  });
  console.log(`[scene] ${result.duration.toFixed(1)}s, ${result.totalFrames}帧, ${result.fps}fps`);
  await encodeFrames(framesDir, outPath, result.fps, null, null);
  await rm(framesDir, { recursive: true, force: true });
  return outPath;
}

function concatVideos(concatFilePath, outputPath) {
  return new Promise((resolve, reject) => {
    const codecs = ["h264_amf", "h264_nvenc", "h264_qsv", "libx264"];
    const run = (idx) => {
      const args = [
        "-y",
        "-f", "concat", "-safe", "0", "-i", concatFilePath,
        "-c:v", codecs[idx],
        "-pix_fmt", "yuv420p",
        "-preset", "ultrafast",
        "-crf", "28",
        outputPath,
      ];
      const ffmpeg = spawn("ffmpeg", args, { stdio: "pipe" });
      let stderr = "";
      ffmpeg.stderr.on("data", (d) => { stderr += d.toString(); });
      ffmpeg.on("close", (code) => {
        if (code === 0) { resolve(); }
        else if (idx < codecs.length - 1) { run(idx + 1); }
        else { reject(new Error(`FFmpeg concat exit ${code}: ${stderr.slice(-300)}`)); }
      });
      ffmpeg.on("error", () => {
        if (idx < codecs.length - 1) run(idx + 1);
        else reject(new Error("无可用编码器"));
      });
    };
    run(0);
  });
}

// =========== 单场景渲染 ===========

app.post("/render", async (req, res) => {
  const { html, width = 1280, height = 720, fps = 15, audio_base64 = "", subtitle_content = "" } = req.body;

  if (!html) {
    return res.status(400).json({ error: "缺少html字段" });
  }

  let audioPath = null;
  let subPath = null;
  const workDir = join(tmpdir(), `svg-render-${randomUUID()}`);
  await mkdir(workDir, { recursive: true });
  const framesDir = join(workDir, "frames");
  await mkdir(framesDir);
  const outputPath = join(workDir, "output.mp4");

  try {
    if (audio_base64) {
      audioPath = join(workDir, "voiceover.mp3");
      await writeFile(audioPath, Buffer.from(audio_base64, "base64"));
    }
    if (subtitle_content) {
      subPath = join(workDir, "subtitles.ass");
      await writeFile(subPath, subtitle_content, "utf-8");
    }

    const result = await renderFrames(html, framesDir, { width, height, fps });
    console.log(`[render] ${result.duration.toFixed(1)}s, ${result.totalFrames}帧, ${result.fps}fps, ${width}x${height}`);
    await encodeFrames(framesDir, outputPath, result.fps, audioPath, subPath);

    if (!existsSync(outputPath)) {
      throw new Error("渲染失败，输出文件不存在");
    }

    res.setHeader("Content-Type", "video/mp4");
    res.setHeader("Content-Disposition", "attachment; filename=output.mp4");
    res.sendFile(outputPath);
  } catch (err) {
    console.error("[render] 错误:", err);
    res.status(500).json({ error: err.message });
  } finally {
    try { await rm(workDir, { recursive: true, force: true }); } catch {}
  }
});

// =========== 多场景拼接渲染（纯视频，无语音无字幕）===========

app.post("/render-all", async (req, res) => {
  const { scenes_html, durations, width = 1280, height = 720, fps = 24 } = req.body;

  if (!scenes_html || !Array.isArray(scenes_html) || scenes_html.length === 0) {
    return res.status(400).json({ error: "缺少scenes_html数组" });
  }

  const mainDir = join(tmpdir(), `svg-render-all-${randomUUID()}`);
  await mkdir(mainDir, { recursive: true });

  try {
    const CONCURRENCY = 3;
    const sceneVideos = new Array(scenes_html.length);

    for (let batch = 0; batch < scenes_html.length; batch += CONCURRENCY) {
      const jobs = [];
      for (let i = batch; i < Math.min(batch + CONCURRENCY, scenes_html.length); i++) {
        const sceneDir = join(mainDir, `scene-${i}`);
        const dur = durations?.[i] != null ? durations[i] : null;
        jobs.push((async (idx, dir, d) => {
          await mkdir(dir);
          console.log(`[render-all] 场景${idx} 开始 (${d != null ? d.toFixed(1) + 's' : 'auto'})`);
          const p = await renderSceneVideo(scenes_html[idx], dir, { width, height, fps, duration: d });
          console.log(`[render-all] 场景${idx} 完成`);
          return { index: idx, path: p };
        })(i, sceneDir, dur));
      }

      const results = await Promise.all(jobs);
      for (const { index, path } of results) {
        sceneVideos[index] = path;
      }
      console.log(`[render-all] 批次完成 (${results.length}个场景)`);
    }

    const concatFile = join(mainDir, "concat.txt");
    let concatContent = "";
    for (const p of sceneVideos) {
      concatContent += `file '${p.replace(/\\/g, "/")}'\n`;
    }
    await writeFile(concatFile, concatContent, "utf-8");

    const outputPath = join(mainDir, "output.mp4");
    console.log(`[render-all] 拼接 ${sceneVideos.length} 个场景...`);
    await concatVideos(concatFile, outputPath);

    if (!existsSync(outputPath)) {
      throw new Error("渲染失败，输出文件不存在");
    }

    console.log(`[render-all] 完成: ${outputPath}`);
    res.setHeader("Content-Type", "video/mp4");
    res.setHeader("Content-Disposition", "attachment; filename=output.mp4");
    res.sendFile(outputPath);
  } catch (err) {
    console.error("[render-all] 错误:", err);
    res.status(500).json({ error: err.message });
  } finally {
    try { await rm(mainDir, { recursive: true, force: true }); } catch {}
  }
});

app.get("/health", (_req, res) => {
  res.json({ status: "ok", browser: !!browser?.connected });
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`渲染服务运行在 http://localhost:${PORT}`);
});
