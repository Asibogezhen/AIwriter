import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '../api/auth'

interface UserInfo {
  id: string
  email: string
  nickname: string
  isVip: boolean
  freeQuota: number
  isAdmin: boolean
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref<UserInfo | null>(JSON.parse(localStorage.getItem('user') || 'null'))

  const isLoggedIn = computed(() => !!token.value)
  const isVip = computed(() => user.value?.isVip ?? false)

  async function login(email: string, password: string) {
    const res = await authApi.login(email, password)
    token.value = res.token
    user.value = res.user
    localStorage.setItem('token', res.token)
    localStorage.setItem('user', JSON.stringify(res.user))
  }

  async function register(email: string, password: string, nickname: string) {
    const res = await authApi.register(email, password, nickname)
    token.value = res.token
    user.value = res.user
    localStorage.setItem('token', res.token)
    localStorage.setItem('user', JSON.stringify(res.user))
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    window.location.href = '/'
  }

  async function refreshUser() {
    try {
      const res = await authApi.me()
      user.value = res
      localStorage.setItem('user', JSON.stringify(res))
    } catch {
      logout()
    }
  }

  return { token, user, isLoggedIn, isVip, login, register, logout, refreshUser }
})
