import client from './client'
import type {
  ShotFilters,
  ExifSearchFilters,
  PhotographerShot,
  ShotListResult,
  PhotographerStats,
  GPSMapData,
  StockChannelPayload,
  StockUploadRequest,
  StockUploadListResult,
  StockSalesSummary,
  StockPlatformSpec,
  StockValidateResult,
} from '@/types/photographer'

export interface RawFormat {
  id: string
  work_id: string
  file_extension: string
  file_size_bytes?: number | null
  sensor_width?: number | null
  sensor_height?: number | null
  color_space?: string | null
  created_at?: string | null
}

export interface DigitalDownload {
  id: string
  work_id: string
  product_id?: string | null
  download_url?: string | null
  max_downloads?: number | null
  download_count: number
  created_at?: string | null
}

export interface FineArtPrintConfig {
  id: string
  work_id: string
  paper_type: string
  max_width_cm?: number | null
  max_height_cm?: number | null
  framing_available: boolean
  price_multiplier: number
  is_active: boolean
  created_at?: string | null
}

export const photographerApi = {
  /** 获取摄影师作品列表（分页） */
  getShots: (params?: ShotFilters) =>
    client.get<{ data: ShotListResult }>('/photographer/shots', { params }),

  /** 更新选片状态 */
  updateShotStatus: (id: string, data: { shot_status: string; shot_notes?: string }) =>
    client.post<{ data: PhotographerShot }>(`/photographer/shots/${id}/shot-status`, data),

  /** EXIF 高级搜索 */
  searchByExif: (filters?: ExifSearchFilters) =>
    client.get<{ data: ShotListResult }>('/photographer/exif/search', { params: filters }),

  /** GPS 地图数据 */
  getGpsMap: (groupId?: string) =>
    client.get<{ data: GPSMapData }>('/photographer/gps/map', { params: groupId ? { group_id: groupId } : undefined }),

  /** 添加图库销售渠道 */
  addStockChannel: (variantId: string, data: StockChannelPayload) =>
    client.post<{ data: unknown }>(`/photographer/stock/channels`, null, {
      params: { variant_id: variantId, ...data },
    }),

  /** 移除图库销售渠道 */
  removeStockChannel: (channel: string, variantId: string) =>
    client.delete<{ data: null }>(`/photographer/stock/channels/${channel}`, {
      params: { variant_id: variantId },
    }),

  /** 摄影师统计面板 */
  getStats: (groupId?: string) =>
    client.get<{ data: PhotographerStats }>('/photographer/stats', { params: groupId ? { group_id: groupId } : undefined }),

  /** 上传作品到图库平台 */
  stockUpload: (data: StockUploadRequest) =>
    client.post<{ data: unknown }>('/photographer/stock/upload', data),

  /** 查询图库上传历史 */
  stockUploadsList: (params?: { channel_id?: string; status?: string; work_id?: string; page?: number; page_size?: number }) =>
    client.get<{ data: StockUploadListResult }>('/photographer/stock/uploads', { params }),

  /** 获取渠道销售数据 */
  stockSales: (channelId: string, params?: { start_date?: string; end_date?: string }) =>
    client.get<{ data: StockSalesSummary }>('/photographer/stock/sales', { params: { channel_id: channelId, ...params } }),

  /** 同步销售数据 */
  stockSyncSales: (channelId: string, params?: { start_date?: string; end_date?: string }) =>
    client.post<{ data: StockSalesSummary }>('/photographer/stock/sync-sales', null, { params: { channel_id: channelId, ...params } }),

  /** 预检文件规格 */
  stockValidate: (workId: string, channelName: string) =>
    client.get<{ data: StockValidateResult }>('/photographer/stock/validate', { params: { work_id: workId, channel_name: channelName } }),

  /** 列出支持的图库平台 */
  stockPlatforms: () =>
    client.get<{ data: StockPlatformSpec[] }>('/photographer/stock/platforms'),

  // ── RAW Format CRUD ────────────────────────────────────────

  listRawFormats: () =>
    client.get<{ data: RawFormat[] }>('/photographer/raw-formats'),

  createRawFormat: (data: { work_id: string; file_extension: string; file_size_bytes?: number | null; sensor_width?: number | null; sensor_height?: number | null; color_space?: string | null }) =>
    client.post<{ data: { id: string } }>('/photographer/raw-formats', data),

  updateRawFormat: (rawId: string, data: Partial<RawFormat>) =>
    client.patch<{ data: { id: string } }>(`/photographer/raw-formats/${rawId}`, data),

  deleteRawFormat: (rawId: string) =>
    client.delete<{ data: null }>(`/photographer/raw-formats/${rawId}`),

  // ── Digital Download CRUD ──────────────────────────────────

  listDigitalDownloads: () =>
    client.get<{ data: DigitalDownload[] }>('/photographer/digital-downloads'),

  createDigitalDownload: (data: { work_id: string; product_id?: string | null; download_url?: string | null; max_downloads?: number | null }) =>
    client.post<{ data: { id: string } }>('/photographer/digital-downloads', data),

  updateDigitalDownload: (ddId: string, data: Partial<DigitalDownload>) =>
    client.patch<{ data: { id: string } }>(`/photographer/digital-downloads/${ddId}`, data),

  deleteDigitalDownload: (ddId: string) =>
    client.delete<{ data: null }>(`/photographer/digital-downloads/${ddId}`),

  // ── Fine Art Print CRUD ────────────────────────────────────

  listFineArtPrints: () =>
    client.get<{ data: FineArtPrintConfig[] }>('/photographer/fine-art-prints'),

  createFineArtPrint: (data: { work_id: string; paper_type: string; max_width_cm?: number | null; max_height_cm?: number | null; framing_available?: boolean; price_multiplier?: number }) =>
    client.post<{ data: { id: string } }>('/photographer/fine-art-prints', data),

  updateFineArtPrint: (fapId: string, data: Partial<FineArtPrintConfig>) =>
    client.patch<{ data: { id: string } }>(`/photographer/fine-art-prints/${fapId}`, data),

  deleteFineArtPrint: (fapId: string) =>
    client.delete<{ data: null }>(`/photographer/fine-art-prints/${fapId}`),
}
