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
      // Update sidebar badge
      const appStore = useAppStore()
      appStore.workCount = total.value
    } finally {
      loading.value = false
    }
  }

  async function fetchWork(id: string) {
    const res = await worksApi.get(id)
    currentWork.value = res.data.data
    return currentWork.value
  }

  async function uploadWork(formData: FormData) {
    const res = await worksApi.create(formData)
    await fetchWorks()
    return res.data.data
  }

  async function updateWork(id: string, data: Partial<Work>) {
    const res = await worksApi.update(id, data)
    await fetchWorks()
    return res.data.data
  }

  async function deleteWork(id: string) {
    await worksApi.delete(id)
    await fetchWorks()
  }

  async function restoreWork(id: string) {
    await worksApi.restore(id)
    await fetchWorks()
  }

  async function permanentDeleteWork(id: string) {
    await worksApi.permanentDelete(id)
    await fetchWorks()
  }

  async function fetchTrashedWorks() {
    loading.value = true
    try {
      const res = await worksApi.trash(filters.value)
      works.value = res.data.data.items
      total.value = res.data.data.total
    } finally {
      loading.value = false
    }
  }

  async function emptyTrash() {
    await worksApi.emptyTrash()
    await fetchWorks()
  }

  async function recomputeHash(id: string) {
    const res = await worksApi.recomputeHash(id)
    return res.data.data
  }

  function setFilter(key: string, value: any) {
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
