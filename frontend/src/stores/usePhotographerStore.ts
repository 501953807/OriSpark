import { defineStore } from 'pinia'
import { ref } from 'vue'
import { photographerApi } from '@/api/photographer'
import type {
  PhotographerShot,
  ShotListResult,
  PhotographerStats,
  GPSMapData,
  ShotFilters,
  ExifSearchFilters,
  StockChannelPayload,
} from '@/types/photographer'

export const usePhotographerStore = defineStore('photographer', () => {
  // ── State ────────────────────────────────────────────────────────
  const shots = ref<PhotographerShot[]>([])
  const shotPagination = ref({ total: 0, page: 1, pageSize: 20, totalPages: 1 })
  const stats = ref<PhotographerStats | null>(null)
  const gpsMap = ref<GPSMapData | null>(null)
  const loading = ref(false)

  // ── Actions ──────────────────────────────────────────────────────

  async function fetchShots(filters?: ShotFilters, groupId?: string) {
    loading.value = true
    try {
      const res = await photographerApi.getShots({ ...filters, group_id: groupId })
      const data = res.data.data
      shots.value = data.items
      shotPagination.value = {
        total: data.total,
        page: data.page,
        pageSize: data.page_size,
        totalPages: data.total_pages,
      }
    } catch (e) {
      console.error('fetchShots failed:', e)
      shots.value = []
    } finally {
      loading.value = false
    }
  }

  async function updateShotStatus(shotId: string, status: string, notes?: string) {
    try {
      const res = await photographerApi.updateShotStatus(shotId, {
        shot_status: status,
        shot_notes: notes,
      })
      const updated: PhotographerShot = res.data.data
      const idx = shots.value.findIndex((s) => s.id === shotId)
      if (idx >= 0) {
        shots.value[idx] = updated
      }
      return updated
    } catch (e) {
      console.error(`updateShotStatus(${shotId}) failed:`, e)
      throw e
    }
  }

  async function addStockChannel(shotId: string, channel: string) {
    try {
      await photographerApi.addStockChannel(shotId, { channel, status: 'submitted' })
      const idx = shots.value.findIndex((s) => s.id === shotId)
      if (idx >= 0) {
        const existing = [...(shots.value[idx].stock_channels ?? [])]
        const entry = { channel, status: 'submitted' as const }
        const dupIdx = existing.findIndex((c) => c.channel === channel)
        if (dupIdx >= 0) {
          existing[dupIdx] = entry
        } else {
          existing.push(entry)
        }
        shots.value[idx] = { ...shots.value[idx], stock_channels: existing }
      }
    } catch (e) {
      console.error(`addStockChannel(${shotId}, ${channel}) failed:`, e)
      throw e
    }
  }

  async function removeStockChannel(shotId: string, channel: string) {
    try {
      await photographerApi.removeStockChannel(channel, shotId)
      const idx = shots.value.findIndex((s) => s.id === shotId)
      if (idx >= 0) {
        const remaining = (shots.value[idx].stock_channels ?? []).filter(
          (c) => c.channel !== channel
        )
        shots.value[idx] = { ...shots.value[idx], stock_channels: remaining }
      }
    } catch (e) {
      console.error(`removeStockChannel(${shotId}, ${channel}) failed:`, e)
      throw e
    }
  }

  async function searchByExif(filters: ExifSearchFilters) {
    try {
      const res = await photographerApi.searchByExif(filters)
      const data = res.data.data
      shots.value = data.items
      shotPagination.value = {
        total: data.total,
        page: data.page,
        pageSize: data.page_size,
        totalPages: data.total_pages,
      }
      return data.items
    } catch (e) {
      console.error('searchByExif failed:', e)
      shots.value = []
      return []
    }
  }

  async function fetchGpsMap(groupId?: string) {
    loading.value = true
    try {
      const res = await photographerApi.getGpsMap(groupId)
      gpsMap.value = res.data.data
      return gpsMap.value
    } catch (e) {
      console.error('fetchGpsMap failed:', e)
      gpsMap.value = null
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchStats(groupId?: string) {
    loading.value = true
    try {
      const res = await photographerApi.getStats(groupId)
      stats.value = res.data.data
      return stats.value
    } catch (e) {
      console.error('fetchStats failed:', e)
      stats.value = null
      return null
    } finally {
      loading.value = false
    }
  }

  return {
    // State
    shots,
    shotPagination,
    stats,
    gpsMap,
    loading,
    // Actions
    fetchShots,
    updateShotStatus,
    addStockChannel,
    removeStockChannel,
    searchByExif,
    fetchGpsMap,
    fetchStats,
  }
})
