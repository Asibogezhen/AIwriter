<template>
  <div class="vip-page">
    <div class="page-header">
      <div class="header-container">
        <h1 class="page-title">升级 VIP</h1>
        <p class="page-subtitle">¥199 永久买断，解锁全部功能</p>
      </div>
    </div>

    <div class="container">
      <!-- 已是 VIP -->
      <template v-if="isVip">
        <div class="vip-active-card">
          <div class="vip-crown"><CrownOutlined /></div>
          <h2 class="vip-active-title">你已是终身 VIP</h2>
          <p class="vip-active-desc">无限创作、AI 生图，全部权益永久享用</p>
          <RouterLink to="/generator">
            <a-button type="primary" size="large">开始创作</a-button>
          </RouterLink>
        </div>
      </template>

      <!-- 购买卡片 -->
      <template v-else>
        <div class="buy-card">
          <div class="buy-card-top">
            <h2 class="buy-title">永久会员</h2>
            <p class="buy-subtitle">一次付费，终身使用</p>
            <div class="buy-price">
              <span class="price-symbol">¥</span>
              <span class="price-value">199</span>
            </div>
          </div>

          <ul class="buy-perks">
            <li v-for="p in perks" :key="p">
              <CheckOutlined class="perk-icon" /> {{ p }}
            </li>
          </ul>

          <a-button
            type="primary"
            size="large"
            block
            class="buy-btn"
            :loading="buying"
            @click="handleBuy"
          >
            {{ buying ? '处理中...' : '立即购买' }}
          </a-button>
        </div>

        <!-- 兑换码 -->
        <div class="redeem-section">
          <a-collapse :bordered="false">
            <a-collapse-panel key="redeem" header="已有兑换码？点击这里兑换">
              <a-input-search
                v-model:value="code"
                placeholder="输入兑换码，例如：VIP-XXXX-XXXX-XXXX"
                enter-button="兑换 VIP"
                size="large"
                :loading="redeeming"
                @search="handleRedeem"
              />
            </a-collapse-panel>
          </a-collapse>
        </div>
      </template>
    </div>

    <!-- 支付弹窗 -->
    <a-modal
      v-model:open="showPayModal"
      :title="null"
      :footer="null"
      :closable="!paying"
      :maskClosable="!paying"
      width="420px"
      centered
      @cancel="cancelPay"
    >
      <div class="pay-modal">
        <h3 class="pay-modal-title">扫码支付</h3>
        <div class="pay-amount">¥199.00</div>

        <!-- 支付方式 Tab -->
        <div class="pay-tabs">
          <div
            :class="['pay-tab', { active: payMethod === 'alipay' }]"
            @click="payMethod = 'alipay'"
          >
            <span class="pay-tab-icon alipay-icon">支</span>
            支付宝
          </div>
          <div
            :class="['pay-tab', { active: payMethod === 'wechat' }]"
            @click="payMethod = 'wechat'"
          >
            <span class="pay-tab-icon wechat-icon">微</span>
            微信支付
          </div>
        </div>

        <!-- 二维码 -->
        <div class="qr-box">
          <div class="qr-code">
            <!-- 模拟二维码图案 -->
            <div class="qr-pattern">
              <div class="qr-corners">
                <span class="qr-corner tl" /><span class="qr-corner tr" />
                <span class="qr-corner bl" /><span class="qr-corner br" />
              </div>
              <div class="qr-center">
                <span class="qr-center-icon" :style="{ background: payMethod === 'alipay' ? '#1677FF' : '#07C160' }">
                  {{ payMethod === 'alipay' ? '支' : '微' }}
                </span>
              </div>
              <div class="qr-dots">
                <span v-for="i in 49" :key="i" :class="['qr-dot', `d-${i % 13}`]" />
              </div>
            </div>
          </div>
          <p class="qr-hint">
            <template v-if="payMethod === 'alipay'">请使用支付宝扫一扫</template>
            <template v-else>请使用微信扫一扫</template>
          </p>
        </div>

        <a-button
          type="primary"
          size="large"
          block
          :loading="paying"
          class="pay-btn"
          @click="handlePay"
        >
          {{ paying ? '验证中...' : '已完成支付' }}
        </a-button>
        <p class="pay-safe">模拟支付环境，点击按钮即完成支付</p>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { CrownOutlined, CheckOutlined } from '@ant-design/icons-vue'
