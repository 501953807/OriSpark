export interface OperationScope {
  regions?: string[]
  channels?: string[]
  products?: string[]
  transform_rights?: Record<string, boolean>
  duration_months?: number
}

export interface OperationCooperation {
  id: string
  work_id: string
  work_title?: string
  creator_id: string
  creator_name?: string
  operator_id: string
  operator_name?: string
  status: 'pending' | 'accepted' | 'rejected' | 'expired' | 'cancelled'
  scope: OperationScope
  notes?: string
  operator_notes?: string
  created_at: string
  accepted_at?: string
  rejected_at?: string
  expires_at?: string
}
