import client from './client'
import type { Work, WorkListParams } from '@/types/work'

export const worksApi = {
  list: (params?: Partial<WorkListParams>) =>
    client.get('/works', { params }),

  get: (id: string) =>
    client.get(`/works/${id}`),

  create: (formData: FormData) =>
    client.post('/works', formData),

  update: (id: string, data: Partial<Work>) =>
    client.patch(`/works/${id}`, data),

  delete: (id: string) =>
    client.delete(`/works/${id}`),

  recomputeHash: (id: string) =>
    client.post(`/works/${id}/hash`),

  preview: (id: string) =>
    client.get(`/works/${id}/preview`),

  listTags: () =>
    client.get('/tags'),

  addTag: (workId: string, tag: string) =>
    client.post(`/works/${workId}/tags`, { tag }),

  removeTag: (workId: string, tagId: string) =>
    client.delete(`/works/${workId}/tags/${tagId}`),

  // Versions
  listVersions: (workId: string) =>
    client.get(`/works/${workId}/versions`),

  createVersion: (workId: string, notes?: string) =>
    client.post(`/works/${workId}/versions`, null, { params: { notes } }),

  rollback: (workId: string, versionId: string) =>
    client.post(`/works/${workId}/rollback/${versionId}`),

  // Batch
  batchEdit: (workIds: string[], data: any) =>
    client.post('/works/batch-edit', { work_ids: workIds, ...data }),

  batchDelete: (workIds: string[]) =>
    client.post('/works/batch-delete', workIds),

  // Recycle bin
  trash: (params?: any) =>
    client.get('/works', { params: { ...params, status: 'trashed' } }),

  restore: (workId: string) =>
    client.patch(`/works/${workId}`, { status: 'active' }),

  permanentDelete: (workId: string) =>
    client.delete(`/works/${workId}/permanent`),

  emptyTrash: () =>
    client.post('/works/empty-trash'),

  // Projects
  listProjects: () =>
    client.get('/projects'),

  createProject: (data: any) =>
    client.post('/projects', data),

  updateProject: (id: string, data: any) =>
    client.patch(`/projects/${id}`, data),

  deleteProject: (id: string) =>
    client.delete(`/projects/${id}`),

  assignProject: (workId: string, projectId: string) =>
    client.post(`/works/${workId}/assign-project/${projectId}`),

  // Tags suggest
  suggestTags: (query: string) =>
    client.get('/tags/suggest', { params: { query } }),

  // Global tag management
  renameTag: (oldTag: string, newTag: string) =>
    client.patch(`/tags/${encodeURIComponent(oldTag)}`, { new_tag: newTag }),

  deleteTag: (tagName: string) =>
    client.delete(`/tags/${encodeURIComponent(tagName)}`),

  // ─── Folder Import (P2) ───
  importFolder: (files: File[], autoCreateProject: boolean = true) => {
    const formData = new FormData()
    files.forEach(f => formData.append('files', f))
    formData.append('auto_create_project', String(autoCreateProject))
    return client.post('/works/import-folder', formData)
  },
}
