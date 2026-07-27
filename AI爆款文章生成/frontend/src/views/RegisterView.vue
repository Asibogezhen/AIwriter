<template>
  <div class="auth-page">
    <div class="page-header">
      <div class="header-container">
        <div>
          <h1 class="page-title">注册</h1>
          <p class="page-subtitle">创建账号，开始 AI 驱动的内容创作</p>
        </div>
      </div>
    </div>

    <div class="auth-container">
      <a-card class="auth-card">
        <a-form :model="form" @finish="handleRegister" layout="vertical">
          <a-form-item name="nickname" :rules="[{ required: true, message: '请输入昵称' }]">
            <a-input v-model:value="form.nickname" placeholder="给自己取个名字" size="large" />
          </a-form-item>
          <a-form-item name="email" :rules="[{ required: true, type: 'email', message: '请输入有效邮箱' }]">
            <a-input v-model:value="form.email" placeholder="输入邮箱地址" size="large" />
          </a-form-item>
          <a-form-item name="password" :rules="[{ required: true, min: 6, message: '密码至少 6 位' }]">
            <a-input-password v-model:value="form.password" placeholder="设置密码（至少 6 位）" size="large" />
          </a-form-item>
          <a-form-item>
            <a-button type="primary" html-type="submit" block size="large" :loading="loading" class="submit-btn">注册</a-button>
          </a-form-item>
          <div class="auth-footer">
            已有账号？<router-link to="/login">立即登录</router-link>
          </div>
        </a-form>
      </a-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const form = reactive({ email: '', password: '', nickname: '' })

async function handleRegister() {
  loading.value = true
  try {
    await auth.register(form.email, form.password, form.nickname)
    message.success('注册成功！新用户赠送 1 次免费生成')
    router.push('/generator')
  } catch {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  width: 100%;
  min-height: calc(100vh - 64px - 57px);
}

.page-header {
  background: var(--gradient-hero);
  padding: 40px 20px;
  margin-bottom: 24px;
  text-align: center;
}

.header-container {
  max-width: 1200px;
  margin: 0 auto;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 6px;
  color: var(--color-text);
}

.page-subtitle {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
}

.auth-container {
  max-width: 420px;
  margin: 0 auto;
  padding: 0 20px 60px;
}

.auth-card {
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-md);
}

.submit-btn {
  height: 48px !important;
  font-size: 16px !important;
  font-weight: 600 !important;
  border-radius: var(--radius-lg) !important;
}

.auth-footer {
  text-align: center;
  font-size: 14px;
  color: var(--color-text-secondary);
}

.auth-footer a {
  color: var(--color-primary);
  font-weight: 500;
}

.auth-footer a:hover {
  color: var(--color-primary-dark);
}
</style>
