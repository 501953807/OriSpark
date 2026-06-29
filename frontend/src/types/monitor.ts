export interface MonitorTask {
  id: string
  work_id: string
  search_type: 'image' | 'text' | 'code'
  platform: string
  interval: 'manual' | 'daily' | 'weekly' | 'monthly'
  last_run: string | null
  next_run: string | null
  status: 'active' | 'paused' | 'completed'
  quota_used_today: number
  created_at: string
  updated_at: string
}

export interface MonitorResult {
  id: string
  task_id: string
  matched_url: string
  matched_title: string | null
  similarity: number
  matched_thumbnail_url: string | null
  screenshot_path: string | null
  found_at: string
  status: 'pending_review' | 'infringing' | 'ignored' | 'whitelisted'
  action_taken: string | null
  ignore_reason: string | null
  notes: string | null
}

// P2.3 Types
export interface BrandWatch {
  id: string
  brand_name: string
  brand_logo_path: string | null
  keywords: string[] | null
  platforms: string[] | null
  is_active: boolean
  last_scan_at: string | null
  total_matches: number
  notes: string | null
  created_at: string
  updated_at: string
}

export interface BrandScanResult {
  id: string
  brand_id: string
  platform: string
  item_url: string
  item_title: string | null
  similarity: number
  thumbnail_url: string | null
  found_at: string
  status: 'pending_review' | 'infringing' | 'ignored'
  notes: string | null
}

export interface DomainWatch {
  id: string
  domain: string
  target_brand: string | null
  watch_type: 'whois' | 'typo' | 'phishing'
  is_active: boolean
  last_checked_at: string | null
  registrar: string | null
  creation_date: string | null
  expiry_date: string | null
  status_notes: string | null
  created_at: string
  updated_at: string
}

export interface CodeSimilarityResult {
  code_a: string
  code_b: string
  similarity: number
  structure_similarity: number
  keyword_similarity: number
  is_mock: boolean
  message: string
}

export interface WhitelistSuggestion {
  id: string
  pattern_url: string
  pattern_type: string
  occurrence_count: number
  last_seen_at: string | null
  suggested_at: string | null
  status: 'suggested' | 'accepted' | 'declined'
}
