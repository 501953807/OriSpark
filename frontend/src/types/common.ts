export interface ApiResponse<T = unknown> {
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

export interface DashboardRecentWork {
  id: string
  title: string
  thumbnail_url?: string
  imported_at?: string
}

export interface DashboardReminder {
  id: string
  title: string
  due_date?: string
  type: string
}

export interface DashboardStats {
  total_works: number
  total_notarized: number
  infringement_alerts: number
  monthly_revenue: number
  recent_works: DashboardRecentWork[]
  upcoming_reminders: DashboardReminder[]
}
