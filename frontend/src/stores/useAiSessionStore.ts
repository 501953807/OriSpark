import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { AiSession } from '@/types/ai_session'
import { aiSessionApi } from '@/api/ai_session'

export const useAiSessionStore = defineStore('aiSession', () => {
  const sessions = ref<AiSession[]>([])
  const loading = ref(false)

  async function fetchByWork(workId: string) {
    loading.value = true
    try {
      const res = await aiSessionApi.list(workId)
      sessions.value = res.data.data
    } finally {
      loading.value = false
    }
  }

  async function create(workId: string, data: Record<string, unknown>) {
    const res = await aiSessionApi.create(workId, data as any)
    sessions.value.push({
      id: res.data.data.id,
      work_id: workId,
      tool_name: data.tool_name as string,
      prompt: data.prompt as string,
      created_at: new Date().toISOString(),
    })
  }

  async function remove(workId: string, sessionId: string) {
    await aiSessionApi.delete(workId, sessionId)
    sessions.value = sessions.value.filter(s => s.id !== sessionId)
  }

  return { sessions, loading, fetchByWork, create, remove }
})
