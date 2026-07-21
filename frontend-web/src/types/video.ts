export type FingerprintStatus = 'pending' | 'processing' | 'completed' | 'failed'
export type PlatformType = 'bilibili' | 'douyin' | 'youtube' | 'wechat'

export interface VideoWork {
  id: string
  work_id: string
  title: string
  duration_seconds?: number
  format?: string
  file_size?: number
  thumbnail_path?: string
  fingerprint_status: FingerprintStatus
  match_count?: number
  created_at?: string
}

export interface VideoFingerprintResult {
  video_id: string
  status: string
  frames_extracted?: number
  phash_generated?: boolean
  matches_found?: number
}

export interface VideoMatchResult {
  match_id: string
  similarity: number
  matched_frames: number
  first_match_frame: number
  source_url?: string
}

export interface PlatformDistribution {
  platform: PlatformType
  status: 'idle' | 'uploading' | 'published' | 'failed'
  published_url?: string
  view_count?: number
  like_count?: number
}

export interface VideoStats {
  total_videos: number
  total_plays: number
  fingerprint_scans: number
  infringement_count: number
  monthly_revenue: number
}

export interface VideoFilters {
  fingerprint_status?: FingerprintStatus | string
  format?: string
  page?: number
  page_size?: number
}

export interface VideoListResult<T = VideoWork> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// --- Fingerprint Config types ---

export interface VideoFingerprintConfig {
  id: string
  name: string
  algorithm: string
  frame_interval: number
  threshold: number
  is_active: boolean
  settings: Record<string, unknown>
  created_at: string | null
  updated_at: string | null
}

export interface CreateConfigPayload {
  name: string
  algorithm?: string
  frame_interval?: number
  threshold?: number
  is_active?: boolean
  settings?: Record<string, unknown>
}

export interface UpdateConfigPayload {
  name?: string
  algorithm?: string
  frame_interval?: number
  threshold?: number
  is_active?: boolean
  settings?: Record<string, unknown>
}

// --- Frame Fingerprint types ---

export interface VideoFrameFingerprint {
  id: string
  work_id: string
  config_id: string | null
  frame_hash: string
  timestamp_ms: number
  frame_index: number
  similarity_score: number | null
  matched_work_id: string | null
  created_at: string | null
}

export interface CreateFramePayload {
  work_id: string
  frame_hash: string
  config_id?: string
  timestamp_ms?: number
  frame_index?: number
  similarity_score?: number
  matched_work_id?: string
}
