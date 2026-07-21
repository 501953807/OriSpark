export interface NotaryRecord {
  id: string
  work_id: string
  platform: string
  platform_url: string | null
  transaction_hash: string | null
  block_height: string | null
  blockchain: string | null
  certificate_id: string | null
  status: 'unverified' | 'pending' | 'confirmed' | 'failed' | 'expired'
  fee: number
  payment_status: 'unpaid' | 'paid'
  qr_code_url: string | null
  evidence_hash: string | null
  confirmed_at: string | null
  expires_at: string | null
  notes: string | null
  created_at: string
  updated_at: string
  certificates: Certificate[]
}

export interface Certificate {
  id: string
  notary_record_id: string
  cert_path: string
  qr_code: string | null
  template_name: string
  issued_at: string
  expires_at: string | null
}

export interface NotaryPlatform {
  key: string
  name: string
  description: string
  fee_per_record: number
  legal_level: 'national' | 'judicial' | 'commercial'
  website: string
  is_available: boolean
}
