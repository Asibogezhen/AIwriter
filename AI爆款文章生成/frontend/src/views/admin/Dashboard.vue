<template>
  <div class="admin-page">
    <div class="page-header">
      <div class="header-container">
        <div>
          <h1 class="page-title">管理后台</h1>
          <p class="page-subtitle">数据概览与系统管理</p>
        </div>
        <router-link to="/admin/codes">
          <a-button type="primary" size="large">兑换码管理</a-button>
        </router-link>
      </div>
    </div>

    <div class="container">
      <div class="stats-grid">
        <div class="stat-card" v-for="s in statCards" :key="s.label">
          <div class="stat-icon" :style="{ background: s.bg, color: s.color }">
            <component :is="s.icon" />
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ s.value }}</div>
            <div class="stat-label">{{ s.label }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, computed, onMounted } from 'vue'
import { UserOutlined, FileTextOutlined, CrownOutlined, CheckCircleOutlined } from '@ant-design/icons-vue'
import { adminApi } from '../../api/vip'

const stats = reactive({ totalUsers: 0, totalArticles: 0, vipUsers: 0, completedArticles: 0 })

const statCards = computed(() => [
  { label: '总用户数', value: stats.totalUsers, icon: UserOutlined, color: '#22C55E', bg: 'rgba(34,197,94,0.1)' },
  { label: '总文章数', value: stats.totalArticles, icon: FileTextOutlined, color: '#3B82F6', bg: 'rgba(59,130,246,0.1)' },
  { label: 'VIP 用户', value: stats.vipUsers, icon: CrownOutlined, color: '#F59E0B', bg: 'rgba(245,158,11,0.1)' },
  { label: '已完成文章', value: stats.completedArticles, icon: CheckCircleOutlined, color: '#8B5CF6', bg: 'rgba(139,92,246,0.1)' },
])

onMounted(async () => {
  const res = await adminApi.stats()
  Object.assign(stats, res)
})
</script>

<style scoped>
.admin-page {
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

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px 40px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.stat-card {
  background: white;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all var(--transition-normal);
}

.stat-card:hover {
  border-color: var(--color-primary-light);
  box-shadow: var(--shadow-card-hover);
  transform: translateY(-2px);
}

.stat-icon {
  width: 52px;
  height: 52px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  flex-shrink: 0;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text);
  font-family: 'Outfit', sans-serif;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: var(--color-text-muted);
  margin-top: 4px;
}

@media (max-width: 992px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .header-container {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
