import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api/capability'
import type { CapabilityDimension, AssessmentResult, AIPredictionResult, StageRecommendation } from '@/types/capability'

export const useCapabilityStore = defineStore('capability', () => {
  const dimensions = ref<CapabilityDimension[]>([])
  const assessment = ref<AssessmentResult | null>(null)
  const aiPrediction = ref<AIPredictionResult | null>(null)
  const stageRec = ref<StageRecommendation | null>(null)
  const loading = ref(false)

  async function loadDimensions() {
    loading.value = true
    try {
      dimensions.value = await api.listDimensions()
    } finally {
      loading.value = false
    }
  }

  async function submitAssessment(scores: Record<string, number>): Promise<AssessmentResult> {
    return api.createAssessment(scores)
  }

  async function runAIRisk(skills: string[], workType: string, years: number): Promise<AIPredictionResult> {
    aiPrediction.value = await api.predictAIRisk(skills, workType, years)
    return aiPrediction.value!
  }

  async function checkStage(score: number): Promise<StageRecommendation> {
    stageRec.value = await api.getStageRecommendation(score)
    return stageRec.value!
  }

  return {
    loading,
    dimensions,
    assessment,
    aiPrediction,
    stageRec,
    loadDimensions,
    submitAssessment,
    runAIRisk,
    checkStage,
  }
})
