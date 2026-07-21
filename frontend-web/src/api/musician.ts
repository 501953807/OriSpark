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
    client.get<{ data: MusicRelease[] }>('/musician/releases', { params }),

  /** 创建发行 */
  createRelease: (data: Partial<MusicRelease>) =>
    client.post<{ data: MusicRelease }>('/musician/releases', data),

  /** 获取发行详情 */
  getRelease: (id: string) =>
    client.get<{ data: MusicRelease }>(`/musician/releases/${id}`),

  /** 更新发行 */
  updateRelease: (id: string, data: Partial<MusicRelease>) =>
    client.put<{ data: MusicRelease }>(`/musician/releases/${id}`, data),

  /** 删除发行 */
  deleteRelease: (id: string) =>
    client.delete<{ data: unknown }>(`/musician/releases/${id}`),

  /** 获取专辑列表 */
  getAlbums: (params?: Record<string, unknown>) =>
    client.get<{ data: Album[] }>('/musician/albums', { params }),

  /** 创建专辑 */
  createAlbum: (data: Partial<Album>) =>
    client.post<{ data: Album }>('/musician/albums', data),

  /** 删除专辑 */
  deleteAlbum: (id: string) =>
    client.delete<{ data: unknown }>(`/musician/albums/${id}`),

  /** 获取分成协议列表 */
  getSplitSheets: (releaseId?: string) => {
    const qs = releaseId ? `?music_release_id=${releaseId}` : ''
    return client.get<{ data: SplitSheet[] }>(`/musician/split-sheets${qs}`)
  },

  /** 创建分成协议 */
  createSplitSheet: (data: Partial<SplitSheet>) =>
    client.post<{ data: SplitSheet }>('/musician/split-sheets', data),

  /** 更新分成协议 */
  updateSplitSheet: (id: string, data: Partial<SplitSheet>) =>
    client.put<{ data: SplitSheet }>(`/musician/split-sheets/${id}`, data),

  /** 删除分成协议 */
  deleteSplitSheet: (id: string) =>
    client.delete<{ data: unknown }>(`/musician/split-sheets/${id}`),

  /** 获取音乐人统计 */
  getStats: () =>
    client.get<{ data: MusicianStats }>('/musician/stats'),
}
