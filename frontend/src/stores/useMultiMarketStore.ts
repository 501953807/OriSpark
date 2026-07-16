import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '@/api/multiMarket'
import type { MarketInfo, GeoArbitrageResult, ExpansionPhase } from '@/types/multiMarket'

export const useMultiMarketStore = defineStore('multiMarket', () => {
  const markets = ref<MarketInfo[]>([])
  const phases = ref<ExpansionPhase[]>([])
  const geoArbitrage = ref<GeoArbitrageResult | null>(null)
  const loading = ref(false)

  async function loadMarkets() {
    loading.value = true
    try {
      markets.value = await api.listMarkets()
    } finally {
      loading.value = false
    }
  }

  async function loadPhases() {
    phases.value = await api.listPhases()
  }

  async function runGeoArbitrage(data: Parameters<typeof api.calcGeoArbitrage>[0]) {
    geoArbitrage.value = await api.calcGeoArbitrage(data)
    return geoArbitrage.value
  }

  return {
    loading,
    markets,
    phases,
    geoArbitrage,
    loadMarkets,
    loadPhases,
    runGeoArbitrage,
  }
})
