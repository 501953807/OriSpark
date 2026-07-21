import client from './client'
import type {
  CraftProduct,
  Factory,
  RFQ,
  Order,
  CraftsmanStats,
} from '@/types/craftsman'

export interface PhysicalProduct {
  id: string
  work_id?: string | null
  title: string
  description?: string | null
  category?: string | null
  dimensions?: Record<string, unknown> | null
  weight_g?: number | null
  price: number
  currency: string
  stock_quantity: number
  shipping_regions?: string[] | null
  is_active: boolean
  created_at?: string | null
  updated_at?: string | null
}

export interface MaterialInventoryItem {
  id: string
  material_name: string
  material_category?: string | null
  unit: string
  quantity_on_hand: number
  quantity_reserved: number
  available_qty: number
  reorder_level?: number | null
  unit_cost?: number | null
  location?: string | null
  last_counted_at?: string | null
  created_at?: string | null
}

export interface MaterialTransaction {
  id: string
  material_id: string
  transaction_type: 'purchase' | 'consume' | 'scrap'
  quantity: number
  reference_type?: string | null
  reference_id?: string | null
  notes?: string | null
  created_at?: string | null
}

export interface ProductionBatch {
  id: string
  work_id?: string | null
  title: string
  planned_quantity: number
  produced_quantity: number
  sold_quantity: number
  status: 'planned' | 'in_production' | 'done' | 'shipped'
  started_at?: string | null
  completed_at?: string | null
  created_at?: string | null
}

export const craftsmanApi = {
  // ── Products ──────────────────────────────────────────────────

  getProducts: () =>
    client.get<{ data: CraftProduct[] }>('/craftsman/products'),

  getProduct: (id: string) =>
    client.get<{ data: CraftProduct }>(`/craftsman/products/${id}`),

  createProduct: (data: Partial<CraftProduct>) =>
    client.post<{ data: { id: string } }>('/craftsman/products', data),

  updateProduct: (id: string, data: Partial<CraftProduct>) =>
    client.patch<{ data: CraftProduct }>(`/craftsman/products/${id}`, data),

  deleteProduct: (id: string) =>
    client.delete<{ data: null }>(`/craftsman/products/${id}`),

  // ── Factories ─────────────────────────────────────────────────

  getFactories: () =>
    client.get<{ data: Factory[] }>('/craftsman/factories'),

  createFactory: (data: Partial<Factory>) =>
    client.post<{ data: { id: string } }>('/craftsman/factories', data),

  updateFactory: (id: string, data: Partial<Factory>) =>
    client.patch<{ data: Factory }>(`/craftsman/factories/${id}`, data),

  deleteFactory: (id: string) =>
    client.delete<{ data: null }>(`/craftsman/factories/${id}`),

  // ── RFQs ──────────────────────────────────────────────────────

  getRFQs: () =>
    client.get<{ data: RFQ[] }>('/craftsman/rfqs'),

  createRFQ: (data: Partial<RFQ>) =>
    client.post<{ data: { id: string } }>('/craftsman/rfqs', data),

  updateRFQ: (id: string, data: Partial<RFQ>) =>
    client.patch<{ data: RFQ }>(`/craftsman/rfqs/${id}`, data),

  deleteRFQ: (id: string) =>
    client.delete<{ data: null }>(`/craftsman/rfqs/${id}`),

  // ── Orders ────────────────────────────────────────────────────

  getOrders: () =>
    client.get<{ data: Order[] }>('/craftsman/orders'),

  // ── Stats (placeholder — calculated on frontend) ──────────────

  getStats: (): Promise<CraftsmanStats> =>
    // Will be computed from products/factories/rfqs on frontend
    Promise.resolve({
      total_products: 0,
      active_listings: 0,
      factory_count: 0,
      rfq_count: 0,
      monthly_revenue: 0,
    }),

  // ── v2: Physical Products ────────────────────────────────────

  listPhysicalProducts: (category?: string) =>
    client.get<{ data: PhysicalProduct[] }>('/craftsman/physical-products', { params: category ? { category } : undefined }),

  createPhysicalProduct: (data: Partial<PhysicalProduct>) =>
    client.post<{ data: { id: string } }>('/craftsman/physical-products', data),

  updatePhysicalProduct: (id: string, data: Partial<PhysicalProduct>) =>
    client.patch<{ data: { id: string } }>(`/craftsman/physical-products/${id}`, data),

  deletePhysicalProduct: (id: string) =>
    client.delete<{ data: null }>(`/craftsman/physical-products/${id}`),

  // ── v2: Material Inventory ───────────────────────────────────

  listMaterials: () =>
    client.get<{ data: MaterialInventoryItem[] }>('/craftsman/materials'),

  createMaterial: (data: Partial<MaterialInventoryItem>) =>
    client.post<{ data: { id: string } }>('/craftsman/materials', data),

  updateMaterial: (id: string, data: Partial<MaterialInventoryItem>) =>
    client.patch<{ data: { id: string } }>(`/craftsman/materials/${id}`, data),

  deleteMaterial: (id: string) =>
    client.delete<{ data: null }>(`/craftsman/materials/${id}`),

  createMaterialTransaction: (data: { material_id: string; transaction_type: 'purchase' | 'consume' | 'scrap'; quantity: number; reference_type?: string | null; reference_id?: string | null; notes?: string | null }) =>
    client.post<{ data: { id: string } }>('/craftsman/material-transactions', data),

  listMaterialTransactions: (materialId?: string, limit = 50) =>
    client.get<{ data: MaterialTransaction[] }>('/craftsman/material-transactions', { params: materialId ? { material_id: materialId, limit } : { limit } }),

  // ── v2: Production Batches ───────────────────────────────────

  listProductionBatches: (status?: string) =>
    client.get<{ data: ProductionBatch[] }>('/craftsman/production-batches', { params: status ? { status } : undefined }),

  createProductionBatch: (data: { work_id?: string | null; title: string; planned_quantity: number }) =>
    client.post<{ data: { id: string } }>('/craftsman/production-batches', data),

  updateProductionBatch: (id: string, data: Partial<ProductionBatch>) =>
    client.patch<{ data: { id: string; title: string; status: string; planned_quantity: number; produced_quantity: number; sold_quantity: number } }>(`/craftsman/production-batches/${id}`, data),

  deleteProductionBatch: (id: string) =>
    client.delete<{ data: null }>(`/craftsman/production-batches/${id}`),
}
