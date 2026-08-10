export const REGION_OPTIONS = [
  { value: 'CN', label: '中国' },
  { value: 'US', label: '美国' },
  { value: 'EU', label: '欧盟' },
  { value: 'JP', label: '日本' },
  { value: 'KR', label: '韩国' },
  { value: 'SEA', label: '东南亚' },
  { value: 'GLOBAL', label: '全球' },
] as const

export const CHANNEL_OPTIONS = [
  { value: 'ecommerce', label: '电商平台' },
  { value: 'social_media', label: '社交媒体' },
  { value: 'streaming', label: '流媒体' },
  { value: 'print', label: '印刷出版' },
  { value: 'offline', label: '线下渠道' },
  { value: 'gaming', label: '游戏' },
] as const

export const PRODUCT_OPTIONS = [
  { value: 'apparel', label: '服饰' },
  { value: 'home_decor', label: '家居装饰' },
  { value: 'accessories', label: '配饰' },
  { value: 'stationery', label: '文具' },
  { value: 'digital', label: '数字产品' },
  { value: 'physical', label: '实体周边' },
  { value: '3d_model', label: '3D模型' },
] as const

export const TRANSFORM_RIGHTS_OPTIONS = [
  { key: '2d_to_3d', label: '2D转3D' },
  { key: 'merchandise', label: '商品化' },
  { key: 'digital_nft', label: '数字NFT' },
  { key: 'animation', label: '动画改编' },
  { key: 'print_publish', label: '印刷出版' },
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

export function daysUntil(iso?: string): number | null {
  if (!iso) return null
  const diff = new Date(iso).getTime() - Date.now()
  return Math.ceil(diff / (1000 * 60 * 60 * 24))
}

export const STATUS_LABEL: Record<string, string> = {
  pending: '待处理',
  accepted: '已接受',
  rejected: '已拒绝',
  expired: '已过期',
  cancelled: '已取消',
}

export const STATUS_COLOR: Record<string, string> = {
  pending: '#f59e0b',
  accepted: '#10b981',
  rejected: '#ef4444',
  expired: '#6b7280',
  cancelled: '#9ca3af',
}
