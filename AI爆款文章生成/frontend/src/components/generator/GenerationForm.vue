<template>
  <a-card class="generate-card">
    <!-- 平台 Tab -->
    <a-tabs v-model:activeKey="platform" size="large" style="margin-bottom: 8px;">
      <a-tab-pane key="article">
        <template #tab><FileTextOutlined /> 爆款长文</template>
      </a-tab-pane>
      <a-tab-pane key="xiaohongshu">
        <template #tab><PictureOutlined /> 小红书笔记</template>
      </a-tab-pane>
    </a-tabs>

    <a-form layout="vertical" :model="form" @finish="handleSubmit">
      <!-- 选题 -->
      <a-form-item :label="platform === 'xiaohongshu' ? '笔记主题' : '选题'" required>
        <a-input
          v-model:value="form.topic"
          :placeholder="platform === 'xiaohongshu'
            ? '例如：早八通勤妆5分钟搞定、被问爆了的AI神器推荐…'
            : '例如：2025年AI编程工具盘点、职场人如何做好时间管理…'"
          size="large"
          :maxlength="200"
        />
      </a-form-item>

      <!-- 小红书专属字段 -->
      <template v-if="platform === 'xiaohongshu'">
        <a-row :gutter="16">
          <a-col :span="8">
            <a-form-item label="内容赛道">
              <a-select v-model:value="form.xhsCategory" size="large" placeholder="选择赛道">
                <a-select-option value="">智能匹配</a-select-option>
                <a-select-option value="美妆护肤">美妆护肤</a-select-option>
                <a-select-option value="穿搭时尚">穿搭时尚</a-select-option>
                <a-select-option value="美食探店">美食探店</a-select-option>
                <a-select-option value="旅行攻略">旅行攻略</a-select-option>
                <a-select-option value="职场成长">职场成长</a-select-option>
                <a-select-option value="情感治愈">情感治愈</a-select-option>
                <a-select-option value="知识干货">知识干货</a-select-option>
                <a-select-option value="生活方式">生活方式</a-select-option>
                <a-select-option value="数码好物">数码好物</a-select-option>
                <a-select-option value="母婴育儿">母婴育儿</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="人设定位">
              <a-input
                v-model:value="form.xhsPersona"
                placeholder="如：95后打工人、护肤成分党…"
                size="large"
                :maxlength="50"
              />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="配图风格">
              <a-select v-model:value="form.xhsImageStyle" size="large" placeholder="选择风格">
                <a-select-option value="bold">多巴胺大胆风</a-select-option>
                <a-select-option value="cute">治愈可爱风</a-select-option>
                <a-select-option value="minimalist">极简留白风</a-select-option>
                <a-select-option value="cyberpunk">赛博朋克风</a-select-option>
                <a-select-option value="chinese-elegance">新中式国风</a-select-option>
                <a-select-option value="clay-3d">3D黏土盲盒风</a-select-option>
                <a-select-option value="dark">暗黑美学风</a-select-option>
                <a-select-option value="dreamcore">梦核怀旧风</a-select-option>
                <a-select-option value="retro-anime">AI旧漫风</a-select-option>
                <a-select-option value="retro-hongkong">复古港风</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
      </template>

      <!-- 长文专属字段 -->
      <template v-if="platform === 'article'">
        <a-row :gutter="16">
          <a-col :span="8">
            <a-form-item label="写作风格">
              <a-select v-model:value="form.style" size="large">
                <a-select-option value="">智能匹配</a-select-option>
                <a-select-option value="tech">科技专业</a-select-option>
                <a-select-option value="emotional">情感故事</a-select-option>
                <a-select-option value="educational">教育科普</a-select-option>
                <a-select-option value="humorous">轻松幽默</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="目标字数">
              <a-slider v-model:value="form.wordCount" :min="800" :max="5000" :step="200" />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="配图偏好">
              <a-select v-model:value="form.imagePreference" size="large">
                <a-select-option value="smart">智能混合（推荐）</a-select-option>
                <a-select-option value="free_only">仅免费图源</a-select-option>
                <a-select-option value="all_ai" :disabled="!isVip">全 AI 生图（VIP）</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
      </template>

      <!-- 产品信息 -->
      <a-collapse v-model:activeKey="productPanelActive" style="margin-bottom: 16px;" :bordered="false">
        <a-collapse-panel key="product" header="填写产品信息（可选，防止 AI 瞎编数据）">
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="产品名称">
                <a-input v-model:value="form.productName" placeholder="如：兰蔻持妆粉底液 PO-01" :maxlength="100" />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="产品规格 / 卖点">
                <a-input v-model:value="form.productDescription" placeholder="如：SPF50+ PA++++，适合混油皮，30ml，450元" :maxlength="200" />
              </a-form-item>
            </a-col>
          </a-row>
        </a-collapse-panel>
      </a-collapse>

      <a-form-item>
        <a-button
          type="primary"
          html-type="submit"
          size="large"
          block
          class="submit-btn"
          :loading="loading"
          :disabled="!form.topic.trim()"
        >
          {{ loading ? '正在准备...' : (platform === 'xiaohongshu' ? '一键生成笔记' : '一键生成') }}
        </a-button>
      </a-form-item>
    </a-form>
  </a-card>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { FileTextOutlined, PictureOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '../../stores/auth'

const emit = defineEmits<{ submit: [params: any] }>()

const auth = useAuthStore()
const isVip = auth.isVip
const loading = ref(false)
const platform = ref('article')
const productPanelActive = ref<string[]>([])

const form = reactive({
  topic: '',
  style: '',
  wordCount: 2000,
  imagePreference: 'smart',
  xhsCategory: '',
  xhsPersona: '',
  xhsImageStyle: 'bold',
  productName: '',
  productDescription: '',
})

function handleSubmit() {
  loading.value = true
  emit('submit', {
    ...form,
    platform: platform.value,
  })
}
</script>

<style scoped>
.generate-card {
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
}

.submit-btn {
  height: 48px !important;
  font-size: 16px !important;
  font-weight: 600 !important;
  border-radius: var(--radius-lg) !important;
}
</style>
