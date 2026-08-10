export const CREATOR_TYPE_LABEL: Record<string, string> = {
  illustrator: '插画师',
  photographer: '摄影师',
  video_creator: '视频创作者',
  craftsman: '手工艺人',
  musician: '音乐人',
  writer: '作家',
}

export const RATING_LEVEL_LABEL: Record<string, string> = {
  starter: '入门',
  bronze: '铜牌',
  silver: '银牌',
  gold: '金牌',
  platinum: '铂金',
}

export const RATING_LEVEL_COLOR: Record<string, string> = {
  starter: '#9ca3af',
  bronze: '#cd7f32',
  silver: '#c0c0c0',
  gold: '#ffd700',
  platinum: '#e5e4e2',
}

export function formatCurrency(amount: number): string {
  if (amount >= 10000) {
    return `¥${(amount / 10000).toFixed(2)}万`
  }
  return `¥${amount.toFixed(2)}`
}

export function formatMonth(iso?: string): string {
  if (!iso) return '-'
  return new Date(iso).toLocaleDateString('zh-CN', { year: 'numeric', month: 'long' })
}

export function formatDateTime(iso?: string): string {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN', {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}
