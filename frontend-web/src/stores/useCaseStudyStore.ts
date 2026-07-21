import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { CaseStudy, CaseStats } from '@/types/caseStudy'

export const useCaseStudyStore = defineStore('caseStudy', () => {
  const cases = ref<CaseStudy[]>([])
  const stats = ref<CaseStats | null>(null)
  const loading = ref(false)

  async function loadAll(filters?: { category?: string; case_type?: string }) {
    loading.value = true
    try {
      const params = new URLSearchParams()
      if (filters?.category) params.set('category', filters.category)
      if (filters?.case_type) params.set('case_type', filters.case_type)
      const res = await fetch(`/api/case-studies?${params}`)
      if (res.ok) cases.value = await res.json()
    } finally { loading.value = false }
  }

  async function loadStats() {
    const res = await fetch('/api/case-studies/stats')
    if (res.ok) stats.value = await res.json()
  }

  async function create(data: Partial<CaseStudy>) {
    const res = await fetch('/api/case-studies', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (res.ok) await loadAll()
  }

  async function remove(id: string) {
    await fetch(`/api/case-studies/${id}`, { method: 'DELETE' })
    await loadAll()
  }

  return { loading, cases, stats, loadAll, loadStats, create, remove }
})
