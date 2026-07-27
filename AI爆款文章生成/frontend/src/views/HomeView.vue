<template>
  <div id="homePage">
    <!-- Hero -->
    <div class="hero-section">
      <div class="hero-bg" />
      <div class="hero-orb orb-1" />
      <div class="hero-orb orb-2" />
      <div class="hero-orb orb-3" />
      <div class="container">
        <div class="hero-badge">
          <ThunderboltOutlined />
          <span>AI 驱动的内容创作平台</span>
        </div>
        <h1 class="hero-title">
          让<span class="hero-accent">每个人</span>都能写出<br/>10万+ 爆款文章
        </h1>
        <p class="hero-subtitle">多智能体协作，从选题到配图，一键生成高质量内容</p>

        <div class="input-wrapper">
          <a-input
            v-model:value="topic"
            placeholder="输入您想创作的文章选题，例如：2026年AI如何改变职场"
            size="large"
            class="topic-input"
            @pressEnter="goToCreate"
          >
            <template #prefix>
              <EditOutlined class="input-icon" />
            </template>
          </a-input>
          <a-button type="primary" size="large" class="cta-btn" @click="goToCreate">
            <RocketOutlined />
            开始创作
          </a-button>
        </div>
        <p class="hero-tips">工作总结、心得体会、演讲稿、分析报告... 一键生成</p>
      </div>
    </div>

    <!-- Features -->
    <div class="features-section">
      <div class="container">
        <div class="section-header">
          <div class="section-badge">核心能力</div>
          <h2 class="section-title">专业人士的一站式 AI 写作工具</h2>
          <p class="section-subtitle">强大的 AI 能力，让创作变得简单高效</p>
        </div>
        <div class="features-grid">
          <div v-for="(f, i) in features" :key="i" class="feature-card">
            <div class="feature-icon-wrapper" :style="{ background: `${f.color}15` }">
              <component :is="f.icon" class="feature-icon" :style="{ color: f.color }" />
            </div>
            <div class="feature-content">
              <h3 class="feature-title">{{ f.title }}</h3>
              <p class="feature-desc">{{ f.desc }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 最近文章（已登录时显示） -->
    <div v-if="auth.isLoggedIn && recentArticles.length > 0" class="articles-section">
      <div class="container">
        <div class="section-header-row">
          <div>
            <h2 class="section-title-sm">最近创作</h2>
            <p class="section-subtitle-sm">查看您最近创作的文章</p>
          </div>
          <RouterLink to="/history" class="view-all-btn">
            查看全部 <RightOutlined />
          </RouterLink>
        </div>
        <div class="articles-grid">
          <div v-for="a in recentArticles" :key="a.id" class="article-card" @click="$router.push(`/article/${a.id}`)">
            <div class="article-cover">
              <FileTextOutlined v-if="!a.coverImage" class="cover-placeholder" />
              <img v-else :src="a.coverImage" :alt="a.title" />
            </div>
            <div class="article-info">
              <h4 class="article-title">{{ a.title || a.topic }}</h4>
              <div class="article-meta">
                <span class="article-time"><ClockCircleOutlined /> {{ fmtTime(a.created_at) }}</span>
                <span :class="['article-status', `status-${a.status}`]">{{ statusLabel(a.status) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { articleApi } from '../api/article'
import {
  RocketOutlined,
  FileTextOutlined,
  OrderedListOutlined,
  EditOutlined,
  PictureOutlined,
  ThunderboltOutlined,
  ClockCircleOutlined,
  RightOutlined,
} from '@ant-design/icons-vue'

const router = useRouter()
const auth = useAuthStore()
const topic = ref('')
const recentArticles = ref<any[]>([])

const features = [
  { icon: FileTextOutlined, title: '智能生成标题', desc: 'AI 自动分析选题，生成吸引眼球的爆款标题', color: '#22C55E' },
  { icon: OrderedListOutlined, title: '自动生成大纲', desc: '智能规划文章结构，确保逻辑清晰完整', color: '#3B82F6' },
  { icon: EditOutlined, title: '流式生成正文', desc: '实时展示创作过程，体验打字机般的流畅输出', color: '#8B5CF6' },
  { icon: PictureOutlined, title: '智能配图', desc: '自动检索高质量无版权图片，完美匹配内容', color: '#F59E0B' },
  { icon: ThunderboltOutlined, title: '快速高效', desc: '5-10 分钟完成全文创作，效率提升 10 倍', color: '#EF4444' },
  { icon: ClockCircleOutlined, title: '历史管理', desc: '随时查看和管理所有创作记录，支持导出', color: '#06B6D4' },
]

function goToCreate() {
  const query = topic.value.trim() ? { topic: topic.value } : {}
  router.push({ path: '/generator', query })
}

function fmtTime(t: string) {
  if (!t) return '--'
  const d = new Date(t)
  return `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

function statusLabel(s: string) {
  const map: Record<string, string> = { completed: '已完成', generating: '生成中', pending: '等待中', failed: '失败' }
  return map[s] || s
}

onMounted(async () => {
  if (auth.isLoggedIn) {
    try {
      const data = await articleApi.list(1, 6)
      recentArticles.value = (data as any).records || []
    } catch { /* ignore */ }
  }
})
</script>

<style scoped>
#homePage {
  width: 100%;
  min-height: 100vh;
  background: var(--color-background);
}

/* Hero */
.hero-section {
  position: relative;
  padding: 80px 20px 100px;
  text-align: center;
  overflow: hidden;
}

.hero-bg {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: var(--gradient-hero-warm);
  z-index: 0;
}

.hero-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  z-index: 0;
  opacity: 0.5;
  pointer-events: none;
}

.orb-1 {
  width: 420px;
  height: 420px;
  background: rgba(34, 197, 94, 0.12);
  top: -150px;
  right: -100px;
  animation: orb-drift 12s ease-in-out infinite;
}

.orb-2 {
  width: 300px;
  height: 300px;
  background: rgba(212, 168, 83, 0.10);
  bottom: -80px;
  left: -60px;
  animation: orb-drift 15s ease-in-out infinite reverse;
}

.orb-3 {
  width: 200px;
  height: 200px;
  background: rgba(34, 197, 94, 0.08);
  top: 40%;
  left: 50%;
  animation: orb-drift 18s ease-in-out infinite;
}

@keyframes orb-drift {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -20px) scale(1.05); }
  66% { transform: translate(-20px, 15px) scale(0.95); }
}

.container {
  position: relative;
  z-index: 1;
  max-width: 900px;
  margin: 0 auto;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 20px;
  background: rgba(34, 197, 94, 0.06);
  border: 1px solid rgba(34, 197, 94, 0.15);
  border-radius: var(--radius-full);
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 28px;
  color: var(--color-primary-dark);
  letter-spacing: 0.5px;
  text-transform: uppercase;
  backdrop-filter: blur(4px);
}

.hero-title {
  font-size: 54px;
  font-weight: 700;
  margin: 0 0 20px;
  letter-spacing: -1.5px;
  line-height: 1.2;
  color: var(--color-text);
  max-width: 700px;
  margin-left: auto;
  margin-right: auto;
}

.hero-accent {
  background: linear-gradient(135deg, var(--color-primary-dark) 0%, var(--color-gold) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 800;
}

.hero-subtitle {
  font-size: 18px;
  margin: 0 0 40px;
  color: var(--color-text-secondary);
  font-weight: 400;
  line-height: 1.6;
}

.input-wrapper {
  display: flex;
  gap: 12px;
  max-width: 700px;
  margin: 0 auto 20px;
  padding: 8px;
  background: white;
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--color-border);
}

.topic-input {
  flex: 1;
  border: none !important;
  box-shadow: none !important;
  font-size: 16px;
  padding: 8px 16px;
  background: transparent !important;
}

.input-icon {
  color: var(--color-text-muted);
  font-size: 18px;
}

.cta-btn {
  height: 52px !important;
  padding: 0 32px !important;
  font-size: 16px !important;
  font-weight: 600 !important;
  border-radius: var(--radius-lg) !important;
  background: var(--gradient-primary) !important;
  border: none !important;
  color: white !important;
  box-shadow: var(--shadow-green) !important;
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
  position: relative;
  overflow: hidden;
}

.cta-btn::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.12), transparent);
  transition: left 0.6s ease;
}

.cta-btn:hover::after {
  left: 100%;
}

.hero-tips {
  font-size: 14px;
  color: var(--color-text-muted);
  margin: 0;
}

/* Features */
.features-section {
  padding: 80px 20px;
  background: var(--color-background-secondary);
}

.features-section .container {
  max-width: 1100px;
}

.section-header {
  text-align: center;
  margin-bottom: 48px;
}

.section-badge {
  display: inline-block;
  padding: 6px 16px;
  background: rgba(34, 197, 94, 0.06);
  border: 1px solid rgba(34, 197, 94, 0.12);
  border-radius: var(--radius-full);
  font-size: 12px;
  font-weight: 600;
  color: var(--color-primary-dark);
  margin-bottom: 16px;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.section-title {
  font-size: 32px;
  font-weight: 700;
  margin: 0 0 12px;
  color: var(--color-text);
  letter-spacing: -0.5px;
}

.section-subtitle {
  font-size: 16px;
  color: var(--color-text-secondary);
  margin: 0;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.feature-card {
  background: white;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  padding: 24px;
  display: flex;
  gap: 16px;
  align-items: flex-start;
  transition: all var(--transition-normal);
  position: relative;
  overflow: hidden;
}

.feature-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--gradient-card-glow);
  opacity: 0;
  transition: opacity var(--transition-normal);
}

.feature-card:hover {
  border-color: rgba(34, 197, 94, 0.2);
  box-shadow: 0 8px 30px rgba(34, 197, 94, 0.10), 0 0 0 1px rgba(34, 197, 94, 0.06);
  transform: translateY(-2px);
}

.feature-card:hover::before {
  opacity: 1;
}

.feature-icon-wrapper {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  flex-shrink: 0;
}

.feature-icon {
  font-size: 22px;
}

.feature-content {
  flex: 1;
  min-width: 0;
}

.feature-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 6px;
  color: var(--color-text);
}

.feature-desc {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
  line-height: 1.5;
}

/* Articles */
.articles-section {
  padding: 60px 20px 80px;
  background: var(--color-background);
}

.articles-section .container {
  max-width: 1100px;
}

.section-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}

.section-title-sm {
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 4px;
  color: var(--color-text);
}

.section-subtitle-sm {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
}

.view-all-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--color-primary);
  font-weight: 500;
  text-decoration: none;
}

.view-all-btn:hover {
  color: var(--color-primary-dark);
}

.articles-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.article-card {
  background: white;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  overflow: hidden;
  transition: all var(--transition-normal);
  cursor: pointer;
  position: relative;
}

.article-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--gradient-card-glow);
  opacity: 0;
  transition: opacity var(--transition-normal);
  z-index: 0;
}

.article-card:hover {
  border-color: rgba(34, 197, 94, 0.2);
  box-shadow: 0 8px 30px rgba(34, 197, 94, 0.10);
  transform: translateY(-2px);
}

.article-card:hover::before {
  opacity: 1;
}

.article-card > * {
  position: relative;
  z-index: 1;
}

.article-cover {
  height: 140px;
  background: var(--color-background-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.article-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-placeholder {
  font-size: 32px;
  color: var(--color-text-muted);
}

.article-info {
  padding: 16px;
}

.article-title {
  font-size: 15px;
  font-weight: 600;
  margin: 0 0 12px;
  color: var(--color-text);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.article-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.article-time {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--color-text-muted);
}

.article-status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-weight: 500;
}

.status-completed { background: rgba(34,197,94,0.1); color: var(--color-primary-dark); }
.status-generating { background: rgba(59,130,246,0.1); color: #2563EB; }
.status-pending { background: var(--color-background-tertiary); color: var(--color-text-muted); }
.status-failed { background: rgba(239,68,68,0.1); color: #DC2626; }

@media (max-width: 992px) {
  .features-grid, .articles-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 768px) {
  .hero-section { padding: 60px 20px 80px; }
  .hero-title { font-size: 36px; }
  .hero-subtitle { font-size: 16px; }
  .input-wrapper { flex-direction: column; padding: 12px; }
  .cta-btn { width: 100%; justify-content: center; }
  .features-grid, .articles-grid { grid-template-columns: 1fr; }
  .section-title { font-size: 24px; }
  .section-header-row { flex-direction: column; align-items: flex-start; gap: 16px; }
}
</style>
