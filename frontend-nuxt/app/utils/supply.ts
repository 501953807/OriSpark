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
  draft: 'var(--m-grey-500)',
  quoting: 'var(--m-warning)',
  confirmed: 'var(--m-primary)',
  in_production: 'var(--m-primary)',
  quality_check: 'var(--m-error)',
  shipped: 'var(--m-info)',
  completed: 'var(--m-success)',
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

export function formatCurrency(amount: number | null | undefined): string {
  if (amount == null || isNaN(amount)) return '¥0.00'
  return `¥${amount.toFixed(2)}`
}

export function daysUntil(iso?: string): number | null {
  if (!iso) return null
  const diff = new Date(iso).getTime() - Date.now()
  return Math.ceil(diff / (1000 * 60 * 60 * 24))
}
