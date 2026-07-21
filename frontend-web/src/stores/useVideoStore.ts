import { defineStore } from 'pinia'
import { ref } from 'vue'
import { videoApi } from '@/api/video'
import type {
  VideoWork,
  VideoFingerprintResult,
  VideoMatchResult,
  PlatformDistribution,
  VideoStats,
  VideoFilters,
  VideoListResult,
  VideoFingerprintConfig,
  CreateConfigPayload,
  UpdateConfigPayload,
  VideoFrameFingerprint,
  CreateFramePayload,
} from '@/types/video'

export const useVideoStore = defineStore('video', () => {
  // ── State ────────────────────────────────────────────────────────
  const videos = ref<VideoWork[]>([])
  const pagination = ref<VideoListResult>({ total: 0, page: 1, page_size: 20, total_pages: 1, items: [] })
  const stats = ref<VideoStats | null>(null)
  const matches = ref<VideoMatchResult[]>([])
  const distributions = ref<PlatformDistribution[]>([])
  const fingerprintLoading = ref(false)
  const loading = ref(false)
  const configs = ref<VideoFingerprintConfig[]>([])
  const frames = ref<VideoFrameFingerprint[]>([])

  // ── Actions ──────────────────────────────────────────────────────

  async function fetchVideos(filters?: VideoFilters) {
    loading.value = true
    try {
      const res = await videoApi.getVideos(filters)
      const data = res.data.data
      videos.value = data.items
      pagination.value = {
        total: data.total,
        page: data.page,
        page_size: data.page_size,
        total_pages: data.total_pages,
        items: data.items,
      }
    } catch (e) {
      console.error('fetchVideos failed:', e)
      videos.value = []
    } finally {
      loading.value = false
    }
  }

  async function fetchStats() {
    try {
      const res = await videoApi.getStats()
      stats.value = res.data.data
      return stats.value
    } catch (e) {
      console.error('fetchStats failed:', e)
      stats.value = null
      return null
    }
  }

  async function scanFingerprint(workId: string): Promise<VideoFingerprintResult | null> {
    fingerprintLoading.value = true
    try {
      const res = await videoApi.scanVideoFingerprint(workId)
      return res.data.data
    } catch (e) {
      console.error(`scanFingerprint(${workId}) failed:`, e)
      return null
    } finally {
      fingerprintLoading.value = false
    }
  }

  async function getMatches(workId: string): Promise<VideoMatchResult[]> {
    try {
      const res = await videoApi.getVideoMatches(workId)
      matches.value = res.data.data
      return matches.value
    } catch (e) {
      console.error(`getMatches(${workId}) failed:`, e)
      matches.value = []
      return []
    }
  }

  async function distributeToPlatform(
    workId: string,
    platform: string,
    title: string,
    description?: string
  ): Promise<PlatformDistribution | null> {
    try {
      const res = await videoApi.distributeToPlatform(workId, { platform, title, description })
      const dist: PlatformDistribution = res.data.data
      const idx = distributions.value.findIndex((d) => d.platform === platform)
      if (idx >= 0) {
        distributions.value[idx] = dist
      } else {
        distributions.value.push(dist)
      }
      return dist
    } catch (e) {
      console.error(`distributeToPlatform(${workId}, ${platform}) failed:`, e)
      return null
    }
  }

  async function submitToContentId(workId: string): Promise<boolean> {
    try {
      await videoApi.submitToContentId(workId)
      return true
    } catch (e) {
      console.error(`submitToContentId(${workId}) failed:`, e)
      return false
    }
  }

  // --- Fingerprint Config CRUD ---

  async function fetchConfigs(isActive?: boolean) {
    try {
      const res = await videoApi.listConfigConfigs(isActive)
      configs.value = res.data.data || []
      return configs.value
    } catch (e) {
      console.error('fetchConfigs failed:', e)
      configs.value = []
      return []
    }
  }

  async function createConfig(data: CreateConfigPayload): Promise<VideoFingerprintConfig | null> {
    try {
      const res = await videoApi.createConfig(data)
      configs.value.push(res.data.data)
      return res.data.data
    } catch (e) {
      console.error('createConfig failed:', e)
      return null
    }
  }

  async function updateConfig(configId: string, data: UpdateConfigPayload): Promise<VideoFingerprintConfig | null> {
    try {
      const res = await videoApi.updateConfig(configId, data)
      const idx = configs.value.findIndex((c) => c.id === configId)
      if (idx >= 0) {
        configs.value[idx] = res.data.data
      }
      return res.data.data
    } catch (e) {
      console.error(`updateConfig(${configId}) failed:`, e)
      return null
    }
  }

  async function deleteConfig(configId: string): Promise<boolean> {
    try {
      await videoApi.deleteConfig(configId)
      configs.value = configs.value.filter((c) => c.id !== configId)
      return true
    } catch (e) {
      console.error(`deleteConfig(${configId}) failed:`, e)
      return false
    }
  }

  // --- Frame Fingerprint CRUD ---

  async function fetchFrames(workId?: string, configId?: string) {
    try {
      const res = await videoApi.listFrameFingerprints(workId, configId)
      frames.value = res.data.data || []
      return frames.value
    } catch (e) {
      console.error('fetchFrames failed:', e)
      frames.value = []
      return []
    }
  }

  async function createFrame(data: CreateFramePayload): Promise<VideoFrameFingerprint | null> {
    try {
      const res = await videoApi.createFrameFingerprint(data)
      frames.value.unshift(res.data.data)
      return res.data.data
    } catch (e) {
      console.error('createFrame failed:', e)
      return null
    }
  }

  return {
    // State
    videos,
    pagination,
    stats,
    matches,
    distributions,
    fingerprintLoading,
    loading,
    configs,
    frames,
    // Actions
    fetchVideos,
    fetchStats,
    scanFingerprint,
    getMatches,
    distributeToPlatform,
    submitToContentId,
    fetchConfigs,
    createConfig,
    updateConfig,
    deleteConfig,
    fetchFrames,
    createFrame,
  }
})
