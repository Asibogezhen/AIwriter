<template>
  <div class="generator-page">
    <div class="page-header">
      <div class="header-container">
        <div>
          <h1 class="page-title">创作工作台</h1>
          <p class="page-subtitle">AI 多智能体协作，一键生成爆款内容</p>
        </div>
      </div>
    </div>

    <div class="generator-layout">
      <!-- 输入表单 -->
      <div class="left-panel" v-if="!showProgress">
        <GenerationForm @submit="handleGenerate" />
      </div>

      <!-- 流程面板（生成中 + 完成） -->
      <div class="main-panel" v-if="showProgress">
        <ProgressPanel
          :percent="sse.state.value.percent"
          :content="sse.state.value.content"
          :images="sse.state.value.images"
          :full-content="sse.state.value.fullContent"
          :is-completed="sse.state.value.isCompleted"
          :error="sse.state.value.error"
          :platform="currentPlatform"
          @view-detail="viewDetail"
          @copy="copyContent"
          @regenerate="reset"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import GenerationForm from '../components/generator/GenerationForm.vue'
import ProgressPanel from '../components/generator/ProgressPanel.vue'
import { useSSE } from '../composables/useSSE'
import { articleApi } from '../api/article'

const router = useRouter()
const sse = useSSE()
const showProgress = ref(false)
const currentArticleId = ref('')
const currentPlatform = ref('article')

async function handleGenerate(params: any) {
  try {
    showProgress.value = true
    currentPlatform.value = params.platform || 'article'
    sse.state.value = {
      stage: '', percent: 0, title: '', content: '',
      outline: [], images: [], fullContent: '', isCompleted: false, error: '',
    }
    const result = await articleApi.generate(params)
    currentArticleId.value = result.articleId
    sse.connect(result.articleId)
  } catch (e: any) {
    message.error(e.message || '生成失败')
    showProgress.value = false
  }
}

function viewDetail() {
  if (currentArticleId.value) {
    router.push(`/article/${currentArticleId.value}`)
  }
}

function copyContent() {
  const text = sse.state.value.fullContent || sse.state.value.content
  navigator.clipboard.writeText(text).then(() => {
    message.success('已复制到剪贴板')
  })
}

function reset() {
  sse.disconnect()
  sse.state.value = {
    stage: '', percent: 0, title: '', content: '',
    outline: [], images: [], fullContent: '', isCompleted: false, error: '',
  }
  showProgress.value = false
}
</script>

<style scoped>
.generator-page {
  width: 100%;
}

.page-header {
  background: var(--gradient-hero);
  padding: 32px 20px;
  margin-bottom: 24px;
}

.header-container {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 6px;
  letter-spacing: -0.5px;
  color: var(--color-text);
}

.page-subtitle {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
}

.generator-layout {
  max-width: 900px;
  margin: 0 auto;
  padding: 0 20px 40px;
}
</style>
