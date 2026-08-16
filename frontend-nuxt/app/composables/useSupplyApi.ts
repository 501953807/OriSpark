import type { Factory, FactoryOrder, PODConfig } from '~/types/supply'

function getApiBase(): string {
  return useRuntimeConfig().public.apiBase
}

function authHeaders(): Record<string, string> {
  const token = import.meta.client ? localStorage.getItem('orispark-token') : useCookie('orispark-token').value
  if (!token) throw new Error('未登录')
  return { Authorization: `Bearer ${token}` }
}

// 工厂管理
export function createFactory(data: {
  name: string
  location?: string
  contact?: string
  phone?: string
  email?: string
  categories?: string[]
  product_categories?: string[]
  material_capabilities?: string[]
  moq?: number
  typical_lead_time_days?: number
  notes?: string
}): Promise<Factory> {
  return $fetch(`${getApiBase()}/operator/supply/factories`, {
    method: 'POST',
    headers: authHeaders(),
    body: data,
  })
}

export function fetchFactories(params?: { category?: string; status?: string }): Promise<Factory[]> {
  const query = new URLSearchParams()
  if (params?.category) query.set('category', params.category)
  if (params?.status) query.set('status', params.status)
  const qs = query.toString()
  return $fetch(`${getApiBase()}/operator/supply/factories${qs ? '?' + qs : ''}`, {
    headers: authHeaders(),
  })
}

export function fetchFactory(id: string): Promise<Factory> {
  return $fetch(`${getApiBase()}/operator/supply/factories/${id}`, {
    headers: authHeaders(),
  })
}

// 生产订单
export function createOrder(data: {
  contract_id?: string
  work_id?: string
  factory_id?: string
  product_name: string
  product_category?: string
  quantity?: number
  unit_price?: number
  expected_date?: string
  notes?: string
}): Promise<FactoryOrder> {
  return $fetch(`${getApiBase()}/operator/supply/orders`, {
    method: 'POST',
    headers: authHeaders(),
    body: data,
  })
}

export function fetchOrders(params?: { status?: string; factory_id?: string }): Promise<FactoryOrder[]> {
  const query = new URLSearchParams()
  if (params?.status) query.set('status', params.status)
  if (params?.factory_id) query.set('factory_id', params.factory_id)
  const qs = query.toString()
  return $fetch(`${getApiBase()}/operator/supply/orders${qs ? '?' + qs : ''}`, {
    headers: authHeaders(),
  })
}

export function confirmOrder(id: string): Promise<{ id: string; status: string }> {
  return $fetch(`${getApiBase()}/operator/supply/orders/${id}/confirm`, {
    method: 'POST',
    headers: authHeaders(),
  })
}

export function startProduction(id: string): Promise<{ id: string; status: string }> {
  return $fetch(`${getApiBase()}/operator/supply/orders/${id}/start`, {
    method: 'POST',
    headers: authHeaders(),
  })
}

export function shipOrder(id: string, data: { shipping_method?: string; tracking_number?: string }): Promise<any> {
  const params = new URLSearchParams()
  if (data.shipping_method) params.set('shipping_method', data.shipping_method)
  if (data.tracking_number) params.set('tracking_number', data.tracking_number)
  const qs = params.toString()
  return $fetch(`${getApiBase()}/operator/supply/orders/${id}/ship${qs ? '?' + qs : ''}`, {
    method: 'POST',
    headers: authHeaders(),
  })
}

export function inspectOrder(id: string, data: { passed: boolean; notes?: string }): Promise<any> {
  return $fetch(`${getApiBase()}/operator/supply/orders/${id}/inspect`, {
    method: 'POST',
    headers: authHeaders(),
    body: data,
  })
}

// POD 配置
export function createPODConfig(data: {
  platform: string
  api_key: string
  api_secret?: string
  default_store_id?: string
  settings?: Record<string, any>
}): Promise<PODConfig> {
  return $fetch(`${getApiBase()}/operator/supply/pod/configs`, {
    method: 'POST',
    headers: authHeaders(),
    body: data,
  })
}

export function fetchPODConfigs(): Promise<PODConfig[]> {
  return $fetch(`${getApiBase()}/operator/supply/pod/configs`, {
    headers: authHeaders(),
  })
}
