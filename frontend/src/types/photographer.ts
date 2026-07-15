export type ShotStatus = 'unreviewed' | 'pass' | 'hold' | 'reject' | 'shortlist'
export type ChannelStatus = 'submitted' | 'active' | 'rejected'

export interface PhotographerShot {
  id: string
  group_id: string
  name: string
  width: number
  height: number
  aspect_ratio: number
  sort_order: number
  created_at: string

  camera_model?: string
  lens?: string
  iso?: number
  aperture?: string
  shutter_speed?: string
  focal_length?: string
  gps_latitude?: number
  gps_longitude?: number
  gps_altitude?: number
  raw_file_path?: string
  shot_status: ShotStatus
  shot_notes?: string
  stock_channels?: Array<{ channel: string; status: string; remote_id?: string }>
}

export interface ShotListResult {
  items: PhotographerShot[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface ShotFilters {
  shot_status?: ShotStatus | string
  camera_model?: string
  group_id?: string
  page?: number
  page_size?: number
}

export interface ExifSearchFilters {
  camera_model?: string
  lens?: string
  iso_min?: number
  iso_max?: number
  aperture?: string
  shutter_speed?: string
  focal_length?: string
  page?: number
  page_size?: number
}

export interface ShotStats {
  total_variants: number
  pass_count: number
  hold_count: number
  reject_count: number
  shortlist_count: number
  unreviewed_count: number
  raw_file_count: number
  stock_channel_count: number
  gps_tracked_count: number
}

export interface RecentActivityItem {
  id: string
  name: string
  shot_status: ShotStatus
  created_at: string | null
}

export interface PhotographerStats {
  stats: ShotStats
  recent_activity: RecentActivityItem[]
}

export interface GPSPoint {
  id: string
  name: string
  latitude: number
  longitude: number
  altitude?: number
  camera_model?: string
}

export interface GPSMapData {
  points: GPSPoint[]
  total: number
}

export interface StockChannelPayload {
  channel: string
  status?: ChannelStatus
  remote_id?: string
}

// --- Stock platform upload/sales types ---

export type UploadStatus = 'pending' | 'uploading' | 'success' | 'failed' | 'rejected'

export interface StockUploadItem {
  id: string
  channel_id: string
  work_id: string
  remote_id: string
  status: UploadStatus
  uploaded_at: string | null
}

export interface StockUploadListResult {
  items: StockUploadItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface StockUploadRequest {
  channel_id: string
  work_id: string
  file_path: string
  keywords?: string[]
  categories?: string[]
}

export interface StockSaleRecord {
  id: string
  sale_amount: number
  license_type?: string
  sale_date: string | null
}

export interface StockSalesSummary {
  channel_name: string
  total_sales: number
  total_revenue: number
  currency: string
  records: StockSaleRecord[]
}

export interface StockPlatformSpec {
  name: string
  display_name: string
  description: string
  requirements: Record<string, unknown>
  supported: boolean
}

export interface StockValidateResult {
  work_id: string
  channel_name: string
  passes: string[]
  warnings: string[]
  blocks: string[]
}
