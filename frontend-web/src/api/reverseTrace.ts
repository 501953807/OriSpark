/**分发回流引擎 API 客户端.*/

import request from '@/utils/request'

export interface TraceLink {
  id: string
  work_id: string
  user_id: string
  platform_code: string
  short_code: string
  original_url: string
  redirect_url: string
  is_active: boolean
  click_count: number
  expire_at: string | null
  utm_source: string | null
  utm_medium: string | null
  utm_campaign: string | null
  created_at: string | null
  updated_at: string | null
}

export interface TraceEvent {
  id: string
  link_id: string
  event_type: string
  ip_address: string | null
  geo_country: string | null
  geo_region: string | null
  geo_city: string | null
  device_type: string | null
  converted: boolean
  conversion_value: number | null
  created_at: string | null
}

export interface AttributionSummary {
  link_id: string
  total_clicks: number
  unique_visitors: number
  event_breakdown: Record<string, number>
  top_countries: Array<{ country: string; count: number }>
  conversion_rate: number
  total_conversions: number
  total_conversion_value: number
}

const reverseTraceApi = {
  /**创建可信短链 */
  create(data: Partial<TraceLink>) {
    return request.post('/trace/links', data)
  },

  /**列出短链 */
  list(params?: { platform_code?: string; is_active?: boolean }) {
    return request.get('/trace/links', { params })
  },

  /**获取链接详情 */
  getById(id: string) {
    return request.get(`/trace/links/${id}`)
  },

  /**更新链接 */
  update(id: string, data: Partial<TraceLink>) {
    return request.patch(`/trace/links/${id}`, data)
  },

  /**删除链接 */
  delete(id: string) {
    return request.delete(`/trace/links/${id}`)
  },

  /**记录归因事件 */
  recordEvent(data: {
    link_id: string
    event_type: string
    ip_address?: string
    geo_country?: string
    converted?: boolean
    conversion_value?: number
  }) {
    return request.post('/trace/events', data)
  },

  /**归因分析 */
  getAnalytics(linkId: string) {
    return request.get(`/trace/analytics/${linkId}`)
  },
}

export default reverseTraceApi
