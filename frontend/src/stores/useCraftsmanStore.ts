import { defineStore } from 'pinia'
import { ref } from 'vue'
import { craftsmanApi } from '@/api/craftsman'
import type {
  CraftProduct,
  Factory,
  RFQ,
  Order,
  CraftsmanStats,
} from '@/types/craftsman'

export const useCraftsmanStore = defineStore('craftsman', () => {
  // ── State ─────────────────────────────────────────────────────

  const products = ref<CraftProduct[]>([])
  const factories = ref<Factory[]>([])
  const rfqs = ref<RFQ[]>([])
  const orders = ref<Order[]>([])
  const stats = ref<CraftsmanStats | null>(null)
  const loading = ref(false)
  const errorMsg = ref('')

  // ── Helpers ───────────────────────────────────────────────────

  function setError(msg: string) {
    errorMsg.value = msg
    console.error('[craftsman]', msg)
  }

  function clearError() {
    errorMsg.value = ''
  }

  function computeStats(): CraftsmanStats {
    return {
      total_products: products.value.length,
      active_listings: products.value.filter((p) => p.unit_price != null).length,
      factory_count: factories.value.length,
      rfq_count: rfqs.value.length,
      monthly_revenue: 0,
    }
  }

  // ── Products ──────────────────────────────────────────────────

  async function fetchProducts() {
    loading.value = true
    clearError()
    try {
      const res = await craftsmanApi.getProducts()
      products.value = res.data.data ?? []
      stats.value = computeStats()
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '加载作品失败'
      setError(msg)
      products.value = []
    } finally {
      loading.value = false
    }
  }

  async function createProduct(data: Partial<CraftProduct>): Promise<CraftProduct> {
    try {
      const res = await craftsmanApi.createProduct(data)
      const created: CraftProduct = {
        ...data,
        id: res.data.data?.id ?? '',
        craft_type: data.craft_type ?? 'other',
        moq: data.moq ?? 1,
        created_at: new Date().toISOString(),
      }
      products.value = [...products.value, created]
      stats.value = computeStats()
      return created
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '创建作品失败'
      setError(msg)
      throw e
    }
  }

  async function updateProduct(id: string, data: Partial<CraftProduct>): Promise<void> {
    try {
      const res = await craftsmanApi.updateProduct(id, data)
      const updated = res.data.data
      const idx = products.value.findIndex((p) => p.id === id)
      if (idx >= 0) {
        const copy = [...products.value]
        copy[idx] = updated
        products.value = copy
        stats.value = computeStats()
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '更新作品失败'
      setError(msg)
      throw e
    }
  }

  async function deleteProduct(id: string): Promise<void> {
    try {
      await craftsmanApi.deleteProduct(id)
      const copy = products.value.filter((p) => p.id !== id)
      products.value = copy
      stats.value = computeStats()
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '删除作品失败'
      setError(msg)
      throw e
    }
  }

  // ── Factories ─────────────────────────────────────────────────

  async function fetchFactories() {
    loading.value = true
    clearError()
    try {
      const res = await craftsmanApi.getFactories()
      factories.value = res.data.data ?? []
      stats.value = computeStats()
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '加载工厂失败'
      setError(msg)
      factories.value = []
    } finally {
      loading.value = false
    }
  }

  async function createFactory(data: Partial<Factory>): Promise<Factory> {
    try {
      const res = await craftsmanApi.createFactory(data)
      const created: Factory = {
        ...data,
        id: res.data.data?.id ?? '',
        name: data.name ?? '',
        created_at: new Date().toISOString(),
      }
      factories.value = [...factories.value, created]
      stats.value = computeStats()
      return created
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '添加工厂失败'
      setError(msg)
      throw e
    }
  }

  async function updateFactory(id: string, data: Partial<Factory>): Promise<void> {
    try {
      const res = await craftsmanApi.updateFactory(id, data)
      const updated = res.data.data
      const idx = factories.value.findIndex((f) => f.id === id)
      if (idx >= 0) {
        const copy = [...factories.value]
        copy[idx] = updated
        factories.value = copy
        stats.value = computeStats()
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '更新工厂失败'
      setError(msg)
      throw e
    }
  }

  async function deleteFactory(id: string): Promise<void> {
    try {
      await craftsmanApi.deleteFactory(id)
      const copy = factories.value.filter((f) => f.id !== id)
      factories.value = copy
      stats.value = computeStats()
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '删除工厂失败'
      setError(msg)
      throw e
    }
  }

  // ── RFQs ──────────────────────────────────────────────────────

  async function fetchRFQs() {
    loading.value = true
    clearError()
    try {
      const res = await craftsmanApi.getRFQs()
      rfqs.value = res.data.data ?? []
      stats.value = computeStats()
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '加载询价单失败'
      setError(msg)
      rfqs.value = []
    } finally {
      loading.value = false
    }
  }

  async function createRFQ(data: Partial<RFQ>): Promise<RFQ> {
    try {
      const res = await craftsmanApi.createRFQ(data)
      const created: RFQ = {
        ...data,
        id: res.data.data?.id ?? '',
        craft_product_id: data.craft_product_id ?? '',
        title: data.title ?? '',
        status: data.status ?? 'open',
        created_at: new Date().toISOString(),
      }
      rfqs.value = [...rfqs.value, created]
      stats.value = computeStats()
      return created
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '创建询价单失败'
      setError(msg)
      throw e
    }
  }

  async function deleteRFQ(id: string): Promise<void> {
    try {
      await craftsmanApi.deleteRFQ(id)
      const copy = rfqs.value.filter((r) => r.id !== id)
      rfqs.value = copy
      stats.value = computeStats()
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '删除询价单失败'
      setError(msg)
      throw e
    }
  }

  async function updateRFQ(id: string, data: Partial<RFQ>): Promise<void> {
    try {
      const res = await craftsmanApi.updateRFQ(id, data)
      const updated = res.data.data
      const idx = rfqs.value.findIndex((r) => r.id === id)
      if (idx >= 0) {
        const copy = [...rfqs.value]
        copy[idx] = updated
        rfqs.value = copy
        stats.value = computeStats()
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '更新询价单失败'
      setError(msg)
      throw e
    }
  }

  // ── Orders ────────────────────────────────────────────────────

  async function fetchOrders() {
    loading.value = true
    clearError()
    try {
      const res = await craftsmanApi.getOrders()
      orders.value = res.data.data ?? []
    } catch (_e: unknown) {
      // Orders endpoint may not exist yet; tolerate gracefully
      orders.value = []
    } finally {
      loading.value = false
    }
  }

  // ── Bulk Load ─────────────────────────────────────────────────

  async function fetchAll() {
    loading.value = true
    clearError()
    try {
      await Promise.allSettled([
        fetchProducts(),
        fetchFactories(),
        fetchRFQs(),
        fetchOrders(),
      ])
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '加载数据失败'
      setError(msg)
    } finally {
      loading.value = false
    }
  }

  return {
    // State
    products,
    factories,
    rfqs,
    orders,
    stats,
    loading,
    errorMsg,
    // Actions
    fetchProducts,
    createProduct,
    updateProduct,
    deleteProduct,
    fetchFactories,
    createFactory,
    updateFactory,
    deleteFactory,
    fetchRFQs,
    createRFQ,
    updateRFQ,
    deleteRFQ,
    fetchOrders,
    fetchAll,
    setError,
    clearError,
  }
})
