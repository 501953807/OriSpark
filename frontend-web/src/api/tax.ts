/**全球税务结算 API 客户端.*/

import request from '@/utils/request'

export interface TaxAgent {
  id: string
  participant_id: string
  name: string
  license_no: string | null
  service_areas: string[]
  fee_rate: number
  avalara_account_id: string | null
  status: string
  rating: number | null
  review_count: number
  created_at: string | null
  approved_at: string | null
}

export interface TaxReport {
  id: string
  participant_id: string
  agent_id: string | null
  report_period: string
  total_income: number
  total_tax_withheld: number
  total_tax_owed: number
  currency: string
  generated_by: string | null
  status: string
  file_path: string | null
  created_at: string | null
  finalized_at: string | null
}

export interface TaxCalculation {
  id: string
  contract_id: string | null
  transaction_id: string | null
  seller_location: Record<string, string>
  buyer_location: Record<string, string>
  product_type: string
  amount: number
  tax_amount: number | null
  tax_rate: number | null
  tax_jurisdiction: string | null
  exemption_status: string | null
  calculated_by: string
  calculated_at: string | null
}

export interface CurrencyConversion {
  source_currency: string
  target_currency: string
  source_amount: number
  target_amount: number
}

const taxAgentApi = {
  list(status?: string) {
    return request.get('/tax/agents', { params: { status } })
  },

  getById(id: string) {
    return request.get(`/tax/agents/${id}`)
  },

  create(data: Partial<TaxAgent>) {
    return request.post('/tax/agents', data)
  },

  update(id: string, data: Partial<TaxAgent>) {
    return request.patch(`/tax/agents/${id}`, data)
  },

  listReports(participantId: string) {
    return request.get('/tax/reports', { params: { participant_id: participantId } })
  },

  createReport(data: { participant_id: string; period: string; currency?: string }) {
    return request.post('/tax/reports', data)
  },
}

const settlementApi = {
  calculateTax(data: {
    seller_location: Record<string, string>
    buyer_location: Record<string, string>
    product_type: string
    amount: number
    currency?: string
    contract_id?: string
  }) {
    return request.post('/settlement/calculate-tax', data)
  },

  listCalculations(productType?: string) {
    return request.get('/settlement/calculations', { params: { product_type: productType } })
  },

  convertCurrency(data: {
    source_currency: string
    target_currency: string
    amount: number
  }) {
    return request.post('/settlement/convert-currency', data)
  },
}

export const taxApi = { taxAgentApi, settlementApi }
export default taxApi