import { vipApi } from '../api/vip'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const isVip = ref(false)
const freeQuota = ref(0)
const code = ref('')
const redeeming = ref(false)
const buying = ref(false)
const paying = ref(false)
const showPayModal = ref(false)
const payMethod = ref('alipay')
const currentOrderNo = ref('')

const perks = [
  '不限次数文章生成',
  'AI 智能生图 (Qwen-Image2)',
  '全部写作风格自由选择',
  '优先体验新功能',
  '永久有效，无需续费',
]

async function fetchStatus() {
  const res = await vipApi.status().catch(() => null)
  if (res) {
    isVip.value = res.isVip
    freeQuota.value = res.freeQuota
  }
}

async function handleBuy() {
  buying.value = true
  try {
    const order = await vipApi.createOrder('lifetime')
    currentOrderNo.value = order.orderNo
    showPayModal.value = true
  } catch {
    // handled by interceptor
  } finally {
    buying.value = false
  }
}

async function handlePay() {
  if (!currentOrderNo.value) return
  paying.value = true
  try {
    await vipApi.payOrder(currentOrderNo.value)
    message.success('支付成功！你已成为终身 VIP')
    showPayModal.value = false
    currentOrderNo.value = ''
    await auth.refreshUser()
    await fetchStatus()
  } catch {
    // handled by interceptor
  } finally {
    paying.value = false
  }
}

function cancelPay() {
  showPayModal.value = false
  currentOrderNo.value = ''
}

async function handleRedeem() {
  if (!code.value.trim()) return
  redeeming.value = true
  try {
    await vipApi.redeem(code.value.trim())
    message.success('兑换成功！你已成为终身 VIP')
    code.value = ''
    await auth.refreshUser()
    await fetchStatus()
  } catch {
    // handled by interceptor
  } finally {
    redeeming.value = false
  }
}

onMounted(() => fetchStatus())
</script>

<style scoped>
.vip-page {
  width: 100%;
  min-height: calc(100vh - 64px - 57px);
}

.page-header {
  background: var(--gradient-hero-warm);
  padding: 48px 20px;
  margin-bottom: 24px;
  text-align: center;
}

.header-container {
  max-width: 1200px;
  margin: 0 auto;
}

.page-title {
  font-size: 32px;
  font-weight: 700;
  margin: 0 0 8px;
  color: var(--color-text);
  letter-spacing: -0.5px;
}

.page-subtitle {
  font-size: 15px;
  color: var(--color-text-secondary);
  margin: 0;
}

.container {
  max-width: 440px;
  margin: 0 auto;
  padding: 0 20px 60px;
}

/* 已是 VIP */
.vip-active-card {
  text-align: center;
  padding: 60px 20px;
  background: white;
  border-radius: var(--radius-xl);
  border: 2px solid var(--color-gold-light);
  box-shadow: var(--shadow-md);
}

.vip-crown {
  font-size: 48px;
  color: var(--color-gold);
  margin-bottom: 16px;
}

.vip-active-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text);
  margin: 0 0 8px;
}

.vip-active-desc {
  font-size: 15px;
  color: var(--color-text-secondary);
  margin: 0 0 24px;
}

/* 购买卡片 */
.buy-card {
  background: white;
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-border);
  padding: 40px 32px 32px;
  box-shadow: var(--shadow-md);
  text-align: center;
}

.buy-card-top {
  margin-bottom: 28px;
}

.buy-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--color-text);
  margin: 0 0 6px;
}

.buy-subtitle {
  font-size: 14px;
  color: var(--color-text-muted);
  margin: 0 0 24px;
}

.buy-price {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 2px;
}

.price-symbol {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text);
}

