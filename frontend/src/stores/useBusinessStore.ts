import { defineStore } from 'pinia'
import { ref } from 'vue'
import { businessApi } from '@/api/business'

export const useBusinessStore = defineStore('business', () => {
  const revenues = ref<any[]>([])
  const revenueSummary = ref<any>({})
  const partners = ref<any[]>([])
  const orders = ref<any[]>([])
  const notifications = ref<any[]>([])
  const unreadCount = ref(0)
  const dashboard = ref<any>({})
  const loading = ref(false)

  async function fetchRevenues(params?: Record<string, any>) {
    loading.value = true
    try {
      const res = await businessApi.listRevenues(params)
      revenues.value = res.data?.items || (Array.isArray(res.data) ? res.data : [])
    } finally { loading.value = false }
  }

  async function addRevenue(data: any) {
    await businessApi.addRevenue(data)
    await fetchRevenues()
  }

  async function importCsv(formData: FormData) {
    return await businessApi.importRevenueCsv(formData)
  }

  async function fetchRevenueSummary(params?: Record<string, any>) {
    const res = await businessApi.revenueSummary(params)
    revenueSummary.value = res.data || {}
  }

  async function fetchPartners(params?: Record<string, any>) {
    const res = await businessApi.listPartners(params)
    partners.value = res.data?.items || (Array.isArray(res.data) ? res.data : [])
  }

  async function fetchOrders(params?: Record<string, any>) {
    const res = await businessApi.listOrders(params)
    orders.value = res.data?.items || (Array.isArray(res.data) ? res.data : [])
  }

  async function updateOrderStatus(id: string, data: any) {
    await businessApi.updateOrderStatus(id, data)
    await fetchOrders()
  }

  async function fetchNotifications(params?: Record<string, any>) {
    const res = await businessApi.listNotifications(params)
    notifications.value = res.data?.items || (Array.isArray(res.data) ? res.data : [])
  }

  async function fetchUnreadCount() {
    try {
      const res = await businessApi.unreadCount()
      unreadCount.value = res.data?.count ?? res.data ?? 0
    } catch { /* ignore */ }
  }

  async function markRead(id: string) {
    await businessApi.markRead(id)
    await Promise.all([fetchNotifications(), fetchUnreadCount()])
  }

  async function markAllRead() {
    await businessApi.markAllRead()
    await Promise.all([fetchNotifications(), fetchUnreadCount()])
  }

  async function fetchDashboard() {
    const res = await businessApi.getDashboard()
    dashboard.value = res.data || {}
  }

  return {
    revenues, revenueSummary, partners, orders, notifications,
    unreadCount, dashboard, loading,
    fetchRevenues, addRevenue, importCsv, fetchRevenueSummary,
    fetchPartners, fetchOrders, updateOrderStatus,
    fetchNotifications, fetchUnreadCount, markRead, markAllRead,
    fetchDashboard,
  }
})
