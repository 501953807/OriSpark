import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api/enforcementRoi'
import type { DecisionTreeResult, RoiPrediction, DefenseTier, CaseReference, UserCasesSummary } from '@/types/enforcementRoi'

export const useEnforcementRoiStore = defineStore('enforcementRoi', () => {
  const decisionTree = ref<DecisionTreeResult | null>(null)
  const roiPrediction = ref<RoiPrediction | null>(null)
  const defenseTiers = ref<DefenseTier[]>([])
  const caseReferences = ref<CaseReference[]>([])
  const userCases = ref<UserCasesSummary | null>(null)
  const loading = ref(false)

  async function runDecisionTree(infringementType: string, lossAmount: number) {
    loading.value = true
    try {
      decisionTree.value = await api.getDecisionTree(infringementType, lossAmount)
      return decisionTree.value
    } finally {
      loading.value = false
    }
  }

  async function runRoiPrediction(data: Parameters<typeof api.predictRoi>[0]) {
    roiPrediction.value = await api.predictRoi(data)
    return roiPrediction.value
  }

  async function loadDefenseTiers() {
    defenseTiers.value = await api.listDefenseTiers()
  }

  async function loadCaseReferences(infringementType?: string) {
    caseReferences.value = await api.listCaseReferences(infringementType)
  }

  async function loadUserCases() {
    userCases.value = await api.getUserCases()
  }

  return {
    loading,
    decisionTree,
    roiPrediction,
    defenseTiers,
    caseReferences,
    userCases,
    runDecisionTree,
    runRoiPrediction,
    loadDefenseTiers,
    loadCaseReferences,
    loadUserCases,
  }
})