.price-value {
  font-size: 56px;
  font-weight: 700;
  font-family: 'Outfit', sans-serif;
  line-height: 1;
  background: linear-gradient(135deg, var(--color-primary-dark), var(--color-primary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.buy-perks {
  list-style: none;
  padding: 0;
  margin: 0 0 28px;
  text-align: left;
}

.buy-perks li {
  padding: 9px 0;
  font-size: 15px;
  color: var(--color-text-secondary);
  display: flex;
  align-items: center;
  gap: 10px;
}

.perk-icon {
  color: var(--color-primary);
  font-size: 16px;
  flex-shrink: 0;
}

.buy-btn {
  height: 52px !important;
  font-size: 17px !important;
  font-weight: 600 !important;
  border-radius: var(--radius-lg) !important;
}

/* 兑换码 */
.redeem-section {
  margin-top: 20px;
}

.redeem-section :deep(.ant-collapse) {
  background: white;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
}

.redeem-section :deep(.ant-collapse-item) {
  border: none;
}

/* ========== 支付弹窗 ========== */
.pay-modal {
  text-align: center;
  padding: 8px 0;
}

.pay-modal-title {
  font-size: 20px;
  font-weight: 700;
  margin: 0 0 4px;
  color: var(--color-text);
}

.pay-amount {
  font-size: 28px;
  font-weight: 700;
  font-family: 'Outfit', sans-serif;
  color: var(--color-primary);
  margin-bottom: 20px;
}

/* 支付方式 Tab */
.pay-tabs {
  display: flex;
  gap: 0;
  margin-bottom: 20px;
  border-radius: var(--radius-md);
  overflow: hidden;
  border: 1px solid var(--color-border);
}

.pay-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 0;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  color: var(--color-text-secondary);
  background: var(--color-background-secondary);
  transition: all var(--transition-fast);
}

.pay-tab.active {
  background: white;
  color: var(--color-text);
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}

.pay-tab-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 700;
  color: white;
}

.alipay-icon {
  background: #1677FF;
}

.wechat-icon {
  background: #07C160;
}

/* 二维码 */
.qr-box {
  margin-bottom: 20px;
}

.qr-code {
  display: flex;
  justify-content: center;
}

.qr-pattern {
  position: relative;
  width: 180px;
  height: 180px;
  background: white;
  border: 3px solid #e8e8e8;
  border-radius: 8px;
  padding: 12px;
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  grid-template-rows: repeat(7, 1fr);
  gap: 3px;
}

.qr-dots {
  position: absolute;
  inset: 20px;
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  grid-template-rows: repeat(7, 1fr);
  gap: 2px;
}

.qr-dot {
  background: #333;
  border-radius: 2px;
  opacity: 0;
}

.qr-dot.d-0, .qr-dot.d-3, .qr-dot.d-5, .qr-dot.d-7, .qr-dot.d-10 { opacity: 0.85; }
.qr-dot.d-1, .qr-dot.d-8 { opacity: 0.3; }
.qr-dot.d-2, .qr-dot.d-6, .qr-dot.d-11 { opacity: 0.9; }
.qr-dot.d-4, .qr-dot.d-9, .qr-dot.d-12 { opacity: 0.5; }

.qr-corners span {
  position: absolute;
  width: 20px;
  height: 20px;
  border: 3px solid #333;
  border-radius: 3px;
}

.qr-corner.tl { top: 4px; left: 4px; border-right: none; border-bottom: none; }
.qr-corner.tr { top: 4px; right: 4px; border-left: none; border-bottom: none; }
.qr-corner.bl { bottom: 4px; left: 4px; border-right: none; border-top: none; }
.qr-corner.br { bottom: 4px; right: 4px; border-left: none; border-top: none; }

.qr-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.qr-center-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 700;
  color: white;
}

.qr-hint {
  margin: 12px 0 0;
  font-size: 13px;
  color: var(--color-text-muted);
}

.pay-btn {
  height: 48px !important;
  font-size: 16px !important;
  font-weight: 600 !important;
  border-radius: var(--radius-lg) !important;
}

.pay-safe {
  margin: 12px 0 0;
  font-size: 12px;
  color: var(--color-text-muted);
}

@media (max-width: 768px) {
  .page-header {
    padding: 32px 20px;
  }

  .page-title {
    font-size: 24px;
  }

  .buy-card {
    padding: 32px 20px 24px;
  }

  .price-value {
    font-size: 48px;
  }
}
</style>
