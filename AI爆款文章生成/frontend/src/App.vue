<template>
  <a-config-provider :theme="themeConfig">
    <a-layout class="app-layout">
      <AppHeader />
      <a-layout-content class="app-content">
        <router-view />
      </a-layout-content>
      <AppFooter />
    </a-layout>
  </a-config-provider>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'
import AppHeader from './components/layout/AppHeader.vue'
import AppFooter from './components/layout/AppFooter.vue'

const auth = useAuthStore()
onMounted(async () => {
  if (auth.isLoggedIn) {
    await auth.refreshUser()
  }
})

const themeConfig = {
  token: {
    colorPrimary: '#22C55E',
    borderRadius: 8,
    colorLink: '#22C55E',
  },
}
</script>

<style>
.app-layout { min-height: 100vh; background: var(--color-background); }
.app-content {
  padding: 0;
  max-width: 100%;
  margin: 0;
  width: 100%;
}
</style>
