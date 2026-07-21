import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getNavigationStatus, completeTask, listTasks } from '@/api/navigation'
import type { NavigationStatusResult, CompleteTaskResult } from '@/types/navigation'

export const useNavigationStore = defineStore('navigation', () => {
  const loading = ref(false)
  const status = ref<NavigationStatusResult | null>(null)
  const tasks = ref<any[]>([])

  async function fetchStatus(userId: string, path = 'onboarding') {
    loading.value = true
    try {
      status.value = await getNavigationStatus(userId, path)
      return status.value
    } finally {
      loading.value = false
    }
  }

  async function markComplete(taskKey: string): Promise<CompleteTaskResult> {
    return completeTask(taskKey)
  }

  async function refreshStatus(userId: string, path = 'onboarding') {
    return fetchStatus(userId, path)
  }

  return { loading, status, tasks, fetchStatus, markComplete, refreshStatus }
})
