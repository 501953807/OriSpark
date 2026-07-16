import { request } from '@/api/client'
import type { SubscriptionLink, FanCommunity, FunnelSummary } from '@/types/privateTraffic'

export function listSubscriptions() {
  return request.get('/private-traffic/subscriptions').then(res => res.data as SubscriptionLink[])
}

export function addSubscription(data: { platform: string; url: string; subscriber_count?: number; monthly_revenue?: number }) {
  return request.post('/private-traffic/subscriptions', data).then(res => res.data)
}

export function updateSubscription(id: string, data: { subscriber_count: number }) {
  return request.patch(`/private-traffic/subscriptions/${id}`, data).then(res => res.data)
}

export function listCommunities() {
  return request.get('/private-traffic/communities').then(res => res.data as FanCommunity[])
}

export function addCommunity(data: { platform: string; name: string; invite_url?: string; member_count?: number; tags?: string[] }) {
  return request.post('/private-traffic/communities', data).then(res => res.data)
}

export function getFunnelSummary() {
  return request.get('/private-traffic/funnel-summary').then(res => res.data as FunnelSummary)
}

export function addFunnelEntry(data: { source_platform: string; public_views: number; profile_clicks: number; link_clicks: number; converted_subscribers: number }) {
  return request.post('/private-traffic/funnel', data).then(res => res.data)
}
