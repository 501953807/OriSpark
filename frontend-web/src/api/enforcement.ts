import client from './client'
import type { EnforcementAction, EnforcementTemplate, EvidencePackage, FromWorkResponse } from '@/types/enforcement'

export const enforcementApi = {
  // Bridge endpoint: POST /enforcement/actions/from-work/{workId}
  createFromWork: (workId: string) =>
    client.post<FromWorkResponse>(`/enforcement/actions/from-work/${workId}`),

  // List actions for a work: GET /enforcement/actions/by-work/{workId}
  listByWork: (workId: string) =>
    client.get<EnforcementAction[]>(`/enforcement/actions/by-work/${workId}`),

  // Get single action: GET /enforcement/actions/{actionId}
  getAction: (actionId: string) =>
    client.get<EnforcementAction>(`/enforcement/actions/${actionId}`),

  // Update action: PATCH /enforcement/actions/{actionId}
  updateAction: (actionId: string, data: Partial<EnforcementAction>) =>
    client.patch<EnforcementAction>(`/enforcement/actions/${actionId}`, data),

  // Gather evidence: POST /enforcement/actions/{actionId}/evidence
  gatherEvidence: (actionId: string) =>
    client.post<EvidencePackage>(`/enforcement/actions/${actionId}/evidence`),

  // Submit complaint: POST /enforcement/actions/{actionId}/submit
  submitComplaint: (actionId: string) =>
    client.post(`/enforcement/actions/${actionId}/submit`),

  // Templates: GET /enforcement/templates
  listTemplates: (params?: { platform?: string; jurisdiction?: string }) =>
    client.get<EnforcementTemplate[]>('/enforcement/templates', { params }),

  // Seed templates: POST /enforcement/templates/seed
  seedTemplates: () =>
    client.post('/enforcement/templates/seed'),
}
