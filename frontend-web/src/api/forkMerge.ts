import client from './client'
import type { ForkMergeWork, Branch, PullRequest, Collaborator } from '@/types/forkMerge'

export const forkMergeApi = {
  listWorks: (params?: { status?: string; visibility?: string }) =>
    client.get<{ data: ForkMergeWork[] }>('/fork-merge/works', { params }),
  createWork: (data: { original_work_id: string; title?: string; description?: string; visibility?: string }) =>
    client.post<{ data: ForkMergeWork }>('/fork-merge/works', data),
  getWork: (id: string) =>
    client.get<{ data: ForkMergeWork }>(`/fork-merge/works/${id}`),
  updateWork: (id: string, data: Partial<ForkMergeWork>) =>
    client.patch<{ data: ForkMergeWork }>(`/fork-merge/works/${id}`, data),
  deleteWork: (id: string) =>
    client.delete<{ data: unknown }>(`/fork-merge/works/${id}`),

  listBranches: (workId: string) =>
    client.get<{ data: Branch[] }>(`/fork-merge/works/${workId}/branches`),
  createBranch: (workId: string, data: { name: string }) =>
    client.post<{ data: Branch }>(`/fork-merge/works/${workId}/branches`, data),

  listPRs: (workId: string, params?: { status?: string }) =>
    client.get<{ data: PullRequest[] }>(`/fork-merge/works/${workId}/pull-requests`, { params }),
  createPR: (workId: string, data: { title: string; description?: string; source_branch_id: string; target_branch_id: string }) =>
    client.post<{ data: PullRequest }>(`/fork-merge/works/${workId}/pull-requests`, data),
  mergePR: (workId: string, prId: string, data?: { merge_method?: string }) =>
    client.patch<{ data: PullRequest }>(`/fork-merge/works/${workId}/pull-requests/${prId}/merge`, data),

  listCollaborators: (workId: string) =>
    client.get<{ data: Collaborator[] }>(`/fork-merge/works/${workId}/collaborators`),
  addCollaborator: (workId: string, data: { user_id: string; role?: string }) =>
    client.post<{ data: Collaborator }>(`/fork-merge/works/${workId}/collaborators`, data),
}
