export interface EnforcementAction {
  id: string
  monitor_result_id: string
  work_id?: string
  action_type: string
  platform: string
  status: 'pending_review' | 'confirmed' | 'evidence_gathered' | 'complaint_filed' | 'resolved'
  complaint_text?: string
  template_used?: string
  sent_at?: string
  response_text?: string
  resolved_at?: string
  resolution_type?: string
  compensation_amount?: number
  notes?: string
  created_at: string
  updated_at: string
  work_title?: string
  work_file_type?: string
  infringement_url?: string
  similarity_score?: number
}

export interface EnforcementTemplate {
  id: string
  platform: string
  jurisdiction: string
  action_type: string
  title: string
  body_template: string
  required_evidence?: string[]
  filing_url?: string
  created_at: string
}

export interface EvidencePackage {
  work_info: Record<string, any>
  sha256: string
  notary_records: any[]
  c2pa_manifests: any[]
  ai_sessions: any[]
  work_versions: any[]
  infringement_evidence: any[]
}

export type FromWorkStatus = 'matches_found' | 'no_matches' | 'already_enforced'

export interface FromWorkResponse {
  status: FromWorkStatus
  action?: Record<string, any> | null
  actions?: Record<string, any>[] | null
  action_ids?: string[] | null
  message?: string | null
}
