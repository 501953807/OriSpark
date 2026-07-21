import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { NotaryRecord, NotaryPlatform } from '@/types/notary'
import { notaryApi } from '@/api/notary'

export const useNotaryStore = defineStore('notary', () => {
  const records = ref<NotaryRecord[]>([])
  const platforms = ref<NotaryPlatform[]>([])
  const loading = ref(false)

  async function fetchRecords(params?: { page?: number; status?: string; platform?: string }) {
    loading.value = true
    try {
      const res = await notaryApi.list(params)
      records.value = res.data.data.items
    } catch (e) {
      console.error('fetchRecords failed:', e)
    } finally {
      loading.value = false
    }
  }

  async function fetchPlatforms() {
    try {
      const res = await notaryApi.platforms()
      platforms.value = res.data.data
    } catch (e) {
      console.error('fetchPlatforms failed:', e)
    }
  }

  async function createRecord(workId: string, platform: string) {
    try {
      const res = await notaryApi.create({ work_id: workId, platform })
      return res.data.data
    } catch (e) {
      console.error(`createRecord(${workId}) failed:`, e)
      throw e
    }
  }

  async function confirmRecord(id: string, data?: Record<string, unknown>) {
    try {
      const res = await notaryApi.confirm(id, data)
      await fetchRecords()
      return res.data.data
    } catch (e) {
      console.error(`confirmRecord(${id}) failed:`, e)
      throw e
    }
  }

  async function batchNotarize(workIds: string[], platform: string) {
    try {
      const res = await notaryApi.batch(workIds, platform)
      return res.data.data
    } catch (e) {
      console.error('batchNotarize failed:', e)
      throw e
    }
  }

  return {
    records,
    platforms,
    loading,
    fetchRecords,
    fetchPlatforms,
    createRecord,
    confirmRecord,
    batchNotarize,
  }
})
