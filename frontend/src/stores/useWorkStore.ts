import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Work, WorkListParams } from '@/types/work'
import { worksApi } from '@/api/works'
import { useAppStore } from '@/stores/useAppStore'

export const useWorkStore = defineStore('work', () => {
  // State
  const works = ref<Work[]>([])
  const currentWork = ref<Work | null>(null)
  const total = ref(0)
  const loading = ref(false)
  const filters = ref<WorkListParams>({
    page: 1,
    page_size: 20,
    file_type: undefined,
    status: 'active',
    tag: undefined,
    search: undefined,
    sort_by: 'imported_at',
    sort_order: 'desc',
  })

  // Actions
  async function fetchWorks() {
    loading.value = true
    try {
      const res = await worksApi.list(filters.value)
      works.value = res.data.data.items
      total.value = res.data.data.total
      const appStore = useAppStore()
      appStore.workCount = total.value
    } catch (e) {
      console.error('fetchWorks failed:', e)
    } finally {
      loading.value = false
    }
  }

  async function fetchWork(id: string) {
    try {
      const res = await worksApi.get(id)
      currentWork.value = res.data.data
      return currentWork.value
    } catch (e) {
      console.error(`fetchWork(${id}) failed:`, e)
      throw e
    }
  }

  async function uploadWork(formData: FormData) {
    try {
      const res = await worksApi.create(formData)
      await fetchWorks()
      return res.data.data
    } catch (e) {
      console.error('uploadWork failed:', e)
      throw e
    }
  }

  async function updateWork(id: string, data: Partial<Work>) {
    try {
      const res = await worksApi.update(id, data)
      await fetchWorks()
      return res.data.data
    } catch (e) {
      console.error(`updateWork(${id}) failed:`, e)
      throw e
    }
  }

  async function deleteWork(id: string) {
    try {
      await worksApi.delete(id)
      await fetchWorks()
    } catch (e) {
      console.error(`deleteWork(${id}) failed:`, e)
      throw e
    }
  }

  async function restoreWork(id: string) {
    try {
      await worksApi.restore(id)
      await fetchWorks()
    } catch (e) {
      console.error(`restoreWork(${id}) failed:`, e)
      throw e
    }
  }

  async function permanentDeleteWork(id: string) {
    try {
      await worksApi.permanentDelete(id)
      await fetchWorks()
    } catch (e) {
      console.error(`permanentDeleteWork(${id}) failed:`, e)
      throw e
    }
  }

  async function fetchTrashedWorks() {
    loading.value = true
    try {
      const res = await worksApi.trash(filters.value)
      works.value = res.data.data.items
      total.value = res.data.data.total
    } catch (e) {
      console.error('fetchTrashedWorks failed:', e)
    } finally {
      loading.value = false
    }
  }

  async function emptyTrash() {
    try {
      await worksApi.emptyTrash()
      await fetchWorks()
    } catch (e) {
      console.error('emptyTrash failed:', e)
      throw e
    }
  }

  async function recomputeHash(id: string) {
    try {
      const res = await worksApi.recomputeHash(id)
      return res.data.data
    } catch (e) {
      console.error(`recomputeHash(${id}) failed:`, e)
      throw e
    }
  }

  function setFilter<K extends keyof WorkListParams>(key: K, value: WorkListParams[K]) {
    filters.value = { ...filters.value, [key]: value, page: 1 }
    fetchWorks()
  }

  function setPage(page: number) {
    filters.value.page = page
    fetchWorks()
  }

  return {
    works,
    currentWork,
    total,
    loading,
    filters,
    fetchWorks,
    fetchWork,
    uploadWork,
    updateWork,
    deleteWork,
    restoreWork,
    permanentDeleteWork,
    fetchTrashedWorks,
    emptyTrash,
    recomputeHash,
    setFilter,
    setPage,
  }
})
