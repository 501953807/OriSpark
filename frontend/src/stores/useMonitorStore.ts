import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { MonitorTask, MonitorResult } from '@/types/monitor'
import { monitorApi } from '@/api/monitor'

export const useMonitorStore = defineStore('monitor', () => {
  const tasks = ref<MonitorTask[]>([])
  const results = ref<MonitorResult[]>([])
  const loading = ref(false)
  const quota = ref<{ baidu: { used_today: number; daily_limit: number }; google: { used_this_month: number; monthly_limit: number } } | null>(null)

  async function fetchTasks(params?: { work_id?: string; status?: string }) {
    loading.value = true
    try {
      const res = await monitorApi.tasks(params)
      tasks.value = res.data.data
    } catch (e) {
      console.error('fetchTasks failed:', e)
    } finally {
      loading.value = false
    }
  }

  async function createTask(workId: string, platform: string = 'baidu', searchType: string = 'image') {
    try {
      const res = await monitorApi.createTask({
        work_id: workId,
        platform,
        search_type: searchType,
      })
      return res.data.data
    } catch (e) {
      console.error(`createTask(${workId}) failed:`, e)
      throw e
    }
  }

  async function triggerScan(taskId: string) {
    try {
      const res = await monitorApi.scan(taskId)
      await fetchResults()
      return res.data.data
    } catch (e) {
      console.error(`triggerScan(${taskId}) failed:`, e)
      throw e
    }
  }

  async function batchScan(workIds: string[], platform: string) {
    try {
      const res = await monitorApi.batchScan(workIds, platform)
      return res.data.data
    } catch (e) {
      console.error('batchScan failed:', e)
      throw e
    }
  }

  async function fetchResults(params?: { task_id?: string; status?: string }) {
    try {
      const res = await monitorApi.results(params)
      results.value = res.data.data
      return results.value
    } catch (e) {
      console.error('fetchResults failed:', e)
      throw e
    }
  }

  async function updateResult(id: string, data: Partial<MonitorResult>) {
    try {
      const res = await monitorApi.updateResult(id, data)
      return res.data.data
    } catch (e) {
      console.error(`updateResult(${id}) failed:`, e)
      throw e
    }
  }

  async function fetchQuota() {
    try {
      const res = await monitorApi.quota()
      quota.value = res.data.data
    } catch (e) {
      console.error('fetchQuota failed:', e)
    }
  }

  return {
    tasks,
    results,
    loading,
    quota,
    fetchTasks,
    createTask,
    triggerScan,
    batchScan,
    fetchResults,
    updateResult,
    fetchQuota,
  }
})
