import client from './client'
import type {
  CraftProduct,
  Factory,
  RFQ,
  Order,
  CraftsmanStats,
} from '@/types/craftsman'

export const craftsmanApi = {
  // ── Products ──────────────────────────────────────────────────

  getProducts: () =>
    client.get<{ data: CraftProduct[] }>('/craftsman/products'),

  getProduct: (id: string) =>
    client.get<{ data: CraftProduct }>(`/craftsman/products/${id}`),

  createProduct: (data: Partial<CraftProduct>) =>
    client.post<{ data: { id: string } }>('/craftsman/products', data),

  updateProduct: (id: string, data: Partial<CraftProduct>) =>
    client.patch<{ data: CraftProduct }>(`/craftsman/products/${id}`, data),

  deleteProduct: (id: string) =>
    client.delete<{ data: null }>(`/craftsman/products/${id}`),

  // ── Factories ─────────────────────────────────────────────────

  getFactories: () =>
    client.get<{ data: Factory[] }>('/craftsman/factories'),

  createFactory: (data: Partial<Factory>) =>
    client.post<{ data: { id: string } }>('/craftsman/factories', data),

  updateFactory: (id: string, data: Partial<Factory>) =>
    client.patch<{ data: Factory }>(`/craftsman/factories/${id}`, data),

  deleteFactory: (id: string) =>
    client.delete<{ data: null }>(`/craftsman/factories/${id}`),

  // ── RFQs ──────────────────────────────────────────────────────

  getRFQs: () =>
    client.get<{ data: RFQ[] }>('/craftsman/rfqs'),

  createRFQ: (data: Partial<RFQ>) =>
    client.post<{ data: { id: string } }>('/craftsman/rfqs', data),

  updateRFQ: (id: string, data: Partial<RFQ>) =>
    client.patch<{ data: RFQ }>(`/craftsman/rfqs/${id}`, data),

  deleteRFQ: (id: string) =>
    client.delete<{ data: null }>(`/craftsman/rfqs/${id}`),

  // ── Orders ────────────────────────────────────────────────────

  getOrders: () =>
    client.get<{ data: Order[] }>('/craftsman/orders'),

  // ── Stats (placeholder — calculated on frontend) ──────────────

  getStats: (): Promise<CraftsmanStats> =>
    // Will be computed from products/factories/rfqs on frontend
    Promise.resolve({
      total_products: 0,
      active_listings: 0,
      factory_count: 0,
      rfq_count: 0,
      monthly_revenue: 0,
    }),
}
