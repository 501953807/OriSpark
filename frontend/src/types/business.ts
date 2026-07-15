export interface RevenueRecord {
  id: string
  product_id?: string
  product_name?: string
  amount: number
  currency: string
  source_type: string
  channel?: string
  date: string
  description?: string
  platform?: string
  net_revenue?: number
  source?: string
  notes?: string
  created_at: string
}

export interface RevenueSummary {
  total_revenue: number
  monthly_revenue: number
  top_channels: Array<{ channel: string; revenue: number }>
  revenue_trend: Array<{ month: string; revenue: number }>
}

export interface Partner {
  id: string
  name: string
  company_name?: string
  type: string
  contact_person?: string
  phone?: string
  email?: string
  address?: string
  website?: string
  categories?: string[]
  product_categories?: string[]
  material_capabilities?: string[]
  moq_per_category?: Record<string, number>
  typical_lead_time_days?: number
  price_range?: Array<{ category: string; unit_price_range?: [number, number]; moq?: number }>
  rating: number
  status: string
  tags?: string[]
  notes?: string
  created_at: string
  updated_at: string
}

export interface Order {
  id: string
  order_number: string
  order_type: string
  partner_id?: string
  campaign_id?: string
  product_id?: string
  listing_id?: string
  product_name: string
  product_category?: string
  quantity: number
  specifications?: string
  design_file_path?: string
  unit_price: number
  total_amount: number
  deposit_percent: number
  deposit_paid: number
  balance_due: number
  shipping_cost: number
  status: string
  expected_date?: string
  actual_date?: string
  sample_requested: number
  sample_received: number
  sample_approved: number
  shipping_method?: string
  tracking_number?: string
  notes?: string
  factory_id?: string
  sample_status: string
  quality_inspection: string
  production_quantity?: number
  delivery_date?: string
  etasync_status: string
  created_at: string
  updated_at: string
}

export interface Notification {
  id: string
  title: string
  content: string
  type: string
  is_read: boolean
  recipient_id?: string
  created_at: string
}

export interface BusinessDashboard {
  total_revenue: number
  monthly_revenue: number
  total_orders: number
  pending_orders: number
  total_partners: number
  active_partners: number
}
