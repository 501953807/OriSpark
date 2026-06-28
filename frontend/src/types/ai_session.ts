export interface AiSession {
  id: string
  work_id: string
  tool_name: string
  tool_version?: string
  prompt: string
  seed?: number | null
  model_name?: string
  created_at: string | null
}

export interface AiSessionCreate {
  tool_name: string
  tool_version?: string
  prompt: string
  prompt_history?: unknown[]
  seed?: number | null
  parameters?: Record<string, unknown>
  negative_prompt?: string
  model_name?: string
  lora_names?: string[]
  output_images?: string[]
  human_interventions?: unknown[]
}
