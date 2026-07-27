import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: () => import('../views/HomeView.vue') },
    { path: '/login', name: 'login', component: () => import('../views/LoginView.vue') },
    { path: '/register', name: 'register', component: () => import('../views/RegisterView.vue') },
    { path: '/generator', name: 'generator', component: () => import('../views/GeneratorView.vue'), meta: { requiresAuth: true } },
    { path: '/history', name: 'history', component: () => import('../views/HistoryView.vue'), meta: { requiresAuth: true } },
    { path: '/article/:id', name: 'article-detail', component: () => import('../views/ArticleDetail.vue'), meta: { requiresAuth: true } },
    { path: '/vip', name: 'vip', component: () => import('../views/VipView.vue'), meta: { requiresAuth: true } },
    { path: '/admin', name: 'admin', component: () => import('../views/admin/Dashboard.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
    { path: '/admin/codes', name: 'admin-codes', component: () => import('../views/admin/RedeemCodes.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
  ],
})

export default router
