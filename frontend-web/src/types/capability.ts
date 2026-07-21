/** 创作者能力评估类型定义 */

export interface CapabilityDimension {
  id: string
  dimension_key: string
  name_zh: string
  description?: string
  weight: number
  is_active: boolean
}

export interface AssessmentResult {
  id: string
  user_id: string
  overall_score: number | null
  dimension_scores: Record<string, number>
  skill_premium_percent: number | null
  ai_risk_level: 'low' | 'medium' | 'high' | 'unknown'
  ai_risk_description: string
  created_at: string
}

export interface SkillPremiumResult {
  premium_percent: number
  breakdown: {
    base: number
    diversity: number
    high_score: number
  }
}

export interface AIPredictionResult {
  risk_level: 'low' | 'medium' | 'high'
  risk_score: number
  vulnerable_skills: string[]
  moat_building_tips: string[]
}

export interface StageRecommendation {
  stage_key: string
  stage_name_zh: string
  min_score: number
  max_score: number | null
  recommended_skills?: string[]
  milestone_tasks?: string[]
}
