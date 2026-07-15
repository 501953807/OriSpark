import { defineStore } from 'pinia'
import { ref } from 'vue'
import { systemApi } from '@/api/system'

export const useSettingsStore = defineStore('settings', () => {
  const settings = ref<Record<string, string>>({})
  const storageInfo = ref<{ total: number; used: number; files: number; breakdown?: Record<string, number>; free_space?: number; total_space?: number } | null>(null)
  const auditLogs = ref<Array<{ id: string; action: string; user_id: string; created_at: string }>>([])

  async function fetchSettings() {
    try {
      const res = await systemApi.settings()
      settings.value = res.data.data
    } catch (e) {
      console.error('fetchSettings failed:', e)
    }
  }

  async function updateSettings(data: Record<string, string>) {
    try {
      await systemApi.updateSettings(data)
      await fetchSettings()
    } catch (e) {
      console.error('updateSettings failed:', e)
      throw e
    }
  }

  async function fetchStorage() {
    try {
      const res = await systemApi.storage()
      storageInfo.value = res.data.data
    } catch (e) {
      console.error('fetchStorage failed:', e)
    }
  }

  async function createBackup(includeFiles: boolean = true) {
    try {
      const res = await systemApi.backup(includeFiles)
      return res.data.data
    } catch (e) {
      console.error('createBackup failed:', e)
      throw e
    }
  }

  async function fetchAuditLogs(params?: Record<string, string>) {
    try {
      const res = await systemApi.auditLogs(params)
      auditLogs.value = res.data.data.items
    } catch (e) {
      console.error('fetchAuditLogs failed:', e)
    }
  }

  return {
    settings,
    storageInfo,
    auditLogs,
    fetchSettings,
    updateSettings,
    fetchStorage,
    createBackup,
    fetchAuditLogs,
  }
})
