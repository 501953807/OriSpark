/**
 * 本地开发 Mock API — 仅开发环境使用
 * 生产构建时此文件不会被包含
 *
 * 拦截 common API 路径，返回 mock 数据，避免后端不可用时的 401/500 错误。
 */

// ── Mock Data ────────────────────────────────────────────────────────────────

const MOCK_WORKS = Array.from({ length: 12 }, (_, i) => ({
  id: `work-${i + 1}`,
  title: `创作作品 ${i + 1}`,
  description: '这是一段作品描述信息',
  category: ['illustration', 'photo', 'video', 'music'][i % 4],
  tags: ['原创', '可用授权'],
  thumbnail: null,
  creator_name: '创作者',
  is_featured: i < 3,
  status: 'active',
  created_at: new Date(Date.now() - i * 86400000).toISOString(),
}))

const MOCK_CONTRACTS = Array.from({ length: 8 }, (_, i) => ({
  id: `contract-${i + 1}`,
  title: `授权合约 ${i + 1}`,
  description: '合约说明',
  contract_type: ['exclusive_license', 'non_exclusive_license'][i % 2],
  total_amount: [500, 1000, 2500, 5000][i % 4],
  currency: 'CNY',
  status: ['listed', 'active', 'executing', 'completed'][i % 4],
  scope_usage: '商业授权',
  scope_geography: '中国大陆',
  created_at: new Date(Date.now() - i * 86400000).toISOString(),
}))

const MOCK_STATS = {
  total_works: 128,
  total_contracts: 45,
  total_listings: 67,
  total_users: 23,
  active_contracts: 12,
  monthly_transaction_volume: 156800,
}

const MOCK_NOTIFICATIONS = [
  { id: '1', title: '合约已认购', body: '您的合约已被运营者认购', type: 'success', created_at: new Date().toISOString() },
  { id: '2', title: '存证完成', body: '作品存证已完成上链', type: 'info', created_at: new Date(Date.now() - 3600000).toISOString() },
  { id: '3', title: '监测预警', body: '发现疑似侵权行为', type: 'warning', created_at: new Date(Date.now() - 7200000).toISOString() },
]

const MOCK_PLUGINS = [
  { id: '1', name: '作品管理', status: 'active' },
  { id: '2', name: '版权存证', status: 'active' },
  { id: '3', name: '监测平台', status: 'inactive' },
]

// ── Router ───────────────────────────────────────────────────────────────────

const routes: Record<string, () => any> = {
  '/api/public/works': () => MOCK_WORKS,
  '/api/public/works?featured=true': () => MOCK_WORKS.filter((w: any) => w.is_featured),
  '/api/public/works?recent=true': () => [...MOCK_WORKS].sort((a: any, b: any) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()).slice(0, 5),
  '/api/public/contracts': () => MOCK_CONTRACTS,
  '/api/public/contracts?recent=true': () => [...MOCK_CONTRACTS].sort((a: any, b: any) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()).slice(0, 5),
  '/api/public/dashboard-stats': () => MOCK_STATS,
  '/api/operator/dashboard/stats': () => MOCK_STATS,
  '/api/operator/works': () => MOCK_WORKS,
  '/api/operator/contracts': () => MOCK_CONTRACTS,
  '/api/operator/notifications': () => MOCK_NOTIFICATIONS,
  '/api/v1/notifications': () => MOCK_NOTIFICATIONS,
  '/api/plugins/list': () => MOCK_PLUGINS,
}

function getMockResponse(url: string): any {
  // Try exact match first, then prefix match
  if (routes[url]) return routes[url]()

  const cleanUrl = url.split('?')[0]
  for (const key of Object.keys(routes)) {
    if (cleanUrl.startsWith(key.split('?')[0])) return routes[key]()
  }
  return null
}

// ── Export ───────────────────────────────────────────────────────────────────

export { getMockResponse }
