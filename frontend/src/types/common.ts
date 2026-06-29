export interface ApiResponse<T = any> {
  success: boolean
  message: string
  data: T
}

export interface PaginatedData<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface DashboardStats {
  total_works: number
  total_notarized: number
  infringement_alerts: number
  monthly_revenue: number
  recent_works: any[]
  upcoming_reminders: any[]
}
