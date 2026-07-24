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
