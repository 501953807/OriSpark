/** POD 利润计算器类型定义 */

export interface PricingSimulation {
  markup_pct: number
  sale_price_usd: number
  sale_price_cny: number
  profit_usd: number
  profit_cny: number
  margin_pct: number
}

export interface SaleRecord {
  id?: string
  platform: string
  product_type: string
  sale_price_usd: number
  base_cost_usd: number
  shipping_cost_usd?: number
  platform_fee_pct?: number
  exchange_rate?: number
}

export interface ProfitResult {
  sale_price_usd: number
  sale_price_cny: number
  base_cost_usd: number
  shipping_cost_usd: number
  platform_fee_usd: number
  profit_usd: number
  profit_cny: number
  margin_pct: number
  exchange_rate: number
}

export interface DesignSummary {
  id: string
  title: string
  status: string
  total_sales: number
  total_revenue_cny: number
  total_profit_cny: number
  avg_margin_pct: number
}

export interface PodOverview {
  total_sales: number
  total_revenue_cny: number
  total_cost_cny: number
  total_profit_cny: number
  overall_margin_pct: number
  by_platform: Record<string, PlatformStat>
}

export interface PlatformStat {
  sales: number
  revenue_cny: number
  profit_cny: number
  margin_pct: number
}
