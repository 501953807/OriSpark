export interface WorkTag {
  id: string
  tag: string
  work_id: string
}

export interface Work {
  id: string
  title: string
  file_name: string
  file_path: string
  file_size: number
  file_type: 'image' | 'audio' | 'video' | 'document' | 'design' | 'code' | 'other'
  file_extension: string
  mime_type: string | null
  sha256: string | null
  md5: string | null
  description: string | null
  project_id: string | null
  project?: { name: string; id: string; work_count?: number } | null
  status: 'active' | 'trashed' | 'archived'
  is_verified: boolean
  verified_date: string | null
  thumbnail_path: string | null
  thumbnail_url: string | null
  file_url: string | null
  width: number | null
  height: number | null
  duration: number | null
  custom_metadata: Record<string, any> | null
  exif_data: Record<string, any> | null
  tags: WorkTag[]
  import_mode: string
  creator_type: string  // illustrator | photographer | video | craftsman | musician | writer
  rights: Record<string, any> | null
  license_type: string | null
  created_at: string
  imported_at: string
  updated_at: string
  verified_status?: string | null
  synopsis?: string | null
  completion_date?: string | null
  current_stage?: string | null
  copyright_year?: number | null
  // Culling fields
  cull_status?: 'pending' | 'pass' | 'fail' | 'hold' | null
  cull_rating?: number | null
  color_label?: string | null
  // AI-assisted creation fields
  ai_assisted?: boolean
  ai_tools_used?: Array<{ name: string; version?: string }>
}

export interface WorkListParams {
  page?: number
  page_size?: number
  file_type?: string
  status?: string
  tag?: string
  search?: string
  project_id?: string
  stage?: string
  license_type?: string
  sort_by?: string
  sort_order?: string
}
