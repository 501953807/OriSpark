import { defineStore } from 'pinia'
import { ref } from 'vue'
import { commissionApi } from '@/api/commission'
import type {
  CommissionProject,
  Milestone,
  Payment,
  Revision,
  DashboardStats,
  CalendarEvent,
  CommissionFilters,
} from '@/types/commission'

export const useCommissionStore = defineStore('commission', () => {
  const commissions = ref<CommissionProject[]>([])
  const milestones = ref<Milestone[]>([])
  const payments = ref<Payment[]>([])
  const revisions = ref<Revision[]>([])
  const timeline = ref<Record<string, unknown>[]>()
  const calendarEvents = ref<CalendarEvent[]>([])
  const dashboard = ref<DashboardStats | null>(null)
  const loading = ref(false)

  async function fetchCommissions(filters?: CommissionFilters) {
    loading.value = true
    try {
      const res = await commissionApi.list(filters)
      commissions.value = res.data.data ?? []
    } catch {
      commissions.value = []
    } finally {
      loading.value = false
    }
  }

  async function fetchCommissionDetail(id: string) {
    loading.value = true
    try {
      const res = await commissionApi.getById(id)
      return res.data.data ?? null
    } catch {
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchMilestones(commissionId: string) {
    try {
      const res = await commissionApi.listMilestones(commissionId)
      milestones.value = res.data.data ?? []
    } catch {
      milestones.value = []
    }
  }

  async function fetchPayments(commissionId: string) {
    try {
      const res = await commissionApi.listPayments(commissionId)
      payments.value = res.data.data ?? []
    } catch {
      payments.value = []
    }
  }

  async function fetchRevisions(commissionId: string) {
    try {
      const res = await commissionApi.listRevisions(commissionId)
      revisions.value = res.data.data ?? []
    } catch {
      revisions.value = []
    }
  }

  async function fetchTimeline(commissionId: string) {
    try {
      const res = await commissionApi.getTimeline(commissionId)
      timeline.value = res.data.data ?? []
    } catch {
      timeline.value = []
    }
  }

  async function createMilestone(commissionId: string, data: { name: string; due_date?: string; description?: string; order_index?: number }) {
    const res = await commissionApi.createMilestone(commissionId, data)
    if (res.data.data) {
      milestones.value = [...milestones.value, res.data.data]
    }
    return res.data.data
  }

  async function updateMilestone(commissionId: string, milestoneId: string, data: Partial<Pick<Milestone, 'status' | 'due_date'>>) {
    const res = await commissionApi.updateMilestone(commissionId, milestoneId, data)
    if (res.data.data) {
      milestones.value = milestones.value.map((m) =>
        m.id === milestoneId ? { ...m, ...data } : m
      )
    }
    return res.data.data
  }

  async function deleteMilestone(commissionId: string, milestoneId: string) {
    await commissionApi.deleteMilestone(commissionId, milestoneId)
    milestones.value = milestones.value.filter((m) => m.id !== milestoneId)
  }

  async function createPayment(commissionId: string, data: { amount: number; method: string; milestone_id?: string; notes?: string }) {
    const res = await commissionApi.createPayment(commissionId, data)
    if (res.data.data) {
      payments.value = [...payments.value, res.data.data]
    }
    return res.data.data
  }

  async function updatePayment(commissionId: string, paymentId: string, data: Partial<Pick<Payment, 'status' | 'paid_at'>>) {
    const res = await commissionApi.updatePayment(commissionId, paymentId, data)
    if (res.data.data) {
      payments.value = payments.value.map((p) =>
        p.id === paymentId ? { ...p, ...data } : p
      )
    }
    return res.data.data
  }

  async function deletePayment(commissionId: string, paymentId: string) {
    await commissionApi.deletePayment(commissionId, paymentId)
    payments.value = payments.value.filter((p) => p.id !== paymentId)
  }

  async function createRevision(commissionId: string, data: { description: string; client_feedback?: string; created_by: string }) {
    const res = await commissionApi.createRevision(commissionId, data)
    if (res.data.data) {
      revisions.value = [res.data.data, ...revisions.value]
    }
    return res.data.data
  }

  async function fetchCalendar(from: string, to: string) {
    const res = await commissionApi.getCalendar(from, to)
    calendarEvents.value = res.data.data?.events ?? []
    return calendarEvents.value
  }

  async function fetchDashboard() {
    const res = await commissionApi.getDashboard()
    dashboard.value = res.data.data ?? null
    return dashboard.value
  }

  async function updateCommissionStatus(id: string, status: string) {
    const res = await commissionApi.update(id, { status })
    if (res.data.data) {
      commissions.value = commissions.value.map((c) =>
        c.id === id ? { ...c, status, updated_at: new Date().toISOString() } : c
      )
    }
    return res.data.data
  }

  return {
    commissions,
    milestones,
    payments,
    revisions,
    timeline,
    calendarEvents,
    dashboard,
    loading,
    fetchCommissions,
    fetchCommissionDetail,
    fetchMilestones,
    fetchPayments,
    fetchRevisions,
    fetchTimeline,
    createMilestone,
    updateMilestone,
    deleteMilestone,
    createPayment,
    updatePayment,
    deletePayment,
    fetchCalendar,
    fetchDashboard,
    updateCommissionStatus,
    createRevision,
  }
})
