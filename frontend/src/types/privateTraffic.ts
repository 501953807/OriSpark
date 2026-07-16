/** 私域流量类型定义 */

export interface SubscriptionLink {
  id: string
  platform: string
  url: string
  subscriber_count: number
  monthly_revenue: number
  currency: string
  total_monthly: number
}

export interface FanCommunity {
  id: string
  platform: string
  name: string
  invite_url?: string
  member_count: number
  tags?: string[]
  description?: string
}

export interface FunnelSummary {
  total_public_views: number
  total_profile_clicks: number
  total_link_clicks: number
  total_converted: number
  overall_conversion_rate: number
  by_platform: Array<{
    platform: string
    views: number
    clicks: number
    links: number
    converted: number
    profile_ctr: number
    link_ctr: number
    conv_rate: number
  }>
}
