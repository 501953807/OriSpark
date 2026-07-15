// ── Type aliases ────────────────────────────────────────────────

export type CraftType =
  | 'embroidery'
  | 'ceramics'
  | 'woodcarving'
  | 'weaving'
  | 'pottery'
  | 'other'

export type RFQStatus = 'open' | 'quoted' | 'awarded' | 'closed'

export type SampleStatus = 'pending' | 'approved' | 'rejected'

export type QualityStatus = 'pending' | 'pass' | 'fail'

export type ETSyncStatus = 'idle' | 'syncing' | 'synced' | 'error'

// ── Dimensions ──────────────────────────────────────────────────

export interface Dimensions {
  length?: number
  width?: number
  height?: number
  weight?: number
}

// ── CraftProduct ────────────────────────────────────────────────

export interface CraftProduct {
  id: string
  work_variant_id?: string
  title?: string
  material?: string
  craft_type: CraftType
  dimensions?: Dimensions
  moq: number
  unit_price?: number
  production_time_days?: number
  created_at?: string
}

// ── Factory ─────────────────────────────────────────────────────

export interface Factory {
  id: string
  name: string
  location?: string
  contact?: string
  rating?: number
  capabilities?: string[]
  created_at?: string
}

// ── RFQ ─────────────────────────────────────────────────────────

export interface RFQ {
  id: string
  craft_product_id: string
  title: string
  description?: string
  quantity_needed?: number
  material_specs?: Record<string, unknown>
  target_price?: number
  status: RFQStatus
  quoted_factories?: string[]
  created_by?: string
  created_at?: string
}

// ── Order ───────────────────────────────────────────────────────

export interface Order {
  id: string
  rfq_id?: string
  factory_id?: string
  craft_product_id?: string
  sample_status: SampleStatus
  quality_inspection: QualityStatus
  production_quantity?: number
  delivery_date?: string
  etasync_status: ETSyncStatus
  created_at?: string
}

// ── CraftsmanStats ──────────────────────────────────────────────

export interface CraftsmanStats {
  total_products: number
  active_listings: number
  factory_count: number
  rfq_count: number
  monthly_revenue: number
}
