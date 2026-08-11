/**
 * 通用列表管理器 Composable
 *
 * 封装常见的加载/错误/分页状态，减少 Store 中的重复代码。
 * 适用于简单的 CRUD 列表场景。
 */
import { ref } from 'vue'

export interface ListState<T> {
  items: T[]
  loading: boolean
  errorMsg: string
  total: number
  page: number
  pageSize: number
}

export interface ListActions<T, CreateData, UpdateData> {
  fetchList: (params?: Record<string, unknown>) => Promise<void>
  createItem: (data: CreateData) => Promise<T | null>
  updateItem: (id: string, data: UpdateData) => Promise<T | null>
  deleteItem: (id: string) => Promise<boolean>
}

export function useListManager<T, CreateData = Record<string, unknown>, UpdateData = Partial<T>>(
  initialState?: Partial<ListState<T>>,
) {
  const items = ref<T[]>(initialState?.items ?? [])
  const loading = ref(false)
  const errorMsg = ref('')
  const total = ref(initialState?.total ?? 0)
  const page = ref(initialState?.page ?? 1)
  const pageSize = ref(initialState?.pageSize ?? 20)

  function setError(msg: string, e?: unknown) {
    errorMsg.value = e instanceof Error ? e.message : msg
    console.error(`[useListManager] ${msg}:`, e)
  }

  function clearError() {
    errorMsg.value = ''
  }

  function withLoading<TPromise>(promise: Promise<TPromise>): Promise<TPromise> {
    loading.value = true
    clearError()
    return promise.finally(() => {
      loading.value = false
    })
  }

  return {
    items,
    loading,
    errorMsg,
    total,
    page,
    pageSize,
    setError,
    clearError,
    withLoading,
  }
}
