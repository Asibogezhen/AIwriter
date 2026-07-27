<template>
  <div class="article-detail-page">
    <div class="page-header">
      <div class="header-container">
        <div>
          <a-button class="back-btn" @click="$router.back()">← 返回</a-button>
        </div>
      </div>
    </div>

    <div class="container">
      <a-spin :spinning="loading">
        <div v-if="article" class="article-card">
          <h1 class="article-title">{{ article.title || article.topic }}</h1>
          <div class="article-meta">
            <span>创建于 {{ formatDate(article.created_at) }}</span>
            <span class="meta-divider">·</span>
            <span>字数 {{ article.word_count || 0 }}</span>
            <span v-if="article.platform" class="meta-divider">·</span>
            <a-tag v-if="article.platform === 'xiaohongshu'" color="#ff2442">小红书</a-tag>
            <a-tag v-else-if="article.platform" color="green">爆款长文</a-tag>
          </div>
          <div class="article-body">
            <MarkdownRender :content="article.rendered_html || article.markdown" />
          </div>
        </div>
      </a-spin>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { articleApi } from '../api/article'
import MarkdownRender from '../components/common/MarkdownRender.vue'

const route = useRoute()
const loading = ref(false)
const article = ref<any>(null)

function formatDate(d: string) {
  return d ? new Date(d).toLocaleString('zh-CN') : ''
}

onMounted(async () => {
  loading.value = true
  try {
    article.value = await articleApi.detail(route.params.id as string)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.article-detail-page {
  width: 100%;
}

.page-header {
  background: var(--gradient-hero);
  padding: 20px;
  margin-bottom: 24px;
}

.header-container {
  max-width: 820px;
  margin: 0 auto;
}

.back-btn {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.back-btn:hover {
  color: var(--color-primary);
}

.container {
  max-width: 820px;
  margin: 0 auto;
  padding: 0 20px 60px;
}

.article-card {
  background: white;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  padding: 32px 36px;
  box-shadow: var(--shadow-sm);
}

.article-title {
  font-size: 30px;
  font-weight: 700;
  margin: 0 0 12px;
  color: var(--color-text);
  letter-spacing: -0.5px;
  line-height: 1.3;
}

.article-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--color-text-muted);
  margin-bottom: 28px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--color-border);
  flex-wrap: wrap;
}

.meta-divider {
  color: var(--color-border);
}

.article-body {
  color: var(--color-text);
  line-height: 1.8;
  font-size: 16px;
}
</style>
