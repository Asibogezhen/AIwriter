<template>
  <div class="codes-page">
    <div class="page-header">
      <div class="header-container">
        <div>
          <h1 class="page-title">兑换码管理</h1>
          <p class="page-subtitle">批量生成与管理 VIP 兑换码</p>
        </div>
      </div>
    </div>

    <div class="container">
      <a-card class="section-card" title="批量生成兑换码">
        <a-form layout="inline" class="gen-form">
          <a-form-item label="数量">
            <a-input-number v-model:value="genCount" :min="1" :max="500" />
          </a-form-item>
          <a-form-item label="批次">
            <a-input v-model:value="genBatch" placeholder="如：202601第一批" />
          </a-form-item>
          <a-form-item label="备注">
            <a-input v-model:value="genNote" placeholder="代理商分发等" />
          </a-form-item>
          <a-form-item>
            <a-button type="primary" :loading="generating" @click="handleGenerate">生成兑换码</a-button>
          </a-form-item>
        </a-form>
        <div v-if="newCodes.length > 0" style="margin-top: 20px;">
          <a-alert type="success" message="生成成功" show-icon />
          <a-textarea :value="newCodes.join('\n')" :rows="6" readonly style="margin-top: 12px;" />
          <a-button size="small" style="margin-top: 8px;" @click="copyCodes">复制全部</a-button>
        </div>
      </a-card>

      <a-card class="section-card table-card" title="兑换码列表" style="margin-top: 16px;">
        <a-table
          :columns="columns"
          :data-source="codes"
          :loading="loading"
          row-key="code"
          :pagination="pagination"
          @change="onPageChange"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'is_used'">
              <a-tag v-if="record.is_used" color="red">已使用</a-tag>
              <a-tag v-else color="green">未使用</a-tag>
            </template>
            <template v-if="column.key === 'used_at'">
              {{ record.used_at ? new Date(record.used_at).toLocaleString('zh-CN') : '-' }}
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
import { adminApi } from '../../api/vip'

const generating = ref(false)
const genCount = ref(10)
const genBatch = ref('')
const genNote = ref('')
const newCodes = ref<string[]>([])

const codes = ref<any[]>([])
const loading = ref(false)
const pagination = reactive({ current: 1, pageSize: 20, total: 0 })

const columns = [
  { title: '兑换码', dataIndex: 'code' },
  { title: '状态', key: 'is_used', dataIndex: 'is_used', width: 100 },
  { title: '批次', dataIndex: 'batch', width: 150 },
  { title: '备注', dataIndex: 'note', width: 150 },
  { title: '使用时间', key: 'used_at', width: 180 },
]

async function handleGenerate() {
  generating.value = true
  try {
    const res = await adminApi.generateCodes(genCount.value, genBatch.value, genNote.value)
    newCodes.value = res.codes
    message.success(`已生成 ${res.count} 个兑换码`)
    fetchCodes()
  } finally {
    generating.value = false
  }
}

function copyCodes() {
  navigator.clipboard.writeText(newCodes.value.join('\n')).then(() => message.success('已复制'))
}

async function fetchCodes() {
  loading.value = true
  try {
    const res = await adminApi.listCodes(pagination.current, '')
    codes.value = res.records
    pagination.total = res.total
  } finally {
    loading.value = false
  }
}

function onPageChange(pag: any) {
  pagination.current = pag.current
  fetchCodes()
}

onMounted(() => fetchCodes())
</script>

<style scoped>
.codes-page {
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

.section-card {
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
}

.gen-form {
  flex-wrap: wrap;
  gap: 8px;
}

.table-card :deep(.ant-card-body) {
  padding: 0;
}
</style>
