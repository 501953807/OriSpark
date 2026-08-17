import { defineStore } from 'pinia'
import { ref } from 'vue'
import { podProfitApi } from '@/api/podProfit'
import type { PricingSimulation, SaleRecord, ProfitResult, DesignSummary, PodOverview } from '@/types/podProfit'

export const usePodProfitStore = defineStore('podProfit', () => {
  const overview = ref<PodOverview | null>(null)
  const designs = ref<DesignSummary[]>([])
  const simulations = ref<PricingSimulation[]>([])
  const lastProfit = ref<ProfitResult | null>(null)
  const loading = ref(false)
  const errorMsg = ref('')

  async function loadOverview() {
    loading.value = true
    try {
      overview.value = await podProfitApi.getOverview()
    } catch (e: unknown) {
      errorMsg.value = (e as Error).message || '加载概览失败'
    } finally {
      loading.value = false
    }
  }

  async function loadDesigns() {
    loading.value = true
    try {
      designs.value = await podProfitApi.getDesignsSummary()
    } catch (e: unknown) {
      errorMsg.value = (e as Error).message || '加载设计数据失败'
    } finally {
      loading.value = false
    }
  }

  async function simulatePricing(platform: string, productType: string, markup: number) {
    loading.value = true
    try {
      simulations.value = await podProfitApi.simulatePricing({ platform, product_type: productType, markup_rate: markup })
    } catch (e: unknown) {
      errorMsg.value = (e as Error).message || '模拟失败'
    } finally {
      loading.value = false
    }
  }

  async function recordSale(data: SaleRecord) {
    loading.value = true
    try {
      lastProfit.value = await podProfitApi.recordSale(data)
      await loadOverview()
    } catch (e: unknown) {
      errorMsg.value = (e as Error).message || '记录销售失败'
    } finally {
      loading.value = false
    }
  }

  return {
    loading, errorMsg, overview, designs, simulations, lastProfit,
    loadOverview, loadDesigns, simulatePricing, recordSale,
  }
})
