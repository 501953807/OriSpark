import client from './client'
import type { AiSessionCreate } from '@/types/ai_session'

export const aiSessionApi = {
  create(workId: string, data: AiSessionCreate) {
    return client.post(`/works/${workId}/ai-session`, data)
  },
  list(workId: string) {
    return client.get(`/works/${workId}/ai-sessions`)
  },
  update(workId: string, sessionId: string, data: Partial<AiSessionCreate>) {
    return client.patch(`/works/${workId}/ai-session/${sessionId}`, data)
  },
  delete(workId: string, sessionId: string) {
    return client.delete(`/works/${workId}/ai-session/${sessionId}`)
  },
}
