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
    headless: true,
    args: [
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-gpu",
      "--disable-dev-shm-usage",
    ],
  });
  return browser;
}

async function recordVideo(html, { width = 1280, height = 720, fps = 15, audioPath = null }) {
  const workDir = join(tmpdir(), `svg-render-${randomUUID()}`);
  const inputPath = join(workDir, "index.html");
  const framesDir = join(workDir, "frames");
  const outputPath = join(workDir, "output.mp4");

  await mkdir(workDir);
  await mkdir(framesDir);
  await writeFile(inputPath, html, "utf-8");

  const b = await getBrowser();

  try {
    const page = await b.newPage();
    await page.setViewport({ width, height });

    // 在页面脚本执行前注入标志，阻止 autoPlay 启动
    await page.evaluateOnNewDocument(() => {
      window.__RENDER_MODE = true;
    });

    console.log(`[render] 加载页面...`);
    await page.goto(`file://${inputPath}`, {
      waitUntil: "networkidle0",
      timeout: 30_000,
    });

    const totalDuration = await page.evaluate(() => {
      return window.__hf ? window.__hf.duration : 10;
    });

    const totalFrames = Math.ceil(totalDuration * fps);
    console.log(`[render] ${totalDuration}s, ${totalFrames}帧, ${fps}fps, ${width}x${height}`);

    for (let i = 0; i < totalFrames; i++) {
      const t = i / fps;
      await page.evaluate((time) => {
        if (window.__hf && window.__hf.seek) {
          window.__hf.seek(time);
        }
      }, t);

      const framePath = join(framesDir, `frame-${String(i).padStart(6, "0")}.jpg`);
      await page.screenshot({ path: framePath, type: "jpeg", quality: 85 });

      if (i % 30 === 0) {
        console.log(`[render] 进度: ${Math.round((i / totalFrames) * 100)}% (${t.toFixed(1)}s)`);
      }
    }

    await page.close();
    console.log(`[render] 截图完成，编码中...`);

    await new Promise((resolve, reject) => {
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

    await rm(framesDir, { recursive: true, force: true });

    console.log(`[render] 完成: ${outputPath}`);
    return outputPath;
  } finally {
    // keep browser alive for reuse
  }
}

app.post("/render", async (req, res) => {
  const { html, width = 1280, height = 720, fps = 15, audio_base64 = "" } = req.body;

  if (!html) {
    return res.status(400).json({ error: "缺少html字段" });
  }

  let audioPath = null;
  try {
    if (audio_base64) {
      const audioDir = join(tmpdir(), `svg-audio-${randomUUID()}`);
      await mkdir(audioDir, { recursive: true });
      audioPath = join(audioDir, "voiceover.mp3");
      const audioBuffer = Buffer.from(audio_base64, "base64");
      await writeFile(audioPath, audioBuffer);
    }

    const outputPath = await recordVideo(html, { width, height, fps, audioPath });

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
    if (audioPath) {
      try { await rm(audioPath, { force: true }); } catch {}
    }
  }
});

app.get("/health", (_req, res) => {
  res.json({ status: "ok", browser: !!browser?.connected });
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`渲染服务运行在 http://localhost:${PORT}`);
});
