import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { MonitorTask, MonitorResult } from '@/types/monitor'
import { monitorApi } from '@/api/monitor'

export const useMonitorStore = defineStore('monitor', () => {
  const tasks = ref<MonitorTask[]>([])
  const results = ref<MonitorResult[]>([])
  const loading = ref(false)
  const quota = ref<any>(null)

  async function fetchTasks(params?: { work_id?: string; status?: string }) {
    loading.value = true
    try {
      const res = await monitorApi.tasks(params)
      tasks.value = res.data.data
    } finally {
      loading.value = false
    }
  }

  async function createTask(workId: string, platform: string = 'baidu', searchType: string = 'image') {
    const res = await monitorApi.createTask({
      work_id: workId,
      platform,
      search_type: searchType,
    })
    return res.data.data
  }

  async function triggerScan(taskId: string) {
    const res = await monitorApi.scan(taskId)
    await fetchResults()
    return res.data.data
  }

  async function batchScan(workIds: string[], platform: string) {
    const res = await monitorApi.batchScan(workIds, platform)
    return res.data.data
  }

  async function fetchResults(params?: { task_id?: string; status?: string }) {
    const res = await monitorApi.results(params)
    results.value = res.data.data
    return results.value
  }

  async function updateResult(id: string, data: any) {
    const res = await monitorApi.updateResult(id, data)
    return res.data.data
  }

  async function fetchQuota() {
    const res = await monitorApi.quota()
    quota.value = res.data.data
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
