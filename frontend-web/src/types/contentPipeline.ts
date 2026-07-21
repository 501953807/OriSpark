/** 多平台内容分发流水线类型定义 */

export interface PlatformAccount {
  id: string
  platform: string
  account_name: string
  account_id?: string
  follower_count: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface PublishSchedule {
  id: string
  title: string
  description?: string
  platforms: Array<{platform: string; account_id?: string; status: string}>
  scheduled_at: string
  is_recurring: boolean
  recurring_pattern?: string
  status: string
  published_at?: string
  error_message?: string
}

export interface SimulateResult {
  platform: string
  platform_name: string
  recommended_cover: string
  max_tags: number
  title_adapted: string
  tags_count: number
  tags_ok: boolean
}

export interface PublishStats {
  total_schedules: number
  scheduled: number
  published: number
  failed: number
  recent_7d_success: number
}
