import client from './client'
import type {
  AiSession,
  AiSessionCreateInput,
  ImportFolderResult,
} from '@/types/illustrator'

export const illustratorApi = {
  // ── AI Sessions ───────────────────────────────────────────────

  /** 获取作品 AI 创作时间线 */
  getSessions: (workId: string) =>
    client.get<{ data: AiSession[] }>(`/works/${workId}/ai-sessions`),

  /** 记录 AI 创作会话 */
  createSession: (workId: string, data: AiSessionCreateInput) =>
    client.post<{ data: AiSession }>(`/works/${workId}/ai-session`, data),

  /** 编辑会话记录 */
  updateSession: (workId: string, sessionId: string, data: Partial<AiSessionCreateInput>) =>
    client.patch<{ data: unknown }>(`/works/${workId}/ai-session/${sessionId}`, data),

  /** 删除会话记录 */
  deleteSession: (workId: string, sessionId: string) =>
    client.delete<{ message: string }>(`/works/${workId}/ai-session/${sessionId}`),

  // ── Folder Import ─────────────────────────────────────────────

  /** 批量导入文件夹 */
  importFolder: (formData: FormData) =>
    client.post<{ data: ImportFolderResult }>('/works/import-folder', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
}
