import client from './client'
import type {
  CapabilityDimension,
  AssessmentResult,
  SkillPremiumResult,
  AIPredictionResult,
  StageRecommendation,
} from '@/types/capability'

export function listDimensions() {
  return client.get('/capability/dimensions').then(res => res.data as CapabilityDimension[])
}

export function createAssessment(dimensionScores: Record<string, number>) {
  return client.post('/capability/assessments', { dimension_scores: dimensionScores })
    .then(res => res.data as AssessmentResult)
}

export function calcPremium(skills: string[], yearsExperience: number, workCount: number) {
  return client.post('/capability/premium', {
    skills,
    years_experience: yearsExperience,
    work_count: workCount,
  }).then(res => res.data as SkillPremiumResult)
}

export function predictAIRisk(currentSkills: string[], workType: string, experienceYears: number) {
  return client.post('/capability/ai-risk', {
    current_skills: currentSkills,
    work_type: workType,
    experience_years: experienceYears,
  }).then(res => res.data as AIPredictionResult)
}

export function getStageRecommendation(score: number) {
  return client.get('/capability/stage-recommendation', { params: { score } })
    .then(res => res.data as StageRecommendation)
}
