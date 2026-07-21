/**
 * Module 9 v2: AI增长引擎 API 客户端
 */

import client from './client'

// ==================== AI 会话对比 ====================

export interface SessionComparison {
  session_a: {
    id: string
    tool_name: string
    model_name: string | null
    seed: number | null
    prompt: string | null
    created_at: string
  }
  session_b: {
    id: string
    tool_name: string
    model_name: string | null
    seed: number | null
    prompt: string | null
    created_at: string
  }
  differences: Record<string, {
    session_a: any
    session_b: any
  }>
}

export const aiSessionV2Api = {
  compareSessions: (workId: string, sessionAId: string, sessionBId: string) =>
    client.get<{ data: SessionComparison }>(
      `/works/${workId}/ai-sessions/${sessionAId}/compare/${sessionBId}`
    ),

  batchImport: (workId: string, imports: any[]) =>
    client.post<{ data: any }>(
      `/works/${workId}/ai-sessions/batch-import`,
      imports
    ),
}

// ==================== 成就徽章 ====================

export const achievementApi = {
  listBadges: () =>
    client.get<{ data: any[] }>('/growth/badges'),

  unlockBadge: (badgeKey: string) =>
    client.post<{ data: any }>(
      `/growth/badges/${badgeKey}/unlock`
    ),

  myAchievements: () =>
    client.get<{ data: any[] }>('/growth/achievements'),

  getLeaderboard: (params?: { creator_type?: string; period?: string; limit?: number }) =>
    client.get<{ data: any[] }>('/growth/leaderboard', { params }),

  refreshLeaderboard: (params: { creator_type: string; period?: string }) =>
    client.post<{ data: any }>('/growth/leaderboard/update', {}, { params }),
}

// ==================== 发票管理 ====================

export const invoiceApi = {
  create: (data: any) =>
    client.post<{ data: any }>('/subscriptions/invoices', data),

  listMy: (params?: { status?: string; limit?: number; offset?: number }) =>
    client.get<{ data: any[] }>('/subscriptions/invoices', { params }),

  markPaid: (invoiceId: string) =>
    client.post<{ data: any }>('/subscriptions/invoices/mark-paid', {
      invoice_id: invoiceId,
    }),

  getAutoRenewal: (subscriberId: string) =>
    client.get<{ data: any }>(
      `/subscriptions/auto-renewal/${subscriberId}`
    ),

  updateAutoRenewal: (subscriberId: string, enabled: boolean) =>
    client.patch<{ data: any }>(
      `/subscriptions/auto-renewal/${subscriberId}`,
      { enabled }
    ),

  processRenewal: (subscriberId: string, success: boolean) =>
    client.post<{ data: any }>('/subscriptions/auto-renewal/process', {
      subscriber_id: subscriberId,
      success,
    }),
}

// ==================== 字幕批量管理 ====================

export const subtitleBatchApi = {
  batchCreate: (videoId: string, languages: string[]) =>
    client.post<{ data: any }>(
      `/videos/${videoId}/subtitles/batch`,
      { languages }
    ),

  translateSubtitle: (videoId: string, subtitleId: string, targetLang: string) =>
    client.post<{ data: any }>(
      `/videos/${videoId}/subtitles/${subtitleId}/translate`,
      { target_lang: targetLang }
    ),
}
