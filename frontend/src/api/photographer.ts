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
}
