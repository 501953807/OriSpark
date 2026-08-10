import type { PlatformStats, CreatorRankingItem, CategoryTrendItem, IndustryReport } from '~/types/data'

function getApiBase(): string {
  return useRuntimeConfig().public.apiBase
}

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem('orispark-token')
  if (!token) throw new Error('未登录')
  return { Authorization: `Bearer ${token}` }
}

export function fetchPlatformStats(): Promise<PlatformStats> {
  return $fetch(`${getApiBase()}/operator/data/platform-stats`, {
    headers: authHeaders(),
  })
}

export function fetchCreatorRanking(params?: {
  sort_by?: string
  limit?: number
}): Promise<CreatorRankingItem[]> {
  const query = new URLSearchParams()
  if (params?.sort_by) query.set('sort_by', params.sort_by)
  if (params?.limit) query.set('limit', params.limit.toString())
  const qs = query.toString()
  return $fetch(`${getApiBase()}/operator/data/creator-ranking${qs ? '?' + qs : ''}`, {
    headers: authHeaders(),
  })
}

export function fetchCategoryTrends(params?: {
  period?: string
  limit?: number
}): Promise<CategoryTrendItem[]> {
  const query = new URLSearchParams()
  if (params?.period) query.set('period', params.period)
  if (params?.limit) query.set('limit', params.limit.toString())
  const qs = query.toString()
  return $fetch(`${getApiBase()}/operator/data/category-trends${qs ? '?' + qs : ''}`, {
    headers: authHeaders(),
  })
}

export function fetchIndustryReport(month?: string): Promise<IndustryReport> {
  const query = new URLSearchParams()
  if (month) query.set('month', month)
  const qs = query.toString()
  return $fetch(`${getApiBase()}/operator/data/industry-report${qs ? '?' + qs : ''}`, {
    headers: authHeaders(),
  })
}
