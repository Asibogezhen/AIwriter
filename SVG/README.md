# SVG AI 动画生成器

一句话生成动画视频——输入主题，AI 自动创作文案、设计 HTML 动画、渲染为 MP4 视频。

## 架构

```
用户浏览器 (Vue 3)
    │
    ▼
 Nginx (前端静态服务 + /api 反向代理)
    │
    ▼
 FastAPI 后端 (Python)
    │  ├─ DeepSeek API → 文案生成 + HTML 动画生成
    │  ├─ Edge TTS → 语音合成 + 字幕时间轴
    │  └─ 渲染代理 → 转发至 Node.js 渲染服务
    │
    ▼
 Puppeteer 渲染服务 (Node.js)
    ├─ Chromium → HTML 截图/录屏
    └─ FFmpeg → 帧编码为 MP4
```

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3 + TypeScript + Vite + Axios |
| 后端 | FastAPI + httpx + Pydantic |
| AI | DeepSeek v4-pro（OpenAI 兼容 API） |
| TTS | Microsoft Edge TTS（edge-tts，免费） |
| 渲染 | Puppeteer + Chromium + FFmpeg |
| 部署 | Docker Compose |

## 功能

- **AI 文案生成**：输入主题，DeepSeek 自动生成旁白文案，按语义拆分为 6-10 个场景
- **HTML 动画生成**：每个场景生成独立 HTML 页面，含多层背景、粒子装饰、CSS 关键帧动画
- **多风格支持**：科技感、水墨风、赛博朋克、扁平化、3D 质感、手绘风，AI 自动适配配色与动效
- **多比例支持**：横屏 16:9、竖屏 9:16、方形 1:1
- **TTS 语音**：5 种微软中文语音可选，词级时间戳对齐
- **字幕烧录**：ASS 字幕自动生成并嵌入视频，单行 ≤16 字，保证可读性
- **场景重生成**：对不满意的场景可单独重生成，支持文字反馈
- **历史管理**：生成结果自动保存，支持回溯、删除
- **视频下载**：支持单场景 MP4、全部场景拼接 MP4、配音 MP3 独立下载

## 快速开始

### 环境要求

- Docker & Docker Compose
- DeepSeek API Key

### 配置

```bash
# 编辑 .env
DEEPSEEK_API_KEY=sk-your-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
FRONTEND_PORT=5276
```

### 启动

```bash
docker compose up -d --build
```

访问 http://localhost:5276

### 本地开发

```bash
# 后端
cd backend && pip install -r requirements.txt && uvicorn backend.main:app --reload --port 8000

# 前端
cd frontend && npm install && npm run dev

# 渲染服务
cd render-service && npm install && npm start
```

## 项目结构

```
SVG/
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.ts
│   │   ├── style.css
│   │   ├── api/index.ts    # API 客户端 + 类型定义
│   │   ├── router/         # Vue Router 路由
│   │   └── views/Home.vue  # 主页面（输入、预览、历史）
│   ├── nginx.conf           # 生产环境 Nginx 配置
│   └── Dockerfile
├── backend/                 # FastAPI 后端
│   ├── main.py              # 应用入口
│   ├── config.py            # 环境变量配置
│   ├── routers/
│   │   ├── generate.py      # 核心路由：生成、重生成、渲染、TTS
│   │   └── history.py       # 历史记录 CRUD
│   └── services/
│       ├── deepseek.py      # DeepSeek API 调用 + Prompt 工程
│       ├── tts.py           # Edge TTS + 字幕对齐
│       └── history.py       # JSON 文件持久化
├── render-service/          # Puppeteer 渲染服务
│   ├── server.js            # Express 服务 + 截图/录屏/FFmpeg 编码
│   └── Dockerfile
├── docker-compose.yml
├── .env
└── start.bat                # Windows 本地一键启动脚本
```

---

## 优化方向

### 生成质量

- **流式生成**：后端改为 SSE 流式推送，前端实时展示生成进度（"正在创作文案…"→"正在生成场景 3/8…"），替代目前的全量等待
- **模板系统**：预置多套 HTML 动画模板（如：数据图表、时间轴、对比展示），AI 选模板只填内容，减少 Token 消耗和截断概率
- **跨场景风格一致性**：增加"全局调色板"约束，确保所有场景的色彩、字体、动效风格统一，目前各场景独立生成可能出现风格跳跃
- **动画时长精度**：引入 CSS `animation-duration` 精确计算 + Puppeteer 帧率校准，解决"动画提前结束/超时"问题

### 渲染性能

- **GPU 加速编码**：优先使用硬件编码器（h264_amf/NVENC/QSV），目前已有 fallback 链但可增加 GPU 可用性检测
- **渲染队列**：多用户并发时引入任务队列（Redis + BullMQ），避免多个 Chromium 实例同时运行导致 OOM
- **帧缓存**：将截图帧存为临时 PNG 然后编码为 H.264 时使用 CRF 调优（当前 ultrafast preset 体积偏大）
- **视频预渲染**：对历史记录中的场景，提供"缓存视频"选项，避免重复渲染

### 功能扩展

- **背景音乐**：支持上传或从免版权音乐库选择 BGM，FFmpeg 混音
- **多语言 TTS**：接入更多语音引擎（Azure Speech、Fish-Speech 等），支持英文/日文旁白
- **导出格式**：增加 GIF 动图导出（短场景适用）、WebM 格式
- **协作分享**：生成结果生成分享链接，他人可查看/评论
- **Prompt 优化**：记录用户反馈（重生成时的修改意见），形成 Few-shot 示例库，提升后续生成命中率
- **画中画/分屏**：支持多场景同屏展示（如对比 A/B 方案）

### 工程与运维

- **用户认证**：简单的 API Key 或 OAuth 登录，保护生成资源不被滥用
- **日志与监控**：接入 Sentry/GL 异常追踪 + Prometheus 指标（生成耗时、渲染成功率、API 调用量）
- **自动化测试**：补充 API 集成测试 + 前端组件测试 + HTML 动画截图对比测试
- **CI/CD**：GitHub Actions 自动构建 Docker 镜像并推送到 Registry
- **API 限流**：对 DeepSeek API 调用增加重试/退避策略，避免 Rate Limit
- **数据迁移**：历史记录从 JSON 文件迁移到 SQLite/PostgreSQL，支持搜索和分页

### 前端体验

- **渐进式生成预览**：每完成一个场景立即展示 iframe 预览，不用等全部完成
- **拖拽排序场景**：生成后允许拖拽调整场景顺序，自动重新组装 combined HTML
- **移动端适配**：当前为桌面端设计，移动端布局需要响应式改造
- **暗色/亮色主题**：当前硬编码暗色主题，增加主题切换
- **快捷键**：Ctrl+Enter 生成、方向键切换场景预览、Esc 关闭弹窗
