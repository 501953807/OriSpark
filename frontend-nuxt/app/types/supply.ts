export interface Factory {
  id: string
  name: string
  location?: string
  contact?: string
  phone?: string
  email?: string
  categories: string[]
  product_categories: string[]
  material_capabilities?: string[]
  moq?: number
  rating?: number
  typical_lead_time_days?: number
  status: string
  qualifications?: FactoryQualification[]
  created_at?: string
}

export interface FactoryQualification {
  type: string
  verified: boolean
  expire_date?: string
}

export interface FactoryOrder {
  id: string
  order_number: string
  contract_id?: string
  work_id?: string
  factory_id?: string
  product_name: string
  product_category?: string
  quantity: number
  unit_price: number
  total_amount: number
  status: 'draft' | 'quoting' | 'confirmed' | 'in_production' | 'quality_check' | 'shipped' | 'completed' | 'cancelled'
  expected_date?: string
  actual_ship_date?: string
  actual_deliver_date?: string
  shipping_method?: string
  tracking_number?: string
  quality_passed?: boolean
  quality_notes?: string
  notes?: string
  created_at?: string
  updated_at?: string
}

export interface PODConfig {
  id: string
  platform: string
  is_active: boolean
  default_store_id?: string
  created_at?: string
  updated_at?: string
}
