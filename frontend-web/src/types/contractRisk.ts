/** 合约风险评估类型定义 */

export interface ContractClauseResult {
  clause_index: number
  clause_text: string
  clause_category: string | null
  risk_level: string | null
  risk_description: string | null
  suggestion: string | null
  is_flagged: boolean
}

export interface ContractReviewResult {
  id: string
  total_score: number
  risk_level: string
  clauses_found: number
  risk_count: number
  clauses: ContractClauseResult[]
  suggestions: string[]
  created_at: string
}

export interface ContractReviewRequest {
  review_type: string
  contract_text: string
  target_type?: string | null
  target_id?: string | null
}

export interface TransactionCheckIssue {
  field: string
  issue: string
}

export interface TransactionCheckResult {
  passed: boolean
  score: number
  risk_level: string
  issues: TransactionCheckIssue[]
}
