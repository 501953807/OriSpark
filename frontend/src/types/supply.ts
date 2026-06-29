export interface Partner {
  id: string
  name: string
  company_name: string | null
  contact_person: string | null
  phone: string | null
  email: string | null
  address: string | null
  website: string | null
  categories: string[] | null
  moq: number | null
  rating: number
  tags: string[] | null
  status: string
  notes: string | null
  created_at: string
}

export interface Order {
  id: string
  order_number: string
  partner_id: string | null
  product_name: string
  quantity: number
  total_amount: number
  deposit_paid: number
  balance_due: number
  status: string
  expected_date: string | null
  actual_date: string | null
  notes: string | null
  created_at: string
}

export interface Reminder {
  id: string
  type: string
  related_id: string
  title: string
  remind_at: string
  status: string
}

// ─── P2: Design Listing types ───────────────────────────────────────

export interface DesignListing {
  id: string
  work_id: string | null
  product_template_id: string
  title: string
  description: string | null
  price: number
  cost: number
  currency: string
  monetization_path: string | null
  variant_sku: string | null
  variant_name: string | null
  spec_validation: Record<string, unknown> | null
  mockup_image_path: string | null
  status: string  // draft / active / discontinued
  created_at: string
  updated_at: string
}

export interface CompatibleTemplate {
  template_id: string
  name_zh: string
  name_en: string
  material_category: string
  compatibility_score: number
  spec_result: 'pass' | 'warning' | 'error'
  error_count: number
  warning_count: number
  min_required_px: string
  current_meets: boolean
}

export interface SpecValidationCompatResponse {
  compatible_templates: CompatibleTemplate[]
  summary: {
    pass_count: number
    warning_count: number
    error_count: number
    total_checked: number
  }
  recommendation: string
}

export interface RemediationSuggestion {
  type: string
  field: string
  description: string
  current?: string
  required?: string
  scale_factor?: string
}

export interface SpecValidationRemediationResponse {
  suggestions: RemediationSuggestion[]
  required_size: string
  required_dpi: number
  category_name: string
}

export interface ListingDetail {
  id: string
  work_id: string | null
  product_template_id: string
  title: string
  description: string | null
  price: number
  cost: number
  currency: string
  monetization_path: string | null
  variant_sku: string | null
  variant_name: string | null
  spec_validation: Record<string, unknown> | null
  mockup_image_path: string | null
  status: string
  publications: Array<{
    id: string
    platform: string
    status: string
    listing_url: string | null
    published_at: string | null
  }>
  revenues: Array<{
    id: string
    amount: number
    date: string | null
    platform: string
    net_revenue: number
  }>
  orders: Array<{
    id: string
    order_number: string
    status: string
    total_amount: number
  }>
  total_revenue: number
  created_at: string
}
