import client from './client'
import type {
  VideoFilters,
  VideoWork,
  VideoListResult,
  VideoFingerprintResult,
  VideoMatchResult,
  PlatformDistribution,
  VideoStats,
  VideoFingerprintConfig,
  CreateConfigPayload,
  UpdateConfigPayload,
  VideoFrameFingerprint,
  CreateFramePayload,
} from '@/types/video'

export const videoApi = {
  /** 获取视频作品列表 */
  getVideos: (params?: VideoFilters) =>
    client.get<{ data: VideoListResult<VideoWork> }>('/work/variants', { params }),

  /** 扫描视频指纹 */
  scanVideoFingerprint: (workId: string) =>
    client.post<{ data: VideoFingerprintResult }>('/monitor/scan-video-fingerprint', { work_id: workId }),

  /** 获取指纹匹配结果 */
  getVideoMatches: (workId: string) =>
    client.get<{ data: VideoMatchResult[] }>(`/monitor/video-matches?work_id=${workId}`),

  /** 提交到 Content ID */
  submitToContentId: (workId: string) =>
    client.post<{ data: unknown }>('/monitor/content-id/submit', { work_id: workId }),

  /** 获取工程包 */
  getProjectPackage: (workId: string) =>
    client.get<{ data: unknown }>(`/work/${workId}/project-package`),

  /** 分发到平台 */
  distributeToPlatform: (workId: string, data: { platform: string; title: string; description?: string }) =>
    client.post<{ data: PlatformDistribution }>('/publish/distribute', { work_id: workId, ...data }),

  /** 获取视频统计 */
  getStats: () =>
    client.get<{ data: VideoStats }>('/video/stats'),

  // --- Fingerprint Config CRUD ---

  /** 获取指纹配置列表 */
  listConfigConfigs: (isActive?: boolean) =>
    client.get<{ data: VideoFingerprintConfig[] }>('/video-fingerprint/configs', { params: isActive !== undefined ? { is_active: isActive } : undefined }),

  /** 获取单个指纹配置 */
  getConfig: (configId: string) =>
    client.get<{ data: VideoFingerprintConfig }>(`/video-fingerprint/configs/${configId}`),

  /** 创建指纹配置 */
  createConfig: (data: CreateConfigPayload) =>
    client.post<{ data: VideoFingerprintConfig }>('/video-fingerprint/configs', data),

  /** 更新指纹配置 */
  updateConfig: (configId: string, data: UpdateConfigPayload) =>
    client.put<{ data: VideoFingerprintConfig }>(`/video-fingerprint/configs/${configId}`, data),

  /** 删除指纹配置 */
  deleteConfig: (configId: string) =>
    client.delete<{ data: VideoFingerprintConfig }>(`/video-fingerprint/configs/${configId}`),

  // --- Frame Fingerprint CRUD ---

  /** 获取帧指纹列表 */
  listFrameFingerprints: (workId?: string, configId?: string) =>
    client.get<{ data: VideoFrameFingerprint[] }>('/video-fingerprint/frames', { params: { work_id: workId, config_id: configId } }),

  /** 创建帧指纹 */
  createFrameFingerprint: (data: CreateFramePayload) =>
    client.post<{ data: VideoFrameFingerprint }>('/video-fingerprint/frames', data),
}
