import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { RegistrationGuide, CopyrightRegistration, RegistrationSummary } from '@/types/copyrightGuide'

export const useCopyrightGuideStore = defineStore('copyrightGuide', () => {
  const guides = ref<RegistrationGuide[]>([])
  const registrations = ref<CopyrightRegistration[]>([])
  const summary = ref<RegistrationSummary | null>(null)
  const loading = ref(false)

  async function loadGuides() {
    const res = await fetch('/api/copyright-guide/guides')
    if (res.ok) guides.value = await res.json()
  }

  async function loadRegistrations() {
    const res = await fetch('/api/copyright-guide/registrations')
    if (res.ok) registrations.value = await res.json()
  }

  async function loadSummary() {
    const res = await fetch('/api/copyright-guide/summary')
    if (res.ok) summary.value = await res.json()
  }

  async function createRegistration(data: { title: string; work_type: string }) {
    const res = await fetch('/api/copyright-guide/registrations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (res.ok) { await loadRegistrations(); await loadSummary() }
  }

  return { loading, guides, registrations, summary, loadGuides, loadRegistrations, loadSummary, createRegistration }
})
