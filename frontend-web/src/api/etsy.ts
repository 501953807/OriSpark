import client from './client'

export interface EtsyShop {
  id: string
  shop_name: string
  shop_id: string
  is_active: boolean
  created_at?: string | null
}

export interface EtsyListing {
  id: string
  title: string
  description?: string | null
  price: number
  currency: string
  quantity: number
  status: string
  etsy_status?: string | null
  views_count?: number
  favorites_count?: number
  sales_count?: number
  revenue?: number
  created_at?: string | null
}

export interface EtsyOrder {
  id: string
  etsy_order_id: string
  buyer_name: string
  order_total: number
  shipping_cost?: number
  tax?: number
  status: string
  order_date?: string | null
  tracking_number?: string | null
}

export const etsyApi = {
  connectShop: (data: { authorization_code: string; shop_id?: string | null; shop_name?: string | null }) =>
    client.post<{ data: unknown }>('/etsy/connect', data),

  listShops: () =>
    client.get<{ data: EtsyShop[] }>('/etsy/shops'),

  disconnectShop: (shopId: string) =>
    client.delete<{ data: null }>(`/etsy/shops/${shopId}`),

  listListings: (params?: { status?: string; page?: number; page_size?: number }) =>
    client.get<{ data: EtsyListing[]; meta?: { total: number; page: number; page_size: number } }>('/etsy/listings', { params }),

  createListing: (data: Partial<EtsyListing>) =>
    client.post<{ data: { id: string } }>('/etsy/listings', data),

  updateListing: (listingId: string, data: Partial<EtsyListing>) =>
    client.patch<{ data: { id: string } }>(`/etsy/listings/${listingId}`, data),

  deleteListing: (listingId: string) =>
    client.delete<{ data: null }>(`/etsy/listings/${listingId}`),

  listOrders: (params?: { status?: string; limit?: number }) =>
    client.get<{ data: EtsyOrder[] }>('/etsy/orders', { params }),
}
