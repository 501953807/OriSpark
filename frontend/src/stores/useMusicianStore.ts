import { defineStore } from 'pinia'
import { ref } from 'vue'
import { musicianApi } from '@/api/musician'
import type {
  MusicRelease,
  Album,
  SplitSheet,
  MusicianStats,
} from '@/types/musician'

export const useMusicianStore = defineStore('musician', () => {
  // ── State ────────────────────────────────────────────────────────
  const releases = ref<MusicRelease[]>([])
  const albums = ref<Album[]>([])
  const splitSheets = ref<SplitSheet[]>([])
  const stats = ref<MusicianStats>({
    total_releases: 0,
    total_albums: 0,
    distributed_count: 0,
    pending_splits: 0,
    monthly_revenue: 0,
  })
  const loading = ref(false)
  const errorMsg = ref('')

  // ── Actions ──────────────────────────────────────────────────────

  async function fetchReleases(params?: Record<string, unknown>) {
    loading.value = true
    errorMsg.value = ''
    try {
      const res = await musicianApi.getReleases(params)
      releases.value = res.data.data ?? []
    } catch (e: unknown) {
      errorMsg.value = e instanceof Error ? e.message : '获取发行列表失败'
      releases.value = []
    } finally {
      loading.value = false
    }
  }

  async function createRelease(data: Partial<MusicRelease>): Promise<MusicRelease | null> {
    try {
      const res = await musicianApi.createRelease(data)
      const item = res.data.data
      releases.value = [...releases.value, item]
      return item
    } catch (e: unknown) {
      errorMsg.value = e instanceof Error ? e.message : '创建发行失败'
      return null
    }
  }

  async function updateRelease(id: string, data: Partial<MusicRelease>): Promise<MusicRelease | null> {
    try {
      const res = await musicianApi.updateRelease(id, data)
      const updated = res.data.data
      releases.value = releases.value.map((r) => (r.id === id ? updated : r))
      return updated
    } catch (e: unknown) {
      errorMsg.value = e instanceof Error ? e.message : '更新发行失败'
      return null
    }
  }

  async function deleteRelease(id: string): Promise<boolean> {
    try {
      await musicianApi.deleteRelease(id)
      releases.value = releases.value.filter((r) => r.id !== id)
      return true
    } catch (e: unknown) {
      errorMsg.value = e instanceof Error ? e.message : '删除发行失败'
      return false
    }
  }

  async function fetchAlbums(params?: Record<string, unknown>) {
    loading.value = true
    errorMsg.value = ''
    try {
      const res = await musicianApi.getAlbums(params)
      albums.value = res.data.data ?? []
    } catch (e: unknown) {
      errorMsg.value = e instanceof Error ? e.message : '获取专辑列表失败'
      albums.value = []
    } finally {
      loading.value = false
    }
  }

  async function createAlbum(data: Partial<Album>): Promise<Album | null> {
    try {
      const res = await musicianApi.createAlbum(data)
      const item = res.data.data
      albums.value = [...albums.value, item]
      return item
    } catch (e: unknown) {
      errorMsg.value = e instanceof Error ? e.message : '创建专辑失败'
      return null
    }
  }

  async function fetchSplitSheets(releaseId?: string) {
    loading.value = true
    errorMsg.value = ''
    try {
      const res = await musicianApi.getSplitSheets(releaseId)
      splitSheets.value = res.data.data ?? []
    } catch (e: unknown) {
      errorMsg.value = e instanceof Error ? e.message : '获取分成协议失败'
      splitSheets.value = []
    } finally {
      loading.value = false
    }
  }

  async function createSplitSheet(data: Partial<SplitSheet>): Promise<SplitSheet | null> {
    try {
      const res = await musicianApi.createSplitSheet(data)
      const item = res.data.data
      splitSheets.value = [...splitSheets.value, item]
      return item
    } catch (e: unknown) {
      errorMsg.value = e instanceof Error ? e.message : '创建分成协议失败'
      return null
    }
  }

  async function updateSplitSheet(id: string, data: Partial<SplitSheet>): Promise<SplitSheet | null> {
    try {
      const res = await musicianApi.updateSplitSheet(id, data)
      const updated = res.data.data
      splitSheets.value = splitSheets.value.map((s) => (s.id === id ? updated : s))
      return updated
    } catch (e: unknown) {
      errorMsg.value = e instanceof Error ? e.message : '更新分成协议失败'
      return null
    }
  }

  async function computeStats(): Promise<MusicianStats> {
    loading.value = true
    try {
      const res = await musicianApi.getStats()
      stats.value = res.data.data ?? stats.value
    } catch (e: unknown) {
      errorMsg.value = e instanceof Error ? e.message : '获取统计数据失败'
    } finally {
      loading.value = false
    }
    return stats.value
  }

  async function fetchAll() {
    loading.value = true
    errorMsg.value = ''
    try {
      await Promise.all([
        fetchReleases(),
        fetchAlbums(),
        fetchSplitSheets(),
        computeStats(),
      ])
    } catch (e: unknown) {
      errorMsg.value = e instanceof Error ? e.message : '加载数据失败'
    } finally {
      loading.value = false
    }
  }

  return {
    // State
    releases,
    albums,
    splitSheets,
    stats,
    loading,
    errorMsg,
    // Actions
    fetchReleases,
    createRelease,
    updateRelease,
    deleteRelease,
    fetchAlbums,
    createAlbum,
    fetchSplitSheets,
    createSplitSheet,
    updateSplitSheet,
    computeStats,
    fetchAll,
  }
})
