import client from './client'
import type { EnforcementAction, EnforcementTemplate, EvidencePackage, FromWorkResponse } from '@/types/enforcement'

export const enforcementApi = {
  // Bridge endpoint
  createFromWork: (workId: string) =>
    client.post<FromWorkResponse>(`/enforcement/actions/from-work/${workId}`),

  // List actions for a work
  listByWork: (workId: string) =>
    client.get<{ data: EnforcementAction[] }>(`/enforcement/actions/by-work/${workId}`),

  // Get single action
  getAction: (actionId: string) =>
    client.get<{ data: EnforcementAction }>(`/enforcement/actions/${actionId}`),

  // Update action
  updateAction: (actionId: string, data: Partial<EnforcementAction>) =>
    client.patch<{ data: EnforcementAction }>(`/enforcement/actions/${actionId}`, data),

  // Gather evidence
  gatherEvidence: (actionId: string) =>
    client.post<{ data: EvidencePackage }>(`/enforcement/actions/${actionId}/evidence`),

  // Submit complaint
  submitComplaint: (actionId: string) =>
    client.post(`/enforcement/actions/${actionId}/submit`),

  // Templates
  listTemplates: (params?: { platform?: string; jurisdiction?: string }) =>
    client.get<EnforcementTemplate[]>('/enforcement/templates', { params }),

  // Seed templates
  seedTemplates: () =>
    client.post('/enforcement/templates/seed'),
}
