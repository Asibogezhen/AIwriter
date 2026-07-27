<template>
  <div class="markdown-body" v-html="renderedHtml" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'

const props = defineProps<{ content: string }>()

const renderedHtml = computed(() => {
  if (!props.content) return ''
  return marked(props.content, { breaks: true, gfm: true }) as string
})
</script>

<style scoped>
.markdown-body {
  line-height: 1.8;
  font-size: 15px;
  color: #333;
}
.markdown-body :deep(h1) { font-size: 24px; margin: 20px 0 12px; }
.markdown-body :deep(h2) { font-size: 20px; margin: 18px 0 10px; border-bottom: 1px solid #eee; padding-bottom: 6px; }
.markdown-body :deep(h3) { font-size: 17px; margin: 14px 0 8px; }
.markdown-body :deep(p) { margin: 8px 0; }
.markdown-body :deep(ul), .markdown-body :deep(ol) { padding-left: 24px; margin: 8px 0; }
.markdown-body :deep(li) { margin: 4px 0; }
.markdown-body :deep(blockquote) {
  border-left: 3px solid #1677ff;
  padding: 4px 12px;
  margin: 12px 0;
  background: #f6f8fa;
  color: #555;
}
.markdown-body :deep(code) {
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 13px;
}
.markdown-body :deep(pre code) {
  display: block;
  padding: 12px;
  overflow-x: auto;
  background: #282c34;
  color: #abb2bf;
}
.markdown-body :deep(img) { max-width: 100%; border-radius: 8px; margin: 12px 0; }
.markdown-body :deep(strong) { font-weight: 600; color: #1a1a1a; }
</style>
