// useProductDesigner.ts — 设计转产品向导状态管理

// 7-step wizard state persisted across navigation and page refresh
import { ref, readonly } from 'vue'

export interface DesignerStep {
  step: number
  completed: boolean
  data: Record<string, unknown>
}

export interface DesignerState {
  // Step 1: Select work
  work_id: string | null
  work_data: Record<string, unknown> | null

  // Step 2: Select monetization path
  monetization_path: string

  // Step 3: Select product category/template
  product_category_id: string
  product_template: Record<string, unknown> | null

  // Step 4: Spec validation results
  spec_result: Record<string, unknown> | null
  compatible_templates: Array<{
    template_id: string
    name_zh: string
    compatibility_score: number
    spec_result: string
    min_required_px: string
    current_meets: boolean
  }>
  remediation_suggestions: Array<{
    type: string
    description: string
    current?: string
    required?: string
    scale_factor?: string
  }>

  // Step 5: Preview
  mockup_url: string | null
  mockup_style: 'canvas' | 'printful' | 'ai'

  // Step 6: Pricing
  cost: number
  price: number
  profit: number
  ai_suggested_price_min: number
  ai_suggested_price_max: number

  // Step 7: Create
  title: string
  description: string
  platform: string
  status: 'draft' | 'active'

  // Overall
  current_step: number
  completed_steps: number
  saved: boolean
}

const DEFAULT_STATE: DesignerState = {
  work_id: null,
  work_data: null,
  monetization_path: 'pod',
  product_category_id: '',
  product_template: null,
  spec_result: null,
  compatible_templates: [],
  remediation_suggestions: [],
  mockup_url: null,
  mockup_style: 'canvas',
  cost: 0,
  price: 0,
  profit: 0,
  ai_suggested_price_min: 0,
  ai_suggested_price_max: 0,
  title: '',
  description: '',
  platform: '',
  status: 'draft',
  current_step: 1,
  completed_steps: 0,
  saved: false,
}

const state = ref<DesignerState>({ ...DEFAULT_STATE })

const STORAGE_KEY = 'product-designer-state'

function saveState() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state.value))
    state.value.saved = true
  } catch {
    // Storage full or unavailable
  }
}

function loadState(): Partial<DesignerState> | null {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      const parsed = JSON.parse(saved)
      // Validate basic structure
      if (parsed && typeof parsed === 'object' && parsed.current_step) {
        return parsed
      }
    }
  } catch {
    // Corrupted data
  }
  return null
}

function clearState() {
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch {
    // ignore
  }
  state.value = { ...DEFAULT_STATE }
}

export function useProductDesigner() {
  // Initialize from localStorage
  const saved = loadState()
  if (saved) {
    state.value = { ...DEFAULT_STATE, ...saved }
  }

  function setStep(step: number) {
    state.value.current_step = step
    saveState()
  }

  function completeStep(step: number) {
    state.value.completed_steps = Math.max(state.value.completed_steps, step)
    saveState()
  }

  function updateField<K extends keyof DesignerState>(key: K, value: DesignerState[K]) {
    ;(state.value as any)[key] = value
    saveState()
  }

  function reset() {
    clearState()
  }

  function getProgress(): number {
    return Math.round((state.value.completed_steps / 7) * 100)
  }

  return {
    state: readonly(state),
    setStep,
    completeStep,
    updateField,
    reset,
    getProgress,
  }
}
