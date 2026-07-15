import { defineStore } from 'pinia'
import { ref } from 'vue'
import { illustratorApi } from '@/api/illustrator'
import type { AiSession, AiSessionCreateInput, ImportFolderResult } from '@/types/illustrator'

export const useIllustratorStore = defineStore('illustrator', () => {
  // ── State ────────────────────────────────────────────────────────

  const sessions = ref<AiSession[]>([])
  const currentWorkId = ref<string | null>(null)
  const loading = ref(false)
  const errorMsg = ref('')

  // ── Helpers ──────────────────────────────────────────────────────

  function setError(msg: string, e: unknown) {
    errorMsg.value = e instanceof Error ? e.message : msg
  }

  // ── AI Sessions ──────────────────────────────────────────────────

  async function fetchSessions(workId: string): Promise<AiSession[]> {
    loading.value = true
    errorMsg.value = ''
    currentWorkId.value = workId
    try {
      const res = await illustratorApi.getSessions(workId)
      sessions.value = res.data.data ?? []
      return sessions.value
    } catch (e: unknown) {
      setError('获取AI创作时间线失败', e)
      sessions.value = []
      return []
    } finally {
      loading.value = false
    }
  }

  async function createSession(
    workId: string,
    data: AiSessionCreateInput
  ): Promise<AiSession | null> {
    try {
      const res = await illustratorApi.createSession(workId, data)
      const item = res.data.data
      sessions.value = [item, ...sessions.value]
      return item
    } catch (e: unknown) {
      setError('记录AI创作会话失败', e)
      return null
    }
  }

  async function updateSession(
    workId: string,
    sessionId: string,
    data: Partial<AiSessionCreateInput>
  ): Promise<boolean> {
    try {
      await illustratorApi.updateSession(workId, sessionId, data)
      sessions.value = sessions.value.map((s) =>
        s.id === sessionId ? { ...s, ...data } : s
      )
      return true
    } catch (e: unknown) {
      setError('更新AI创作会话失败', e)
      return false
    }
  }

  async function deleteSession(workId: string, sessionId: string): Promise<boolean> {
    try {
      await illustratorApi.deleteSession(workId, sessionId)
      sessions.value = sessions.value.filter((s) => s.id !== sessionId)
      return true
    } catch (e: unknown) {
      setError('删除AI创作会话失败', e)
      return false
    }
  }

  // ── Folder Import ────────────────────────────────────────────────

  async function importFolder(formData: FormData): Promise<ImportFolderResult | null> {
    loading.value = true
    errorMsg.value = ''
    try {
      const res = await illustratorApi.importFolder(formData)
      return res.data.data ?? { imported: 0, skipped_duplicate: 0, failed: 0 }
    } catch (e: unknown) {
      setError('批量导入失败', e)
      return null
    } finally {
      loading.value = false
    }
  }

  // ── Bulk Load ────────────────────────────────────────────────────

  async function fetchAll() {
    loading.value = true
    errorMsg.value = ''
    try {
      // Currently only sessions are per-work, nothing global to load
    } catch (e: unknown) {
      setError('加载数据失败', e)
    } finally {
      loading.value = false
    }
  }

  return {
    // State
    sessions,
    currentWorkId,
    loading,
    errorMsg,
    // Actions
    fetchSessions,
    createSession,
    updateSession,
    deleteSession,
    importFolder,
    fetchAll,
  }
})
