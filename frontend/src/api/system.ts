import client from './client'

export const systemApi = {
  settings: () =>
    client.get('/system/settings'),

  updateSettings: (data: Record<string, string>) =>
    client.patch('/system/settings', data),

  // Backup (P2.7.3-P2.7.4 enhanced)
  backup: (encrypted: boolean = false, incremental: boolean = false, includeFiles: boolean = true) =>
    client.post('/system/backup', null, { params: { include_files: includeFiles, encrypted, incremental } }),

  backups: () =>
    client.get('/system/backups'),

  deleteBackup: (id: string) =>
    client.delete(`/system/backups/${id}`),

  restore: (backupId: string) =>
    client.post('/system/restore', null, { params: { backup_id: backupId } }),

  backupSchedule: () =>
    client.get('/system/backup/schedule'),

  createBackupSchedule: (cron: string, encrypted: boolean = true) =>
    client.post('/system/backup/schedule', null, { params: { cron_expr: cron, encrypted } }),

  auditLogs: (params?: any) =>
    client.get('/system/audit-logs', { params }),

  storage: () =>
    client.get('/system/storage'),

  // Health Dashboard (P2.7.1-P2.7.2)
  healthDashboard: () =>
    client.get('/system/health/dashboard'),

  serviceStatus: () =>
    client.get('/system/health/services'),

  // -- 统一字典数据中心 --
  dictGroups: (module?: string) =>
    client.get('/system/dict/groups', { params: module ? { module } : {} }),

  dictGroupItems: (groupKey: string) =>
    client.get(`/system/dict/groups/${groupKey}`),

  dictItemsBulk: (keys?: string[]) =>
    client.get('/system/dict/items', { params: keys ? { keys: keys.join(',') } : {} }),

  updateDictItem: (id: string, data: any) =>
    client.patch(`/system/dict/items/${id}`, data),

  deleteDictItem: (id: string) =>
    client.delete(`/system/dict/items/${id}`),

  // -- 通知中心 --
  notifications: (params?: any) =>
    client.get('/notifications', { params }),

  unreadCount: () =>
    client.get('/notifications/unread-count'),

  markRead: (id: string) =>
    client.patch(`/notifications/${id}/read`),

  markAllRead: () =>
    client.post('/notifications/read-all'),

  // -- Email Notification (P2.7.5) --
  testEmail: (recipient: string) =>
    client.post('/system/notification/email/test', null, { params: { recipient } }),

  sendEmail: (recipient: string, subject: string, body: string) =>
    client.post('/system/notification/email/send', null, { params: { recipient, subject, body } }),

  // -- WeChat Notification (P2.7.6) --
  testWechat: () =>
    client.post('/system/notification/wechat/test'),

  // -- Plugin Framework (P2.7.8) --
  plugins: () =>
    client.get('/system/plugins'),

  registerPlugin: (data: any) =>
    client.post('/system/plugins', data),

  updatePlugin: (id: string, data: any) =>
    client.patch(`/system/plugins/${id}`, data),

  deletePlugin: (id: string) =>
    client.delete(`/system/plugins/${id}`),

  // -- Email Verification (P2.7.11) --
  sendVerificationCode: (email: string) =>
    client.post('/system/email/verify/send', null, { params: { email } }),

  confirmVerificationCode: (email: string, code: string) =>
    client.post('/system/email/verify/confirm', null, { params: { email, code } }),

  // -- Password Reset (P2.7.12) --
  requestPasswordReset: (email: string) =>
    client.post('/system/password/reset/request', null, { params: { email } }),

  confirmPasswordReset: (token: string, newPassword: string) =>
    client.post('/system/password/reset/confirm', null, { params: { token, new_password: newPassword } }),

  // -- Password Strength (P2.7.13) --
  checkPasswordStrength: (password: string) =>
    client.post('/system/password/check-strength', null, { params: { password } }),

  // -- Avatar Upload (P2.7.14) --
  uploadAvatar: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return client.post('/system/avatar/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  // -- Data Export (P2.7.14) --
  exportAllData: (format: string = 'json') =>
    client.get('/system/export/all', { params: { format } }),

  // -- Danger Zone (P2.7.15) --
  deleteAccount: (confirmation: string) =>
    client.post('/system/danger/delete-account', null, { params: { confirmation } }),

  clearAllData: (confirmation: string) =>
    client.post('/system/danger/clear-data', null, { params: { confirmation } }),

  // -- MCP Server (P2.6.7) --
  mcpInfo: () =>
    client.get('/mcp'),

  // -- OAuth --
  googleLoginUrl: () =>
    client.get('/auth/google/url'),

  wechatQrcode: () =>
    client.get('/auth/wechat/qrcode'),

  douyinLoginUrl: () =>
    client.get('/auth/douyin/url'),

  bindProvider: (provider: string, data: any) =>
    client.post(`/auth/bind/${provider}`, data),

  unbindProvider: (provider: string) =>
    client.delete(`/auth/unbind/${provider}`),

  // ─── TOTP 2FA (P2-8) ───
  setupTOTP: () =>
    client.post('/auth/totp/setup'),

  verifyTOTP: (code: string) =>
    client.post('/auth/totp/verify', null, { params: { code } }),

  totpStatus: () =>
    client.get('/auth/totp/status'),

  disableTOTP: () =>
    client.post('/auth/totp/disable'),

  // ─── Sessions ───
  getSessions: () =>
    client.get('/system/sessions'),

  revokeSession: (sessionId: string) =>
    client.delete(`/system/sessions/${sessionId}`),

  // ─── Notification Preferences ───
  updateNotifPrefs: (data: any) =>
    client.post('/system/notification/prefs', data),

  // ─── Onboarding (P2) ───
  completeOnboarding: (data: { creator_type: string }) =>
    client.post('/auth/complete-onboarding', data),

  onboardingStatus: () =>
    client.get('/system/onboarding-status'),

  // ─── Metadata Templates (P2-4) ───
  metadataTemplates: (params?: { is_default?: boolean }) =>
    client.get('/metadata-templates', { params }),

  createMetadataTemplate: (data: any) =>
    client.post('/metadata-templates', data),

  updateMetadataTemplate: (id: string, data: any) =>
    client.patch(`/metadata-templates/${id}`, data),

  deleteMetadataTemplate: (id: string) =>
    client.delete(`/metadata-templates/${id}`),

  templateFields: (id: string) =>
    client.get(`/metadata-templates/${id}/fields`),

  addTemplateField: (templateId: string, data: any) =>
    client.post(`/metadata-templates/${templateId}/fields`, data),

  updateTemplateField: (templateId: string, fieldId: string, data: any) =>
    client.patch(`/metadata-templates/${templateId}/fields/${fieldId}`, data),

  deleteTemplateField: (templateId: string, fieldId: string) =>
    client.delete(`/metadata-templates/${templateId}/fields/${fieldId}`),

  applyTemplate: (templateId: string, workId: string) =>
    client.post(`/metadata-templates/${templateId}/apply`, null, { params: { work_id: workId } }),

  // ─── Watermark Presets (P2-5) ───
  watermarkPresets: (params?: { watermark_type?: string; is_default?: boolean }) =>
    client.get('/watermark/presets', { params }),

  createWatermarkPreset: (data: any) =>
    client.post('/watermark/presets', data),

  updateWatermarkPreset: (id: string, data: any) =>
    client.patch(`/watermark/presets/${id}`, data),

  deleteWatermarkPreset: (id: string) =>
    client.delete(`/watermark/presets/${id}`),

  applyWatermark: (workId: string, presetId: string) =>
    client.post('/watermark/apply', null, { params: { work_id: workId, preset_id: presetId } }),

  previewWatermark: (config: any, imagePath: string) =>
    client.post('/watermark/preview', null, { params: { config: JSON.stringify(config), image_path: imagePath } }),

  // ─── Work Variants (P3-4) ───
  variantGroups: (workId?: string) =>
    client.get('/work-variants/groups', { params: workId ? { work_id: workId } : {} }),

  variantGroupDetail: (groupId: string) =>
    client.get(`/work-variants/groups/${groupId}`),

  createVariantGroup: (data: any) =>
    client.post('/work-variants/groups', data),

  updateVariantGroup: (id: string, data: any) =>
    client.patch(`/work-variants/groups/${id}`, data),

  deleteVariantGroup: (id: string) =>
    client.delete(`/work-variants/groups/${id}`),

  groupVariants: (groupId: string) =>
    client.get(`/work-variants/groups/${groupId}/variants`),

  addVariant: (groupId: string, data: any) =>
    client.post(`/work-variants/groups/${groupId}/variants`, data),

  updateVariant: (groupId: string, variantId: string, data: any) =>
    client.patch(`/work-variants/groups/${groupId}/variants/${variantId}`, data),

  deleteVariant: (groupId: string, variantId: string) =>
    client.delete(`/work-variants/groups/${groupId}/variants/${variantId}`),

  generateVariants: (workId: string, groupId: string) =>
    client.post(`/work-variants/${workId}/generate`, null, { params: { group_id: groupId } }),

  // ─── RAW Processing (P2-1) ───
  processRaw: (workId: string, outputFormat: string = 'jpeg') =>
    client.post(`/works/${workId}/process-raw`, null, { params: { output_format: outputFormat } }),

  // ─── Culling (P2-3) ───
  batchCull: (workIds: string[], action: string) => {
    const cullStatus = action === 'keep' ? 'pass' : 'fail'
    return client.post('/works/cull-batch', { work_ids: workIds, cull_status: cullStatus })
  },

  cullWork: (workId: string, action: string) =>
    client.patch(`/works/${workId}/cull`, { action }),

  // ─── Subscription Tiers ───
  subscriptionTiers: (isActive?: boolean) =>
    client.get('/subscription/tiers', { params: isActive !== undefined ? { is_active: isActive } : {} }),

  createSubscriptionTier: (data: any) =>
    client.post('/subscription/tiers', data),

  updateSubscriptionTier: (id: string, data: any) =>
    client.patch(`/subscription/tiers/${id}`, data),

  deleteSubscriptionTier: (id: string) =>
    client.delete(`/subscription/tiers/${id}`),

  subscriptionSubscribers: (params?: any) =>
    client.get('/subscription/subscribers', { params }),

  subscribe: (data: { user_id: string; tier_id: string }) =>
    client.post('/subscription/subscribe', data),

  cancelSubscription: (data: { user_id: string }) =>
    client.post('/subscription/cancel', data),

  // ─── Commission ───
  commissions: (params?: { user_id?: string; status?: string }) =>
    client.get('/commission/projects', { params }),

  createCommission: (data: any) =>
    client.post('/commission/projects', data),

  updateCommission: (id: string, data: any) =>
    client.put(`/commission/projects/${id}`, data),

  deleteCommission: (id: string) =>
    client.delete(`/commission/projects/${id}`),

  commissionOrders: (projectId: string, params?: { status?: string }) =>
    client.get(`/commission/projects/${projectId}/orders`, { params }),

  createCommissionOrder: (projectId: string, data: { order_type: string; amount: number }) =>
    client.post(`/commission/projects/${projectId}/orders`, data),

  commissionMessages: (projectId: string) =>
    client.get(`/commission/projects/${projectId}/messages`),

  createCommissionMessage: (projectId: string, data: { sender_id: string; content: string }) =>
    client.post(`/commission/projects/${projectId}/messages`, data),

  // ─── C2PA ───
  generateC2PA: (workId: string) =>
    client.post(`/notary/c2pa/${workId}/generate`),

  verifyC2PA: (workId: string) =>
    client.get(`/notary/verify/c2pa/${workId}`),

  // ─── Platform Config ───
  platformConfig: () =>
    client.get('/system/platform-config'),

  updatePlatformConfig: (data: any) =>
    client.patch('/system/platform-config', data),

  // ─── Auth ───
  authMe: () =>
    client.get('/auth/me'),
}
