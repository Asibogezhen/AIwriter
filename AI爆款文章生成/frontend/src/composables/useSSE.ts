import { ref, onUnmounted } from 'vue'

export interface SseState {
  stage: string
  percent: number
  title: string
  content: string
  outline: Array<{ section: number; title: string; points: string[] }>
  images: Array<{ position: number; url: string; method: string; sectionTitle: string }>
  fullContent: string
  isCompleted: boolean
  error: string
}

export function useSSE() {
  const state = ref<SseState>({
    stage: '',
    percent: 0,
    title: '',
    content: '',
    outline: [],
    images: [],
    fullContent: '',
    isCompleted: false,
    error: '',
  })

  let eventSource: EventSource | null = null

  function connect(articleId: string) {
    const url = `/api/v1/articles/generate/${articleId}/sse`
    eventSource = new EventSource(url)

    const handlers: Record<string, (data: any) => void> = {
      progress: (d) => {
        state.value.stage = d.stage || ''
        state.value.percent = d.percent || 0
      },
      content_chunk: (d) => {
        state.value.content += d.text || ''
      },
      content_done: () => {},
      image_gen_done: (d) => {
        state.value.images.push(d)
      },
      render_done: (d) => {
        state.value.fullContent = d.fullContent || ''
      },
      done: () => {
        state.value.isCompleted = true
        eventSource?.close()
      },
      error: (d) => {
        state.value.error = d.message || '生成失败'
        eventSource?.close()
      },
    }

    Object.entries(handlers).forEach(([event, handler]) => {
      eventSource!.addEventListener(event, (e) => {
        try {
          handler(JSON.parse(e.data))
        } catch {
          handler(e.data)
        }
      })
    })

    eventSource.onerror = () => {
      if (!state.value.isCompleted && !state.value.error) {
        state.value.error = '连接断开，请刷新重试'
      }
      eventSource?.close()
    }
  }

  function disconnect() {
    eventSource?.close()
    eventSource = null
  }

  onUnmounted(() => disconnect())

  return { state, connect, disconnect }
}
