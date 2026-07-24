import client from './client'
import type { SCRScore, SCRAuditLog, LeaderboardEntry } from '@/types/scr'

export const scrApi = {
  getScore: (userId: string) =>
    client.get<{ data: SCRScore }>(`/scr/score/${userId}`),
  submitReport: (data: { user_id: string; score_delta: number; reason: string; related_transaction_id?: string; description?: string }) =>
    client.post<{ data: SCRScore }>('/scr/report', data),
  getHistory: (userId: string) =>
    client.get<{ data: SCRAuditLog[] }>(`/scr/history/${userId}`),
  getLeaderboard: (limit?: number) =>
    client.get<{ data: LeaderboardEntry[] }>('/scr/leaderboard', { params: { limit } }),
}
