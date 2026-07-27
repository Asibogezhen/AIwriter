# 墨笔 — 多智能体 AI 爆款文章生成器

> 输入一个选题，七个 AI Agent 串行协作，全自动生成配图长文或小红书笔记。

## 核心功能

- **多智能体流水线**：标题 → 大纲 → 搜索资料 → 正文生成 → 配图分析 → 配图生成 → 图文合成，7 个 Agent 串行编排
- **双平台支持**：公众号/知乎长文模式 + 小红书笔记模式（口语化、emoji、风格化配图）
- **实时流式输出**：正文通过 SSE 流式推送，打字机效果逐字呈现
- **三种配图来源**：Pexels 免费图库 / AI 文生图(Qwen-Image) / LLM 生成 SVG 示意图，自动轮换避免单一
- **搜索增强**：对接 Tavily 搜索引擎，为文章注入最新资料和数据
- **用户系统**：JWT 认证 + VIP 订阅（¥199 永久买断），新用户赠送 1 次免费生成

## 技术栈

| 层 | 技术 |
|---|---|
| 后端框架 | FastAPI + Uvicorn |
| 数据库 | PostgreSQL / SQLite，SQLAlchemy 2.0 + Alembic |
| AI 模型 | DeepSeek Chat（文本）、Qwen-Image-Max（文生图） |
| 前端 | Vue 3 + Vite + Ant Design Vue 4 + Pinia |
| 实时通信 | Server-Sent Events (SSE) |
| 容器化 | Docker Compose（app + frontend + PostgreSQL + Redis + Nginx） |

## 项目结构

```
AI爆款文章生成/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py            # 配置中心
│   │   ├── core/                # 数据库、LLM客户端、JWT、SSE管理器
│   │   ├── agents/              # 7 个 AI Agent（标题/大纲/搜索/正文/配图分析/配图生成/渲染）
│   │   ├── api/v1/              # REST API（认证、文章、VIP、管理）
│   │   ├── services/            # 外部服务（Pexels、Qwen-Image、Tavily、SVG生成）
│   │   ├── models/              # SQLAlchemy ORM 模型
│   │   ├── schemas/             # Pydantic 请求/响应模型
│   │   └── utils/               # Prompt 模板、小红书风格配置
│   ├── alembic/                 # 数据库迁移
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── views/               # 页面（首页/创作台/历史/文章详情/VIP/管理后台）
│   │   ├── components/          # 组件（创作表单/进度面板/Markdown渲染）
│   │   ├── composables/         # useSSE 流式连接
│   │   ├── stores/              # Pinia 认证状态
│   │   └── api/                 # Axios 请求封装
│   └── Dockerfile
├── docker-compose.yml
└── .env.example
```

## 快速开始

### 1. 配置环境变量

```bash
cp .env.example backend/.env
```

编辑 `backend/.env`，填入必要的 API 密钥：

```env
DEEPSEEK_API_KEY=sk-xxx          # 必填，核心 LLM
DASHSCOPE_API_KEY=xxx            # 可选，AI 文生图
PEXELS_API_KEY=xxx               # 可选，免费图库
TAVILY_API_KEY=xxx               # 可选，搜索增强
```

### 2. Docker 一键启动

```bash
docker compose up -d
```

前端访问 `http://localhost:3000`，后端 API 位于 `http://localhost:8000`。

### 3. 本地开发

```bash
# 后端
cd backend
pip install -r requirements.txt
# 将 DB_TYPE 改为 sqlite，注释掉 Redis 配置
uvicorn app.main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

前端开发服务器默认运行在 `http://localhost:5276`。

## API 概览

| 端点 | 说明 |
|---|---|
| `POST /api/v1/auth/register` | 用户注册 |
| `POST /api/v1/auth/login` | 用户登录 |
| `POST /api/v1/articles/generate` | 提交创作任务（返回 SSE 流地址） |
| `GET /api/v1/articles/generate/{id}/sse` | SSE 实时进度流 |
| `GET /api/v1/articles` | 文章列表（分页） |
| `GET /api/v1/articles/{id}` | 文章详情 |
| `DELETE /api/v1/articles/{id}` | 删除文章 |
| `GET /api/v1/vip/status` | VIP 状态查询 |
| `POST /api/v1/admin/redeem-codes` | 批量生成兑换码 |

## 创作流程

```
用户输入选题
  → Agent 1: 生成标题 + 副标题 + 备选
  → Agent 2: 生成文章大纲（小红书跳过）
  → Agent 3: 搜索最新参考资料（可选）
  → Agent 4: 流式生成正文（SSE 实时推送）
  → Agent 5: 智能分析配图需求
  → Agent 6: 并行生成所有配图（Pexels / SVG / AI 生图）
  → Agent 7: 图文合成，输出完整文章
```

## 优化方向

### 架构层面

- **Agent 并行化**：当前 7 个 Agent 完全串行，标题和大纲生成无依赖关系时可并行；配图生成已并行，但配图分析可与正文生成部分重叠
- **Agent 图编排**：从硬编码流水线迁移到 DAG 图编排（LangGraph / 自研），支持条件分支和动态路由，便于扩展新的内容形态
- **消息队列解耦**：当前异步任务直接在线程中启动，引入 Celery / Redis Queue 做任务队列，支持失败重试和水平扩展

### 性能与成本

- **LLM 调用优化**：引入 prompt caching 减少重复 system prompt 的 token 消耗；对短文本任务（标题、配图分析）考虑使用更便宜的模型
- **正文分片生成**：长文 >5000 字时，按章节分段生成后拼接，避免超长上下文导致的 token 截断和质量下降
- **图片懒加载与 CDN**：生成的图片目前本地存储，接入 OSS + CDN 加速分发；首页列表改为缩略图减少带宽

### 功能增强

- **模板/工作流市场**：允许用户保存和分享 Agent 编排模板（如"产品评测"、"教程"、"新闻稿"），降低重复配置成本
- **多轮对话编辑**：生成完成后支持"改写这一段"、"换个标题风格"等交互式修改，而非只能重新生成
- **数据分析与 A/B**：记录文章的标题、大纲、风格参数与实际阅读量/互动数据，反馈到 Prompt 优化形成数据飞轮
- **多平台一键分发**：生成后直接对接公众号草稿箱 API、知乎发布 API、小红书发布接口
- **品牌知识库**：为付费用户提供产品/品牌信息持久化存储，每次生成自动注入，减少重复输入

### 工程质量

- **测试覆盖**：当前 `tests/` 目录为空，需要补充 Agent 单元测试、API 集成测试和 E2E 测试
- **数据库迁移规范化**：当前 SQLite 兼容迁移写在 `main.py` 启动逻辑中，应统一迁移到 Alembic 管理
- **API 密钥安全**：`.env` 文件不应出现在 Git 历史中，需轮换已泄露的密钥并使用 `.env.local` 覆盖机制

### 前端体验

- **SSE 断线重连增强**：正文生成中断后支持从断点续传，而非整篇重来
- **移动端适配**：当前为桌面端设计，创作表单在小屏幕上体验需优化
- **创作历史搜索与筛选**：当前仅分页列表，加入按标题/日期/平台筛选和全文搜索

## License

MIT
