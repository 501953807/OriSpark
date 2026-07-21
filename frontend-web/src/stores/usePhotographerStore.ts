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
import type { RawFormat, DigitalDownload, FineArtPrintConfig } from '@/api/photographer'

export const usePhotographerStore = defineStore('photographer', () => {
  // ── State ────────────────────────────────────────────────────────
  const shots = ref<PhotographerShot[]>([])
  const shotPagination = ref({ total: 0, page: 1, pageSize: 20, totalPages: 1 })
  const stats = ref<PhotographerStats | null>(null)
  const gpsMap = ref<GPSMapData | null>(null)
  const loading = ref(false)

  // v2 state
  const rawFormats = ref<RawFormat[]>([])
  const digitalDownloads = ref<DigitalDownload[]>([])
  const fineArtPrints = ref<FineArtPrintConfig[]>([])

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

  // ── v2: RAW Formats ────────────────────────────────────────────

  async function fetchRawFormats() {
    loading.value = true
    try {
      const res = await photographerApi.listRawFormats()
      rawFormats.value = res.data.data ?? []
    } catch (e) {
      console.error('fetchRawFormats failed:', e)
      rawFormats.value = []
    } finally {
      loading.value = false
    }
  }

  async function createRawFormat(data: Partial<RawFormat>) {
    try {
      const res = await photographerApi.createRawFormat({
        work_id: data.work_id ?? '',
        file_extension: data.file_extension ?? '',
        ...data,
      })
      rawFormats.value = [...rawFormats.value, {
        ...data,
        id: res.data.data?.id ?? '',
        work_id: data.work_id ?? '',
        file_extension: data.file_extension ?? '',
      }]
    } catch (e) {
      console.error('createRawFormat failed:', e)
      throw e
    }
  }

  async function deleteRawFormat(rawId: string) {
    try {
      await photographerApi.deleteRawFormat(rawId)
      rawFormats.value = rawFormats.value.filter((r) => r.id !== rawId)
    } catch (e) {
      console.error(`deleteRawFormat(${rawId}) failed:`, e)
      throw e
    }
  }

  // ── v2: Digital Downloads ──────────────────────────────────────

  async function fetchDigitalDownloads() {
    loading.value = true
    try {
      const res = await photographerApi.listDigitalDownloads()
      digitalDownloads.value = res.data.data ?? []
    } catch (e) {
      console.error('fetchDigitalDownloads failed:', e)
      digitalDownloads.value = []
    } finally {
      loading.value = false
    }
  }

  async function createDigitalDownload(data: Partial<DigitalDownload>) {
    try {
      const res = await photographerApi.createDigitalDownload({
        work_id: data.work_id ?? '',
        ...data,
      })
      digitalDownloads.value = [...digitalDownloads.value, {
        ...data,
        id: res.data.data?.id ?? '',
        work_id: data.work_id ?? '',
        download_count: data.download_count ?? 0,
      }]
    } catch (e) {
      console.error('createDigitalDownload failed:', e)
      throw e
    }
  }

  async function deleteDigitalDownload(ddId: string) {
    try {
      await photographerApi.deleteDigitalDownload(ddId)
      digitalDownloads.value = digitalDownloads.value.filter((d) => d.id !== ddId)
    } catch (e) {
      console.error(`deleteDigitalDownload(${ddId}) failed:`, e)
      throw e
    }
  }

  // ── v2: Fine Art Prints ────────────────────────────────────────

  async function fetchFineArtPrints() {
    loading.value = true
    try {
      const res = await photographerApi.listFineArtPrints()
      fineArtPrints.value = res.data.data ?? []
    } catch (e) {
      console.error('fetchFineArtPrints failed:', e)
      fineArtPrints.value = []
    } finally {
      loading.value = false
    }
  }

  async function createFineArtPrint(data: Partial<FineArtPrintConfig>) {
    try {
      const res = await photographerApi.createFineArtPrint({
        work_id: data.work_id ?? '',
        paper_type: data.paper_type ?? '',
        ...data,
      })
      fineArtPrints.value = [...fineArtPrints.value, {
        ...data,
        id: res.data.data?.id ?? '',
        work_id: data.work_id ?? '',
        paper_type: data.paper_type ?? '',
        price_multiplier: data.price_multiplier ?? 1.0,
        is_active: data.is_active ?? true,
        framing_available: data.framing_available ?? false,
      }]
    } catch (e) {
      console.error('createFineArtPrint failed:', e)
      throw e
    }
  }

  async function deleteFineArtPrint(fapId: string) {
    try {
      await photographerApi.deleteFineArtPrint(fapId)
      fineArtPrints.value = fineArtPrints.value.filter((f) => f.id !== fapId)
    } catch (e) {
      console.error(`deleteFineArtPrint(${fapId}) failed:`, e)
      throw e
    }
  }

  return {
    // State
    shots,
    shotPagination,
    stats,
    gpsMap,
    loading,
    rawFormats,
    digitalDownloads,
    fineArtPrints,
    // Actions
    fetchShots,
    updateShotStatus,
    addStockChannel,
    removeStockChannel,
    searchByExif,
    fetchGpsMap,
    fetchStats,
    fetchRawFormats,
    createRawFormat,
    deleteRawFormat,
    fetchDigitalDownloads,
    createDigitalDownload,
    deleteDigitalDownload,
    fetchFineArtPrints,
    createFineArtPrint,
    deleteFineArtPrint,
  }
})
