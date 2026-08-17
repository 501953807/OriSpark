import client from './client'
import type {
  CreateContractInput,
  QuoteInput,
  ValidTransitions,
  StatusSummary,
  TimelineResponse,
} from '@/types/contractMarket'

export function createContract(body: CreateContractInput) {
  return client.post('/contracts', body).then(res => res.data)
}

export function listContracts(params?: { status?: string; creator_id?: string; limit?: number; offset?: number }) {
  return client.get('/contracts', { params }).then(res => res.data as any[])
}

export function getContract(id: string) {
  return client.get(`/contracts/${id}`).then(res => res.data)
}

export function updateContract(id: string, body: Record<string, unknown>) {
  return client.patch(`/contracts/${id}`, body).then(res => res.data)
}

export function publishContract(id: string) {
  return client.post(`/contracts/${id}/publish`).then(res => res.data)
}

export function activateContract(id: string) {
  return client.post(`/contracts/${id}/activate`).then(res => res.data)
}

export function subscribeContract(id: string, subscriberId: string) {
  return client.post(`/contracts/${id}/subscribe`, null, { params: { subscriber_id: subscriberId } }).then(res => res.data)
}

export function initiateEscrow(id: string, provider: string) {
  return client.post(`/contracts/${id}/escrow/initiate`, null, { params: { provider } }).then(res => res.data)
}

export function confirmEscrow(id: string, transactionId: string) {
  return client.post(`/contracts/${id}/escrow/confirm`, null, { params: { transaction_id: transactionId } }).then(res => res.data)
}

export function activateInsurance(id: string, opts?: { insurance_product_id?: string; policy_no?: string; premium?: number }) {
  return client.post(`/contracts/${id}/insurance/activate`, null, { params: opts }).then(res => res.data)
}

export function startExecution(id: string) {
  return client.post(`/contracts/${id}/execute/start`).then(res => res.data)
}

export function completeContract(id: string) {
  return client.post(`/contracts/${id}/complete`).then(res => res.data)
}

export function disputeContract(id: string, reason: string) {
  return client.post(`/contracts/${id}/dispute`, null, { params: { reason } }).then(res => res.data)
}

export function resolveDispute(id: string, resolution: string) {
  return client.post(`/contracts/${id}/resolve`, null, { params: { resolution } }).then(res => res.data)
}

export function refundContract(id: string, reason: string) {
  return client.post(`/contracts/${id}/refund`, null, { params: { reason } }).then(res => res.data)
}

export function releaseEscrow(id: string) {
  return client.post(`/contracts/${id}/escrow/release`).then(res => res.data)
}

export function escrowRefund(id: string, reason: string) {
  return client.post(`/contracts/${id}/escrow/refund`, null, { params: { reason } }).then(res => res.data)
}

export function cancelContract(id: string, reason: string) {
  return client.post(`/contracts/${id}/cancel`, null, { params: { reason } }).then(res => res.data)
}

export function getValidTransitions() {
  return client.get('/contracts/transitions').then(res => res.data as ValidTransitions)
}

export function getStatusSummary(id: string) {
  return client.get(`/contracts/${id}/status`).then(res => res.data as StatusSummary)
}

export function getTimeline(id: string) {
  return client.get(`/contracts/${id}/timeline`).then(res => res.data as TimelineResponse)
}

export function getSplitRules(contractId: string) {
  return client.get(`/contracts/${contractId}/split-rules`).then(res => res.data)
}

export function submitQuote(body: QuoteInput) {
  return client.post(`/contracts/${body.contract_id}/split-rules/quotes`, {
    participant_id: body.participant_id,
    role: body.role,
    percentage: body.percentage,
    quote_amount: body.quote_amount,
  }).then(res => res.data)
}

export function lockSplitQuotes(contractId: string) {
  return client.post(`/contracts/${contractId}/split-rules/lock`).then(res => res.data)
}

export function calculateSplit(contractId: string, totalAmount?: number) {
  const params = totalAmount ? { total_amount: totalAmount } : {}
  return client.get(`/contracts/${contractId}/split-rules/calculate`, { params }).then(res => res.data)
}

export function executeSplit(contractId: string, body?: { total_amount?: number; batch_id?: string }) {
  return client.post(`/contracts/${contractId}/split-rules/execute`, body ?? {}).then(res => res.data)
}

export function refundSplit(contractId: string, reason: string) {
  return client.post(`/contracts/${contractId}/split-rules/refund`, { reason }).then(res => res.data)
}

export function getPlatformFee(totalAmount: number) {
  return client.get('/contracts/platform-fee', { params: { total_amount: totalAmount } }).then(res => res.data)
}
