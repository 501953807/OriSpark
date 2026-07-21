import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { RevenueRecord, RevenueSummary, Partner, Order, Notification, BusinessDashboard } from '@/types/business'
import { businessApi } from '@/api/business'

export const useBusinessStore = defineStore('business', () => {
  const revenues = ref<RevenueRecord[]>([])
  const revenueSummary = ref<RevenueSummary>({} as RevenueSummary)
  const partners = ref<Partner[]>([])
  const orders = ref<Order[]>([])
  const notifications = ref<Notification[]>([])
  const unreadCount = ref(0)
  const dashboard = ref<BusinessDashboard>({} as BusinessDashboard)
  const loading = ref(false)

  async function fetchRevenues(params?: Record<string, string>) {
    loading.value = true
    try {
      const res = await businessApi.listRevenues(params)
      revenues.value = res.data?.items || (Array.isArray(res.data) ? res.data : [])
    } catch (e) {
      console.error('fetchRevenues failed:', e)
    } finally {
      loading.value = false
    }
  }

  async function addRevenue(data: Partial<RevenueRecord>) {
    try {
      await businessApi.addRevenue(data)
      await fetchRevenues()
    } catch (e) {
      console.error('addRevenue failed:', e)
      throw e
    }
  }

  async function importCsv(formData: FormData) {
    try {
      return await businessApi.importRevenueCsv(formData)
    } catch (e) {
      console.error('importCsv failed:', e)
      throw e
    }
  }

  async function fetchRevenueSummary(params?: Record<string, string>) {
    try {
      const res = await businessApi.revenueSummary(params)
      revenueSummary.value = res.data || {} as RevenueSummary
    } catch (e) {
      console.error('fetchRevenueSummary failed:', e)
    }
  }

  async function fetchPartners(params?: Record<string, string>) {
    try {
      const res = await businessApi.listPartners(params)
      partners.value = res.data?.items || (Array.isArray(res.data) ? res.data : [])
    } catch (e) {
      console.error('fetchPartners failed:', e)
    }
  }

  async function fetchOrders(params?: Record<string, string>) {
    try {
      const res = await businessApi.listOrders(params)
      orders.value = res.data?.items || (Array.isArray(res.data) ? res.data : [])
    } catch (e) {
      console.error('fetchOrders failed:', e)
    }
  }

  async function updateOrderStatus(id: string, data: Partial<Order>) {
    try {
      await businessApi.updateOrderStatus(id, data)
      await fetchOrders()
    } catch (e) {
      console.error(`updateOrderStatus(${id}) failed:`, e)
      throw e
    }
  }

  async function fetchNotifications(params?: Record<string, string>) {
    try {
      const res = await businessApi.listNotifications(params)
      notifications.value = res.data?.items || (Array.isArray(res.data) ? res.data : [])
    } catch (e) {
      console.error('fetchNotifications failed:', e)
    }
  }

  async function fetchUnreadCount() {
    try {
      const res = await businessApi.unreadCount()
      unreadCount.value = res.data?.count ?? res.data ?? 0
    } catch {
      /* ignore */
    }
  }

  async function markRead(id: string) {
    try {
      await businessApi.markRead(id)
      await Promise.all([fetchNotifications(), fetchUnreadCount()]).catch(() => {})
    } catch (e) {
      console.error(`markRead(${id}) failed:`, e)
      throw e
    }
  }

  async function markAllRead() {
    try {
      await businessApi.markAllRead()
      await Promise.all([fetchNotifications(), fetchUnreadCount()]).catch(() => {})
    } catch (e) {
      console.error('markAllRead failed:', e)
      throw e
    }
  }

  async function fetchDashboard() {
    try {
      const res = await businessApi.getDashboard()
      dashboard.value = res.data || {} as BusinessDashboard
    } catch (e) {
      console.error('fetchDashboard failed:', e)
    }
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
