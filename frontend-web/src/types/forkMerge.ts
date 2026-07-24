export interface ForkMergeWork {
  id: string
  original_work_id: string
  title: string
  description?: string
  owner_id: string
  status: 'active' | 'closed' | 'archived'
  visibility: 'public' | 'private'
  base_commit_sha?: string
  created_at?: string
  updated_at?: string
  branch_count?: number
  pr_count?: number
  collaborator_count?: number
}

export interface Branch {
  id: string
  work_id: string
  name: string
  commit_id?: string
  is_default: boolean
  created_at?: string
}

export interface PullRequest {
  id: string
  work_id: string
  title: string
  description?: string
  author_id: string
  source_branch_id?: string
  target_branch_id?: string
  status: 'open' | 'merged' | 'closed' | 'rejected'
  merged_at?: string
  merge_method?: string
  conflict_detail?: Record<string, unknown>
  review_comments?: Record<string, unknown>[]
  created_at?: string
  updated_at?: string
}

export interface Collaborator {
  id: string
  work_id: string
  user_id: string
  role: 'owner' | 'collaborator' | 'contributor' | 'viewer'
  permissions?: Record<string, unknown>
  joined_at?: string
  left_at?: string
}
