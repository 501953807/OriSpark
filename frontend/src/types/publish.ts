export interface Product {
  id: string
  work_id: string | null
  title: string
  description: string | null
  ai_description: string | null
  price: number
  category: string | null
  csv_export_path: string | null
  created_at: string
}

export interface PublishPlatform {
  key: string
  name: string
  fields: string[]
  auth_type: 'oauth' | 'api_key'
}

export interface RevenueRecord {
  id: string
  product_id: string | null
  platform: string
  amount: number
  currency: string
  date: string
  order_count: number
}
