import client from './client'
import type {
  MusicRelease,
  Album,
  SplitSheet,
  MusicianStats,
} from '@/types/musician'

export const musicianApi = {
  /** 获取发行列表 */
  getReleases: (params?: Record<string, unknown>) =>
    client.get<{ data: MusicRelease[] }>('/music/releases', { params }),

  /** 创建发行 */
  createRelease: (data: Partial<MusicRelease>) =>
    client.post<{ data: MusicRelease }>('/music/releases', data),

  /** 获取发行详情 */
  getRelease: (id: string) =>
    client.get<{ data: MusicRelease }>(`/music/releases/${id}`),

  /** 更新发行 */
  updateRelease: (id: string, data: Partial<MusicRelease>) =>
    client.put<{ data: MusicRelease }>(`/music/releases/${id}`, data),

  /** 删除发行 */
  deleteRelease: (id: string) =>
    client.delete<{ data: unknown }>(`/music/releases/${id}`),

  /** 获取专辑列表 */
  getAlbums: (params?: Record<string, unknown>) =>
    client.get<{ data: Album[] }>('/music/albums', { params }),

  /** 创建专辑 */
  createAlbum: (data: Partial<Album>) =>
    client.post<{ data: Album }>('/music/albums', data),

  /** 获取分成协议列表 */
  getSplitSheets: (releaseId?: string) => {
    const qs = releaseId ? `?music_release_id=${releaseId}` : ''
    return client.get<{ data: SplitSheet[] }>(`/music/split-sheets${qs}`)
  },

  /** 创建分成协议 */
  createSplitSheet: (data: Partial<SplitSheet>) =>
    client.post<{ data: SplitSheet }>('/music/split-sheets', data),

  /** 更新分成协议 */
  updateSplitSheet: (id: string, data: Partial<SplitSheet>) =>
    client.put<{ data: SplitSheet }>(`/music/split-sheets/${id}`, data),

  /** 获取音乐人统计 */
  getStats: () =>
    client.get<{ data: MusicianStats }>('/music/stats'),
}
