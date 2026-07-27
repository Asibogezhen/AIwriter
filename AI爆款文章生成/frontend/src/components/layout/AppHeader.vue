<template>
  <a-layout-header class="header">
    <div class="header-container">
      <div class="header-left">
        <RouterLink to="/" class="logo-link">
          <span class="logo-dot" />
          <span class="logo-text">墨笔</span>
        </RouterLink>
      </div>

      <nav class="nav-center">
        <RouterLink to="/" :class="['nav-item', { active: route.path === '/' }]">
          <HomeOutlined class="nav-icon" />
          <span>首页</span>
        </RouterLink>
        <RouterLink to="/generator" :class="['nav-item', { active: route.path === '/generator' }]">
          <EditOutlined class="nav-icon" />
          <span>创作</span>
        </RouterLink>
        <RouterLink to="/history" :class="['nav-item', { active: route.path === '/history' }]">
          <UnorderedListOutlined class="nav-icon" />
          <span>历史</span>
        </RouterLink>
      </nav>

      <div class="header-right">
        <template v-if="auth.isLoggedIn">
          <RouterLink v-if="!auth.isVip" to="/vip" class="upgrade-vip-btn">
            <CrownOutlined />
            <span>升级 VIP</span>
          </RouterLink>
          <RouterLink v-else to="/vip" class="vip-badge">
            <CrownOutlined />
            <span>VIP</span>
          </RouterLink>

          <a-dropdown>
            <a-space class="user-info">
              <a-avatar :size="34" class="user-avatar">
                {{ (auth.user?.nickname || auth.user?.email || '?')[0].toUpperCase() }}
              </a-avatar>
              <span class="user-name">{{ auth.user?.nickname || auth.user?.email }}</span>
              <DownOutlined class="user-arrow" />
            </a-space>
            <template #overlay>
              <a-menu>
                <a-menu-item key="quota">
                  <span class="quota-text">剩余额度：{{ auth.user?.freeQuota ?? 0 }} 次</span>
                </a-menu-item>
                <a-menu-item v-if="auth.user?.isAdmin" key="admin">
                  <RouterLink to="/admin">管理后台</RouterLink>
                </a-menu-item>
                <a-menu-divider />
                <a-menu-item key="logout" @click="auth.logout()">
                  <LogoutOutlined />
                  <span>退出登录</span>
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </template>
        <template v-else>
          <RouterLink to="/login" class="login-btn">登录</RouterLink>
        </template>
      </div>
    </div>
  </a-layout-header>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import {
  DownOutlined,
  HomeOutlined,
  EditOutlined,
  UnorderedListOutlined,
  CrownOutlined,
  LogoutOutlined,
} from '@ant-design/icons-vue'
import { useAuthStore } from '../../stores/auth'

const route = useRoute()
const auth = useAuthStore()
</script>

<style scoped>
.header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  padding: 0;
  height: 64px;
  line-height: 64px;
  border-bottom: 1px solid var(--color-border);
  transition: all var(--transition-normal);
}

.header-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
}

.header-left {
  display: flex;
  align-items: center;
}

.logo-link {
  display: flex;
  align-items: center;
  gap: 10px;
  transition: opacity var(--transition-fast);
}

.logo-link:hover {
  opacity: 0.85;
}

.logo-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--gradient-gold);
  box-shadow: 0 0 8px rgba(212, 168, 83, 0.4);
}

.logo-text {
  font-family: 'Outfit', sans-serif;
  font-size: 20px;
  font-weight: 700;
  color: var(--color-text);
  white-space: nowrap;
  letter-spacing: -0.3px;
}

.nav-center {
  display: flex;
  align-items: center;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
  transition: all var(--transition-fast);
  text-decoration: none;
  line-height: 1;
}

.nav-item:hover {
  color: var(--color-text);
  background: var(--color-background-secondary);
}

.nav-item.active {
  color: var(--color-primary-dark);
  background: rgba(34, 197, 94, 0.1);
}

.nav-icon {
  font-size: 16px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.upgrade-vip-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 500;
  color: var(--color-primary);
  text-decoration: none;
  transition: all var(--transition-fast);
}

.upgrade-vip-btn:hover {
  background: rgba(34, 197, 94, 0.08);
  color: var(--color-primary-dark);
}

.vip-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-primary);
  text-decoration: none;
}

.vip-badge:hover {
  color: var(--color-primary-dark);
}

.user-info {
  padding: 4px 12px;
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
  cursor: pointer;
}

.user-info:hover {
  background: var(--color-background-secondary);
}

.user-avatar {
  background: var(--color-primary);
  color: white;
  font-weight: 600;
}

.user-name {
  font-weight: 500;
  color: var(--color-text);
  font-size: 14px;
}

.user-arrow {
  font-size: 12px;
  color: var(--color-text-muted);
}

.quota-text {
  color: var(--color-text-secondary);
  font-size: 13px;
}

.login-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 38px;
  padding: 0 24px;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 600;
  color: white;
  background: var(--gradient-primary);
  border: none;
  box-shadow: var(--shadow-green);
  transition: all var(--transition-normal);
  text-decoration: none;
}

.login-btn:hover {
  color: white;
  box-shadow: 0 6px 20px rgba(34, 197, 94, 0.35);
}

@media (max-width: 768px) {
  .header-container {
    padding: 0 16px;
  }

  .logo-text {
    font-size: 16px;
  }

  .nav-item span {
    display: none;
  }

  .nav-item {
    padding: 8px 12px;
  }

  .user-name {
    display: none;
  }
}
</style>
