import client from './client'

// ---------------------------------------------------------------------------
// Inline types for dashboard response payloads so consumers stay type-safe.
// ---------------------------------------------------------------------------

export interface RevenueByMonth {
  month: string
  revenue: number
  currency?: string
}

export interface RevenueSummary {
  total_revenue: number
  revenue_by_month: RevenueByMonth[]
  currency?: string
}

export interface WorkTrend {
  date: string
  count: number
}

export interface TrendsSummary {
  daily_trends: WorkTrend[]
  total_works_30d: number
  avg_daily: number
}

export interface DashboardStats {
  total_works: number
  total_notarized: number
  infringement_alerts: number
  monthly_revenue: number
  recent_works: RecentWork[]
  upcoming_reminders: Record<string, unknown>[]
  recent_alerts?: Array<{
    id: string
    work_title?: string
    matched_title?: string
    found_at?: string
  }>
}

export interface RecentWork {
  id: string
  title: string
  file_type: string
  file_extension?: string
  thumbnail_url?: string
  thumbnail_path?: string
  file_size?: number
  sha256?: string
  is_verified?: boolean
  imported_at?: string
}

export const dashboardApi = {
  stats: () =>
    client.get<{ data: DashboardStats }>('/dashboard/stats'),

  recent: (limit?: number) =>
    client.get<{ data: RecentWork[] }>('/dashboard/recent', { params: { limit } }),

  revenue: () =>
    client.get<{ data: RevenueSummary }>('/dashboard/revenue'),

  trends: () =>
    client.get<{ data: TrendsSummary }>('/dashboard/trends'),
}
