import { defineStore } from 'pinia'
import { ref } from 'vue'
import { etsyApi } from '@/api/etsy'
import type { EtsyShop, EtsyListing, EtsyOrder } from '@/api/etsy'

export const useEtsyStore = defineStore('etsy', () => {
  // ── State ─────────────────────────────────────────────────────
  const shops = ref<EtsyShop[]>([])
  const listings = ref<EtsyListing[]>([])
  const orders = ref<EtsyOrder[]>([])
  const loading = ref(false)
  const errorMsg = ref('')

  function setError(msg: string) {
    errorMsg.value = msg
    console.error('[etsy]', msg)
  }

  function clearError() {
    errorMsg.value = ''
  }

  // ── Shops ─────────────────────────────────────────────────────

  async function fetchShops() {
    loading.value = true
    clearError()
    try {
      const res = await etsyApi.listShops()
      shops.value = res.data.data ?? []
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '加载店铺失败'
      setError(msg)
      shops.value = []
    } finally {
      loading.value = false
    }
  }

  async function connectShop(data: { authorization_code: string; shop_id?: string | null; shop_name?: string | null }) {
    try {
      await etsyApi.connectShop(data)
      await fetchShops()
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '连接店铺失败'
      setError(msg)
      throw e
    }
  }

  async function disconnectShop(shopId: string) {
    try {
      await etsyApi.disconnectShop(shopId)
      shops.value = shops.value.filter((s) => s.id !== shopId)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '断开失败'
      setError(msg)
      throw e
    }
  }

  // ── Listings ──────────────────────────────────────────────────

  async function fetchListings(params?: { status?: string; page?: number; page_size?: number }) {
    loading.value = true
    clearError()
    try {
      const res = await etsyApi.listListings(params)
      listings.value = res.data.data ?? []
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '加载商品列表失败'
      setError(msg)
      listings.value = []
    } finally {
      loading.value = false
    }
  }

  async function createListing(data: Partial<EtsyListing>) {
    try {
      const res = await etsyApi.createListing(data)
      const created: EtsyListing = {
        ...data,
        id: res.data.data?.id ?? '',
        title: data.title ?? '',
        price: data.price ?? 0,
        quantity: data.quantity ?? 0,
        currency: data.currency ?? 'USD',
        status: data.status ?? 'active',
        created_at: new Date().toISOString(),
      }
      listings.value = [...listings.value, created]
      return created
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '创建商品失败'
      setError(msg)
      throw e
    }
  }

  async function deleteListing(listingId: string) {
    try {
      await etsyApi.deleteListing(listingId)
      listings.value = listings.value.filter((l) => l.id !== listingId)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '删除失败'
      setError(msg)
      throw e
    }
  }

  // ── Orders ────────────────────────────────────────────────────

  async function fetchOrders(params?: { status?: string; limit?: number }) {
    loading.value = true
    clearError()
    try {
      const res = await etsyApi.listOrders(params)
      orders.value = res.data.data ?? []
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '加载订单失败'
      setError(msg)
      orders.value = []
    } finally {
      loading.value = false
    }
  }

  // ── Bulk Load ─────────────────────────────────────────────────

  async function fetchAll() {
    loading.value = true
    clearError()
    try {
      await Promise.allSettled([fetchShops(), fetchListings(), fetchOrders()])
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '加载数据失败'
      setError(msg)
    } finally {
      loading.value = false
    }
  }

  return {
    // State
    shops,
    listings,
    orders,
    loading,
    errorMsg,
    // Actions
    fetchShops,
    connectShop,
    disconnectShop,
    fetchListings,
    createListing,
    deleteListing,
    fetchOrders,
    fetchAll,
    setError,
    clearError,
  }
})
