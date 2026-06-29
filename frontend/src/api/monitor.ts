import client from './client'

export const monitorApi = {
  tasks: (params?: any) =>
    client.get('/monitor/tasks', { params }),

  createTask: (data: { work_id: string; platform: string; search_type: string; interval?: string }) =>
    client.post('/monitor/tasks', data),

  scan: (taskId: string) =>
    client.post(`/monitor/tasks/${taskId}/scan`),

  batchScan: (workIds: string[], platform: string) =>
    client.post('/monitor/scan', { work_ids: workIds, platform }),

  results: (params?: any) =>
    client.get('/monitor/results', { params }),

  updateResult: (id: string, data: any) =>
    client.patch(`/monitor/results/${id}`, data),

  generateEvidence: (resultId: string, data: { work_id: string; result_ids: string[]; package_type: string }) =>
    client.post(`/monitor/results/${resultId}/evidence`, data),

  quota: () =>
    client.get('/monitor/quota'),

  // P2.3: Fingerprints
  computeFingerprints: (workId: string, hashTypes?: string[]) =>
    client.post('/monitor/fingerprints', { work_id: workId, hash_types: hashTypes || ['dhash', 'phash'] }),

  compareFingerprints: (workIdA: string, workIdB: string, hashType?: string) =>
    client.post('/monitor/fingerprints/compare', { work_id_a: workIdA, work_id_b: workIdB, hash_type: hashType || 'dhash' }),

  // P2.3: Brand watches
  brandWatches: () =>
    client.get('/monitor/brand-watches'),

  createBrandWatch: (data: { brand_name: string; keywords: string[]; platforms: string[]; notes?: string }) =>
    client.post('/monitor/brand-watches', data),

  updateBrandWatch: (id: string, data: any) =>
    client.patch(`/monitor/brand-watches/${id}`, data),

  deleteBrandWatch: (id: string) =>
    client.delete(`/monitor/brand-watches/${id}`),

  brandScan: (brandId: string) =>
    client.post(`/monitor/brands/${brandId}/scan`),

  brandResults: (brandId: string, params?: any) =>
    client.get(`/monitor/brands/${brandId}/results`, { params }),

  // P2.3: Domain watches
  domainWatches: () =>
    client.get('/monitor/domains/watch'),

  registerDomainWatch: (data: { domain: string; target_brand?: string; watch_type?: string }) =>
    client.post('/monitor/domains/watch', data),

  deleteDomainWatch: (id: string) =>
    client.delete(`/monitor/domains/watch/${id}`),

  // P2.3: DMCA template
  dmcaTemplate: (workId: string) =>
    client.get(`/monitor/evidence/dmca/${workId}`),

  // P2.3: Code similarity
  checkCodeSimilarity: (codeA: string, codeB: string, language?: string) =>
    client.post('/monitor/check/code', { code_a: codeA, code_b: codeB, language: language || 'python' }),

  // P2.3: Whitelist suggestions
  whitelistSuggestions: () =>
    client.get('/monitor/whitelist-suggestions'),

  whitelistAction: (suggestionId: string, action: string) =>
    client.post('/monitor/whitelist-suggestions/action', { suggestion_id: suggestionId, action }),
}
