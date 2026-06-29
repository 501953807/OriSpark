import { defineStore } from 'pinia'
import { ref } from 'vue'
import { systemApi } from '@/api/system'

export const useSettingsStore = defineStore('settings', () => {
  const settings = ref<Record<string, string>>({})
  const storageInfo = ref<any>(null)
  const auditLogs = ref<any[]>([])

  async function fetchSettings() {
    const res = await systemApi.settings()
    settings.value = res.data.data
  }

  async function updateSettings(data: Record<string, string>) {
    await systemApi.updateSettings(data)
    await fetchSettings()
  }

  async function fetchStorage() {
    const res = await systemApi.storage()
    storageInfo.value = res.data.data
  }

  async function createBackup(includeFiles: boolean = true) {
    const res = await systemApi.backup(includeFiles)
    return res.data.data
  }

  async function fetchAuditLogs(params?: any) {
    const res = await systemApi.auditLogs(params)
    auditLogs.value = res.data.data.items
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
