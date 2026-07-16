/** 版权登记指南类型定义 */

export interface GuideStep {
  step: number
  title: string
  description: string
  required_files: string[]
}

export interface RegistrationGuide {
  id: string
  work_type: string
  title_zh: string
  steps: GuideStep[]
  estimated_days: number
  estimated_fee_yuan: number
}

export interface CopyrightRegistration {
  id: string
  title: string
  work_type: string
  registration_type: string
  status: string
  application_number?: string
  registration_date?: string
  fee_yuan?: number
  notes?: string
  created_at: string
  updated_at: string
}

export interface RegistrationSummary {
  total: number
  by_status: Record<string, number>
  by_type: Record<string, number>
  total_fees_yuan: number
}
