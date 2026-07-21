// ── AI Session Types ───────────────────────────────────────────────

export interface AiSession {
  id: string
  work_id: string
  tool_name: string
  tool_version?: string | null
  prompt?: string | null
  seed?: number | null
  parameters?: Record<string, unknown> | null
  negative_prompt?: string | null
  model_name?: string | null
  lora_names?: string[] | null
  output_images?: number | string[] | null
  human_interventions?: string[] | null
  created_at: string | null
  updated_at?: string | null
}

export interface AiSessionCreateInput {
  tool_name: string
  prompt?: string
  tool_version?: string
  seed?: number
  parameters?: Record<string, unknown>
  negative_prompt?: string
  model_name?: string
  lora_names?: string[]
  output_images?: number | string[]
  human_interventions?: string[]
}

// ── Folder Import ──────────────────────────────────────────────────

export interface ImportFolderResult {
  imported: number
  skipped_duplicate: number
  failed: number
  errors?: Array<{ filename: string; error: string }>
}
