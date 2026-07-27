<template>
  <div class="history-page">
    <div class="page-header">
      <div class="header-container">
        <div>
          <h1 class="page-title">创作历史</h1>
          <p class="page-subtitle">查看和管理你所有的创作记录</p>
        </div>
      </div>
    </div>

    <div class="container">
      <template v-if="!loading && articles.length === 0">
        <div class="empty-state">
          <div class="empty-icon">
            <FileTextOutlined />
          </div>
          <p class="empty-title">还没有创作记录</p>
          <p class="empty-desc">去创作工作台，让 AI 帮你写出第一篇爆款文章</p>
          <router-link to="/generator">
            <a-button type="primary" size="large">开始创作</a-button>
          </router-link>
        </div>
      </template>

      <a-card v-else class="table-card">
        <a-table
          :columns="columns"
          :data-source="articles"
          :loading="loading"
          row-key="id"
          :pagination="pagination"
          @change="onPageChange"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'title'">
              <router-link :to="`/article/${record.id}`" class="title-link">
                {{ record.title || record.topic }}
              </router-link>
            </template>
            <template v-if="column.key === 'platform'">
              <a-tag v-if="record.platform === 'xiaohongshu'" color="#ff2442">小红书</a-tag>
              <a-tag v-else color="green">爆款长文</a-tag>
            </template>
            <template v-if="column.key === 'status'">
              <a-tag v-if="record.status === 'completed'" color="green">已完成</a-tag>
              <a-tag v-else-if="record.status === 'generating'" color="blue">生成中</a-tag>
              <a-tag v-else-if="record.status === 'failed'" color="red">失败</a-tag>
              <a-tag v-else>{{ record.status }}</a-tag>
            </template>
            <template v-if="column.key === 'created_at'">
              {{ formatDate(record.created_at) }}
            </template>
            <template v-if="column.key === 'actions'">
              <a-space>
                <router-link :to="`/article/${record.id}`">
                  <a-button size="small">查看</a-button>
                </router-link>
                <a-popconfirm title="确定删除？" @confirm="handleDelete(record.id)">
                  <a-button size="small" danger>删除</a-button>
                </a-popconfirm>
              </a-space>
            </template>
          </template>
        </a-table>
      </a-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { FileTextOutlined } from '@ant-design/icons-vue'
import { articleApi } from '../api/article'

const loading = ref(false)
const articles = ref<any[]>([])
const pagination = reactive({ current: 1, pageSize: 10, total: 0 })

const columns = [
  { title: '标题', key: 'title', dataIndex: 'title' },
  { title: '平台', key: 'platform', dataIndex: 'platform', width: 110 },
  { title: '风格', dataIndex: 'style', width: 100 },
  { title: '状态', key: 'status', dataIndex: 'status', width: 100 },
  { title: '创建时间', key: 'created_at', dataIndex: 'created_at', width: 180 },
  { title: '操作', key: 'actions', width: 150 },
]

async function fetchList() {
  loading.value = true
  try {
    const res = await articleApi.list(pagination.current, pagination.pageSize)
    articles.value = res.records
    pagination.total = res.total
  } finally {
    loading.value = false
  }
}

async function handleDelete(id: string) {
  await articleApi.delete(id)
  message.success('删除成功')
  fetchList()
}

function onPageChange(pag: any) {
  pagination.current = pag.current
  fetchList()
}

function formatDate(d: string) {
  return d ? new Date(d).toLocaleString('zh-CN') : ''
}

onMounted(() => fetchList())
</script>

<style scoped>
.history-page {
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

.container {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 20px 40px;
}

.table-card {
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
}

.table-card :deep(.ant-card-body) {
  padding: 0;
}

.title-link {
  color: var(--color-text);
  font-weight: 500;
}

.title-link:hover {
  color: var(--color-primary);
}

.empty-state {
  padding: 80px 20px;
  text-align: center;
}

.empty-icon {
  margin-bottom: 16px;
}

.empty-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 8px;
}

.empty-desc {
  font-size: 14px;
  color: var(--color-text-muted);
  margin: 0 0 24px;
}
</style>
