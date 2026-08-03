import client from './client'
import type { TaxDeadline, BurnoutRisk } from '@/types/riskWarning'

export function listTaxDeadlines() {
  return client.get('/risk-warning/tax-deadlines').then(res => res.data as TaxDeadline[])
}

export function addTaxDeadline(data: { tax_type: string; due_date: string; amount_yuan?: number }) {
  return client.post('/risk-warning/tax-deadlines', data).then(res => res.data)
}

export function completeTaxDeadline(id: string) {
  return client.patch(`/risk-warning/tax-deadlines/${id}/complete`).then(res => res.data)
}

export function getBurnoutRisk() {
  return client.get('/risk-warning/burnout-risk').then(res => res.data as BurnoutRisk)
}
