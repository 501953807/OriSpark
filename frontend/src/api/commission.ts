import client from './client'
import type {
  CommissionProject,
  Milestone,
  Payment,
  Revision,
  DashboardStats,
  CalendarEvent,
  CommissionFilters,
} from '@/types/commission'

export const commissionApi = {
  // Project CRUD
  list: (params?: CommissionFilters) =>
    client.get<{ data: CommissionProject[] }>('/commission/projects', { params }),
  getById: (id: string) =>
    client.get<{ data: CommissionProject }>(`/commission/projects/${id}`),
  create: (data: Partial<CommissionProject>) =>
    client.post<{ data: CommissionProject }>('/commission/projects', data),
  update: (id: string, data: Partial<CommissionProject>) =>
    client.put<{ data: CommissionProject }>(`/commission/projects/${id}`, data),
  delete: (id: string) =>
    client.delete<{ data: unknown }>(`/commission/projects/${id}`),

  // Orders
  listOrders: (id: string, params?: { status?: string }) =>
    client.get<{ data: Record<string, unknown>[] }>(`/commission/projects/${id}/orders`, { params }),
  createOrder: (id: string, data: { order_type: string; amount: number }) =>
    client.post<{ data: Record<string, unknown> }>(`/commission/projects/${id}/orders`, data),

  // Messages
  listMessages: (id: string) =>
    client.get<{ data: Record<string, unknown>[] }>(`/commission/projects/${id}/messages`),
  createMessage: (id: string, data: { sender_id: string; content: string }) =>
    client.post<{ data: Record<string, unknown> }>(`/commission/projects/${id}/messages`, data),

  // Milestones
  listMilestones: (id: string) =>
    client.get<{ data: Milestone[] }>(`/commission/projects/${id}/milestones`),
  createMilestone: (id: string, data: { name: string; due_date?: string; description?: string; order_index?: number }) =>
    client.post<{ data: Milestone }>(`/commission/projects/${id}/milestones`, data),
  updateMilestone: (id: string, milestoneId: string, data: Partial<Pick<Milestone, 'status' | 'due_date'>>) =>
    client.patch<{ data: Milestone }>(`/commission/projects/${id}/milestones/${milestoneId}`, data),
  deleteMilestone: (id: string, milestoneId: string) =>
    client.delete<{ data: unknown }>(`/commission/projects/${id}/milestones/${milestoneId}`),

  // Payments
  listPayments: (id: string) =>
    client.get<{ data: Payment[] }>(`/commission/projects/${id}/payments`),
  createPayment: (id: string, data: { amount: number; method: string; milestone_id?: string; notes?: string }) =>
    client.post<{ data: Payment }>(`/commission/projects/${id}/payments`, data),
  updatePayment: (id: string, paymentId: string, data: Partial<Pick<Payment, 'status' | 'paid_at'>>) =>
    client.patch<{ data: Payment }>(`/commission/projects/${id}/payments/${paymentId}`, data),
  deletePayment: (id: string, paymentId: string) =>
    client.delete<{ data: unknown }>(`/commission/projects/${id}/payments/${paymentId}`),

  // Revisions
  listRevisions: (id: string) =>
    client.get<{ data: Revision[] }>(`/commission/projects/${id}/revisions`),
  createRevision: (id: string, data: { description: string; client_feedback?: string; files?: string[] }) =>
    client.post<{ data: Revision }>(`/commission/projects/${id}/revisions`, data),
  deleteRevision: (id: string, revisionId: string) =>
    client.delete<{ data: unknown }>(`/commission/projects/${id}/revisions/${revisionId}`),

  // Timeline
  getTimeline: (id: string) =>
    client.get<{ data: Record<string, unknown>[] }>(`/commission/projects/${id}/timeline`),

  // Calendar
  getCalendar: (from: string, to: string) =>
    client.get<{ data: { events: CalendarEvent[] } }>('/commission/calendar', { params: { from, to } }),

  // Dashboard
  getDashboard: () =>
    client.get<{ data: DashboardStats }>('/commission/dashboard'),
}
