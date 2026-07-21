export type AlbumType = 'single' | 'ep' | 'album' | 'compilation'
export type ReleaseFormat = 'mp3' | 'flac' | 'wav'
export type DistributionStatus = 'pending' | 'distributing' | 'distributed'
export type SplitSheetStatus = 'draft' | 'signing' | 'signed' | 'active'

export interface MusicRelease {
  id: string
  album_id?: string
  work_variant_id?: string
  title: string
  isrc?: string
  audio_file_path?: string
  duration_seconds?: number
  bitrate?: number
  format: ReleaseFormat
  genre?: string
  mood?: string
  bpm?: number
  distribution_status: DistributionStatus
  created_at?: string
  updated_at?: string
}

export interface Album {
  id: string
  title: string
  album_type: AlbumType
  release_date?: string
  cover_art_path?: string
  label?: string
  total_tracks?: number
  duration_seconds?: number
  created_at?: string
  updated_at?: string
}

export interface SplitSheet {
  id: string
  music_release_id: string
  title: string
  splits?: Array<{ name: string; share: number }>
  publishing_share?: number
  master_share?: number
  status: SplitSheetStatus
  signed_at?: string
  created_at?: string
  updated_at?: string
}

export interface MusicianStats {
  total_releases: number
  total_albums: number
  distributed_count: number
  pending_splits: number
  monthly_revenue: number
}
