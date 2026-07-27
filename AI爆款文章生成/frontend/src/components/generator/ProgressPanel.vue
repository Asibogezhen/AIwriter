<template>
  <div class="progress-panel">
    <!-- 步骤条 -->
    <div class="steps-card">
      <a-steps :current="currentStep" size="small">
        <a-step v-for="s in steps" :key="s.key" :title="s.title" />
      </a-steps>
      <a-progress :percent="percent" :show-info="false" style="margin-top: 16px;" />
    </div>

    <!-- 正文流式 -->
    <div class="content-card" v-if="content">
      <div class="card-header">文章正文</div>
      <div class="card-body">
        <MarkdownRender :content="content" />
        <span v-if="!isCompleted" class="typing-cursor">|</span>
      </div>
    </div>

    <!-- 配图 -->
    <div class="images-card" v-if="images.length > 0">
      <div class="card-header">配图生成</div>
      <div class="card-body">
        <div class="images-grid">
          <div class="image-item" v-for="img in images" :key="img.position">
            <a-image :src="img.url" :preview="true" />
            <div class="image-label">{{ img.sectionTitle || `配图 ${img.position}` }}</div>
          </div>
        </div>
        <a-spin v-if="!isCompleted && !error" size="small" style="margin-top: 12px;" />
      </div>
    </div>

    <!-- 错误 -->
    <a-alert v-if="error" type="error" :message="error" show-icon closable style="margin-bottom: 16px;" />

    <!-- 完成 -->
    <div v-if="isCompleted && fullContent" class="done-card">
      <div class="done-icon"><CheckCircleOutlined /></div>
      <div class="done-title">文章生成完毕</div>
      <div class="done-actions">
        <a-space size="middle">
          <a-button type="primary" size="large" class="btn-primary-gradient" @click="$emit('view-detail')">查看文章</a-button>
          <a-button size="large" @click="$emit('copy')">复制全文</a-button>
          <a-button size="large" @click="$emit('regenerate')">重新生成</a-button>
        </a-space>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { CheckCircleOutlined } from '@ant-design/icons-vue'
import MarkdownRender from '../common/MarkdownRender.vue'

const props = defineProps<{
  percent: number
  content: string
  images: Array<{ position: number; url: string; method: string; sectionTitle: string }>
  fullContent: string
  isCompleted: boolean
  error: string
  platform?: string
}>()

defineEmits<{ 'view-detail': []; copy: []; regenerate: [] }>()

const articleSteps = [
  { key: 'title', title: '生成标题' },
  { key: 'search', title: '搜索资料' },
  { key: 'outline', title: '生成大纲' },
  { key: 'content', title: '写正文' },
  { key: 'image', title: '配图' },
  { key: 'render', title: '合成' },
]

const xhsSteps = [
  { key: 'title', title: '生成标题' },
  { key: 'content', title: '写笔记' },
  { key: 'image', title: 'AI 配图' },
  { key: 'render', title: '图文合成' },
]

const steps = computed(() => props.platform === 'xiaohongshu' ? xhsSteps : articleSteps)

const currentStep = computed(() => {
  const max = steps.value.length - 1
  if (props.percent < 12) return 0
  if (props.percent < 35) return 1
  if (props.percent < 65) return Math.min(2, max)
  if (props.percent < 90) return Math.min(3, max)
  return max
})
</script>

<style scoped>
.progress-panel {
  max-width: 900px;
  margin: 0 auto;
}

.steps-card,
.content-card,
.images-card {
  background: white;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  padding: 20px 24px;
  margin-bottom: 16px;
  box-shadow: var(--shadow-sm);
}

.card-header {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--color-text);
}

.card-body {
  color: var(--color-text);
}

.images-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.image-item {
  border-radius: var(--radius-md);
  overflow: hidden;
  border: 1px solid var(--color-border);
  transition: all var(--transition-normal);
}

.image-item:hover {
  border-color: var(--color-primary-light);
  box-shadow: var(--shadow-card-hover);
}

.image-item img {
  width: 100%;
  display: block;
}

.image-label {
  text-align: center;
  padding: 6px 4px;
  font-size: 12px;
  color: var(--color-text-muted);
}

.typing-cursor {
  display: inline-block;
  width: 2px;
  height: 20px;
  background: var(--color-primary);
  animation: blink 0.8s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.done-card {
  text-align: center;
  padding: 60px 20px;
  background: white;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
}

.done-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: rgba(34, 197, 94, 0.1);
  color: var(--color-primary);
  font-size: 32px;
  margin-bottom: 16px;
}

.done-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 24px;
}

.done-actions {
  display: flex;
  justify-content: center;
}
</style>
