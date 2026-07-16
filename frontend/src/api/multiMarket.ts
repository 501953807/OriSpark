import { request } from '@/api/client'
import type { MarketInfo, GeoArbitrageResult, ExpansionPhase, TaxGuide } from '@/types/multiMarket'

export function listMarkets() {
  return request.get('/multi-market/markets').then(res => res.data as MarketInfo[])
}

export function calcGeoArbitrage(data: {
  current_markets: string[]
  creator_type: string
  monthly_revenue_yuan: number
}) {
  return request.post('/multi-market/geo-arbitrage', data)
    .then(res => res.data as GeoArbitrageResult)
}

export function listPhases() {
  return request.get('/multi-market/phases').then(res => res.data as ExpansionPhase[])
}

export function createPlan(data: {
  target_markets: string[]
  phase: string
  start_date?: string
  notes?: string
}) {
  return request.post('/multi-market/plans', data).then(res => res.data)
}

export function getTaxGuide(source = 'cn', target = 'us') {
  return request.get('/multi-market/tax-guide', { params: { source, target } })
    .then(res => res.data as TaxGuide)
}
