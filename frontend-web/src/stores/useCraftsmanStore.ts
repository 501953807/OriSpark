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
import type {
  PhysicalProduct,
  MaterialInventoryItem,
  MaterialTransaction,
  ProductionBatch,
} from '@/api/craftsman'

export const useCraftsmanStore = defineStore('craftsman', () => {
  // ── State ─────────────────────────────────────────────────────

  const products = ref<CraftProduct[]>([])
  const factories = ref<Factory[]>([])
  const rfqs = ref<RFQ[]>([])
  const orders = ref<Order[]>([])
  const stats = ref<CraftsmanStats | null>(null)
  const loading = ref(false)
  const errorMsg = ref('')

  // v2 state
  const physicalProducts = ref<PhysicalProduct[]>([])
  const materials = ref<MaterialInventoryItem[]>([])
  const materialTransactions = ref<MaterialTransaction[]>([])
  const productionBatches = ref<ProductionBatch[]>([])

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
      total_products: products.value.length + physicalProducts.value.length,
      active_listings: products.value.filter((p) => p.unit_price != null).length + physicalProducts.value.filter((p) => p.is_active).length,
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
        fetchPhysicalProducts(),
        fetchMaterials(),
        fetchProductionBatches(),
      ])
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '加载数据失败'
      setError(msg)
    } finally {
      loading.value = false
    }
  }

  // ── v2: Physical Products ─────────────────────────────────────

  async function fetchPhysicalProducts(category?: string) {
    loading.value = true
    clearError()
    try {
      const res = await craftsmanApi.listPhysicalProducts(category)
      physicalProducts.value = res.data.data ?? []
      stats.value = computeStats()
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '加载物理产品失败'
      setError(msg)
      physicalProducts.value = []
    } finally {
      loading.value = false
    }
  }

  async function createPhysicalProduct(data: Partial<PhysicalProduct>): Promise<PhysicalProduct> {
    try {
      const res = await craftsmanApi.createPhysicalProduct(data)
      const created: PhysicalProduct = {
        ...data,
        id: res.data.data?.id ?? '',
        title: data.title ?? '',
        price: data.price ?? 0,
        stock_quantity: data.stock_quantity ?? 0,
        currency: data.currency ?? 'CNY',
        is_active: data.is_active ?? false,
        created_at: new Date().toISOString(),
        updated_at: undefined,
      }
      physicalProducts.value = [...physicalProducts.value, created]
      stats.value = computeStats()
      return created
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '创建物理产品失败'
      setError(msg)
      throw e
    }
  }

  async function deletePhysicalProduct(id: string): Promise<void> {
    try {
      await craftsmanApi.deletePhysicalProduct(id)
      physicalProducts.value = physicalProducts.value.filter((p) => p.id !== id)
      stats.value = computeStats()
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '删除物理产品失败'
      setError(msg)
      throw e
    }
  }

  // ── v2: Material Inventory ────────────────────────────────────

  async function fetchMaterials() {
    loading.value = true
    clearError()
    try {
      const res = await craftsmanApi.listMaterials()
      materials.value = res.data.data ?? []
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '加载原料库存失败'
      setError(msg)
      materials.value = []
    } finally {
      loading.value = false
    }
  }

  async function createMaterial(data: Partial<MaterialInventoryItem>): Promise<MaterialInventoryItem> {
    try {
      const res = await craftsmanApi.createMaterial(data)
      const created: MaterialInventoryItem = {
        ...data,
        id: res.data.data?.id ?? '',
        material_name: data.material_name ?? '',
        unit: data.unit ?? '个',
        quantity_on_hand: data.quantity_on_hand ?? 0,
        quantity_reserved: data.quantity_reserved ?? 0,
        available_qty: data.available_qty ?? 0,
        created_at: new Date().toISOString(),
      }
      materials.value = [...materials.value, created]
      return created
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '添加原料失败'
      setError(msg)
      throw e
    }
  }

  async function deleteMaterial(id: string): Promise<void> {
    try {
      await craftsmanApi.deleteMaterial(id)
      materials.value = materials.value.filter((m) => m.id !== id)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '删除原料失败'
      setError(msg)
      throw e
    }
  }

  // ── v2: Production Batches ────────────────────────────────────

  async function fetchProductionBatches(status?: string) {
    loading.value = true
    clearError()
    try {
      const res = await craftsmanApi.listProductionBatches(status)
      productionBatches.value = res.data.data ?? []
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '加载生产批次失败'
      setError(msg)
      productionBatches.value = []
    } finally {
      loading.value = false
    }
  }

  async function createProductionBatch(data: { work_id?: string | null; title: string; planned_quantity: number }): Promise<ProductionBatch> {
    try {
      const res = await craftsmanApi.createProductionBatch(data)
      const created: ProductionBatch = { ...data, id: res.data.data?.id ?? '', produced_quantity: 0, sold_quantity: 0, status: 'planned', created_at: new Date().toISOString() }
      productionBatches.value = [...productionBatches.value, created]
      return created
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '创建生产批次失败'
      setError(msg)
      throw e
    }
  }

  async function updateProductionBatchStatus(id: string, status: ProductionBatch['status']): Promise<void> {
    try {
      await craftsmanApi.updateProductionBatch(id, { status })
      const idx = productionBatches.value.findIndex((b) => b.id === id)
      if (idx >= 0) {
        const copy = [...productionBatches.value]
        copy[idx] = { ...copy[idx], status }
        productionBatches.value = copy
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '更新生产批次失败'
      setError(msg)
      throw e
    }
  }

  async function deleteProductionBatch(id: string): Promise<void> {
    try {
      await craftsmanApi.deleteProductionBatch(id)
      productionBatches.value = productionBatches.value.filter((b) => b.id !== id)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '删除生产批次失败'
      setError(msg)
      throw e
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
    physicalProducts,
    materials,
    materialTransactions,
    productionBatches,
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
    // v2 actions
    fetchPhysicalProducts,
    createPhysicalProduct,
    deletePhysicalProduct,
    fetchMaterials,
    createMaterial,
    deleteMaterial,
    fetchProductionBatches,
    createProductionBatch,
    updateProductionBatchStatus,
    deleteProductionBatch,
  }
})
