/** 合约市场类型定义 */

// ContractInstance — core model fields returned by GET /contracts/:id
export interface ContractInstance {
  id: string
  title: string
  description?: string
  work_id?: string
  contract_type: 'copyright_transfer' | 'product_license' | 'exclusive_license' | 'non_exclusive_license'
  total_amount: number
  currency: string
  billing_cycle: 'one_time' | 'monthly' | 'quarterly' | 'yearly' | 'revenue_share'
  scope_usage: 'personal' | 'commercial' | 'resale' | 'modify'
  scope_geography: 'local' | 'national' | 'global' | 'china' | 'eu' | 'us' | 'jp'
  scope_duration?: string
  status: 'draft' | 'listed' | 'active' | 'subscribed' | 'escrowed' | 'insured' | 'executing' | 'inspect' | 'completed' | 'dispute' | 'resolved' | 'refunded' | 'cancelled'
  verified: 'pending' | 'approved' | 'rejected'
  creator_id: string
  operator_id?: string
  trader_id?: string
  split_rules_json?: string
  insurance_product_id?: string
  insurance_policy_no?: string
  insurance_premium?: number
  escrow_provider?: string
  escrow_transaction_id?: string
  published_at?: string
  subscribed_at?: string
  escrowed_at?: string
  executed_at?: string
  completed_at?: string
  created_at?: string
  updated_at?: string
}

// List item shape from GET /contracts
export interface ContractListItem {
  id: string
  title: string
  status: string
  total_amount: number
  currency: string
  contract_type: string
  creator_id: string
  verified: string
  created_at?: string
}

// GET /contracts/transitions response
export interface ValidTransitions {
  valid_transitions: Record<string, string[]>
  labels: Record<string, string>
}

// GET /contracts/:id/status response
export interface StatusSummary {
  id: string
  title?: string
  status: string
  status_label: string
  next_possible: Array<{ status: string; label: string }>
  verified: string
  created_at?: string
  updated_at?: string
}

// GET /contracts/:id/timeline response
export interface TimelineResponse {
  contract_id: string
  timeline: Array<{
    timestamp?: string
    event: string
    label?: string
    action?: string
  }>
}

// Split rules
export interface SplitRule {
  id: string
  contract_id: string
  participant_id: string
  role: string
  percentage: number
  quote_amount?: number
  quoted_at: string
  locked_at?: string
}

// Input types
export interface CreateContractInput {
  title: string
  description?: string
  work_id?: string
  contract_type?: string
  total_amount: number
  currency?: string
  billing_cycle?: string
  scope_usage?: string
  scope_geography?: string
  scope_duration?: string
  split_rules_json?: string
}

export interface QuoteInput {
  contract_id: string
  participant_id: string
  role: string
  percentage: number
  quote_amount: number
}
