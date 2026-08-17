import client from './client'
import type { PricingSimulation, SaleRecord, ProfitResult, DesignSummary, PodOverview } from '@/types/podProfit'

export interface ProductConfigInput {
  platform: string
  product_type: string
  markup_rate: number
}

async function unwrap<T>(res: any): Promise<T> {
  return (res.data?.data ?? res.data) as T
}

export const podProfitApi = {
  getProductConfig: (platform: string, productType: string) =>
    unwrap<{ id: string; platform: string; product_type: string; base_cost_usd: number; markup_rate: number }>(
      client.post('/pod-profit/product-config', { platform, product_type: productType, markup_rate: 0.3 })
    ),

  simulatePricing: (data: ProductConfigInput) =>
    unwrap<PricingSimulation[]>(client.post('/pod-profit/simulate-pricing', data)),

  recordSale: (data: SaleRecord) =>
    unwrap<ProfitResult>(client.post('/pod-profit/log-sale', data)),

  getDesignsSummary: () =>
    unwrap<DesignSummary[]>(client.get('/pod-profit/designs-summary')),

  getOverview: () =>
    unwrap<PodOverview>(client.get('/pod-profit/overview')),
}
