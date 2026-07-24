import client from './client'
import type { TradeNegotiation } from '@/types/negotiation'

export const negotiationApi = {
  list: (params?: { status?: string; party?: string }) =>
    client.get<{ data: TradeNegotiation[] }>('/negotiations', { params }),
  getById: (id: string) =>
    client.get<{ data: TradeNegotiation }>(`/negotiations/${id}`),
  create: (data: { buyer_id: string; seller_id: string; listing_id?: string; description?: string; initial_price_yuan?: number }) =>
    client.post<{ data: TradeNegotiation }>('/negotiations', data),
  reply: (id: string, data: { offer_yuan: number; message?: string }) =>
    client.post<{ data: TradeNegotiation }>(`/negotiations/${id}/reply`, data),
  confirm: (id: string, data: { final_price_yuan: number }) =>
    client.patch<{ data: TradeNegotiation }>(`/negotiations/${id}`, data),
  cancel: (id: string) =>
    client.delete<{ data: unknown }>(`/negotiations/${id}`),
}
