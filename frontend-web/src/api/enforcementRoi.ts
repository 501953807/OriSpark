import client from './client'
import type { DecisionTreeResult, RoiPrediction, DefenseTier, CaseReference, UserCasesSummary } from '@/types/enforcementRoi'

export function getDecisionTree(infringementType: string, lossAmount: number) {
  return client.get('/enforcement-roi/decision-tree', {
    params: { infringement_type: infringementType, loss_amount: lossAmount },
  }).then(res => res.data as DecisionTreeResult)
}

export function predictRoi(data: {
  work_value_yuan: number
  infringement_type: string
  target_platform: string
  action_type: string
}) {
  return client.post('/enforcement-roi/predict', data)
    .then(res => res.data as RoiPrediction)
}

export function listDefenseTiers() {
  return client.get('/enforcement-roi/defense-tiers').then(res => res.data as DefenseTier[])
}

export function listCaseReferences(infringementType?: string) {
  const params = infringementType ? { infringement_type: infringementType } : undefined
  return client.get('/enforcement-roi/cases-reference', { params })
    .then(res => res.data as CaseReference[])
}

export function saveCase(data: {
  work_id?: string
  infringement_type: string
  target_platform: string
  estimated_loss_yuan: number
  action_taken: string
  cost_yuan?: number
  compensation_received_yuan?: number
  outcome: string
  notes?: string
}) {
  return client.post('/enforcement-roi/cases', data).then(res => res.data)
}

export function getUserCases() {
  return client.get('/enforcement-roi/my-cases')
    .then(res => res.data as UserCasesSummary)
}
