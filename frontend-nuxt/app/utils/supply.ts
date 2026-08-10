export const ORDER_STATUS_LABEL: Record<string, string> = {
  draft: '草稿',
  quoting: '询价中',
  confirmed: '已确认',
  in_production: '生产中',
  quality_check: '质检中',
  shipped: '已发货',
  completed: '已完成',
  cancelled: '已取消',
}

export const ORDER_STATUS_COLOR: Record<string, string> = {
  draft: '#6b7280',
  quoting: '#f59e0b',
  confirmed: '#3b82f6',
  in_production: '#8b5cf6',
  quality_check: '#ef4444',
  shipped: '#0ea5e9',
  completed: '#10b981',
  cancelled: '#9ca3af',
}

export const PLATFORM_OPTIONS = [
  { value: 'printful', label: 'Printful' },
  { value: 'printify', label: 'Printify' },
  { value: 'gelato', label: 'Gelato' },
  { value: 'custom', label: '自定义' },
] as const

export function formatDate(iso?: string): string {
  if (!iso) return '-'
  return new Date(iso).toLocaleDateString('zh-CN', { year: 'numeric', month: 'short', day: 'numeric' })
}

export function formatDateTime(iso?: string): string {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN', {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export function formatCurrency(amount: number): string {
  return `¥${amount.toFixed(2)}`
}

export function daysUntil(iso?: string): number | null {
  if (!iso) return null
  const diff = new Date(iso).getTime() - Date.now()
  return Math.ceil(diff / (1000 * 60 * 60 * 24))
}
