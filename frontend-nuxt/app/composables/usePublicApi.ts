import type { Work, Contract, DashboardStats, MarketTrend, CaseStudy, Opportunity } from '~/types/public'

function getApiBase(): string {
  return useRuntimeConfig().public.apiBase
}

export function fetchPublicWorks(params?: Record<string, string>): Promise<Work[]> {
  const query = new URLSearchParams(params ?? {}).toString()
  return $fetch(`${getApiBase()}/public/works${query ? '?' + query : ''}`)
}

export function fetchPublicWork(id: string): Promise<Work | { error: string }> {
  return $fetch(`${getApiBase()}/public/works/${id}`)
}

export function fetchPublicContracts(params?: Record<string, string>): Promise<Contract[]> {
  const query = new URLSearchParams(params ?? {}).toString()
  return $fetch(`${getApiBase()}/public/contracts${query ? '?' + query : ''}`)
}

export function fetchPublicContract(id: string): Promise<Contract | null> {
  // 列表接口支持按id过滤
  return fetchPublicContracts({ id }).then(
    (res) => (res as any[]).find((c) => c.id === id) ?? null
  ).catch(() => null)
}

export function fetchDashboardStats(): Promise<DashboardStats> {
  return $fetch(`${getApiBase()}/public/dashboard-stats`)
}

export function fetchMarketTrends(period: string = 'monthly'): Promise<MarketTrend[]> {
  return $fetch(`${getApiBase()}/public/market/trends?period=${period}`)
}

export function fetchCaseStudies(): Promise<CaseStudy[]> {
  return $fetch(`${getApiBase()}/public/case-studies`)
}

export function fetchOpportunities(): Promise<Opportunity[]> {
  return $fetch(`${getApiBase()}/public/opportunities`)
}

export function fetchGalleryCategories(): Promise<string[]> {
  return $fetch(`${getApiBase()}/public/gallery/categories`)
}

export function subscribeContract(contractId: string): Promise<{ id: string; status: string }> {
  const token = useCookie('orispark-token').value
  if (!token) throw new Error('未登录')
  const userStr = useCookie('orispark-user').value
  const user = userStr ? JSON.parse(userStr) : {}
  return $fetch(`${getApiBase()}/contracts/${contractId}/subscribe?subscriber_id=${user.id || ''}`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  })
}
