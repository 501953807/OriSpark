import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { PricingSimulation, SaleRecord, ProfitResult, DesignSummary, PodOverview } from '@/types/podProfit'

export const usePodProfitStore = defineStore('podProfit', () => {
  const overview = ref<PodOverview | null>(null)
  const designs = ref<DesignSummary[]>([])
  const simulations = ref<PricingSimulation[]>([])
  const lastProfit = ref<ProfitResult | null>(null)
  const loading = ref(false)

  async function loadOverview() {
    loading.value = true
    try {
      const res = await fetch('/api/pod-profit/overview')
      if (res.ok) overview.value = await res.json()
    } catch (e) { console.error(e) }
    finally { loading.value = false }
  }

  async function loadDesigns() {
    try {
      const res = await fetch('/api/pod-profit/designs-summary')
      if (res.ok) designs.value = await res.json()
    } catch (e) { console.error(e) }
  }

  async function simulatePricing(platform: string, productType: string, markup: number) {
    const res = await fetch('/api/pod-profit/simulate-pricing', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ platform, product_type: productType, markup_rate: markup }),
    })
    if (res.ok) simulations.value = await res.json()
  }

  async function recordSale(data: SaleRecord) {
    const res = await fetch('/api/pod-profit/log-sale', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (res.ok) {
      lastProfit.value = await res.json()
      await loadOverview()
    }
  }

  return {
    loading, overview, designs, simulations, lastProfit,
    loadOverview, loadDesigns, simulatePricing, recordSale,
  }
})
