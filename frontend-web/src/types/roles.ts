/** 合约市场 9 方参与角色定义 */

export type ParticipantRole =
  | 'creator'
  | 'operator'
  | 'legal_rep'
  | 'tax_agent'
  | 'logistics'
  | 'insurer'
  | 'trader'
  | 'payment_provider'
  | 'platform'

export interface ParticipantRoleInfo {
  key: ParticipantRole
  label: string
  icon: string
  color: string
  description: string
  requires_license: boolean
  dashboardModules?: DashboardModule[]
  sidebarItems?: SidebarItem[]
}

export interface DashboardModule {
  path: string
  icon: string
  name: string
  desc: string
}

export interface SidebarItem {
  path: string
  icon: string
  label: string
}

export const PARTICIPANT_ROLES: Record<ParticipantRole, ParticipantRoleInfo> = {
  creator: {
    key: 'creator',
    label: '创作者',
    icon: '🎨',
    color: '#8B5CF6',
    description: '内容/作品原创者',
    requires_license: false,
  },
  operator: {
    key: 'operator',
    label: '运营方',
    icon: '📋',
    color: '#3B82F6',
    description: '作品运营/推广代理',
    requires_license: true,
    sidebarItems: [
      { path: '/app/contract-market', icon: '📝', label: '合约市场' },
      { path: '/app/multimarket', icon: '🌍', label: '多市场扩展' },
      { path: '/app/negotiation', icon: '🤝', label: '交易谈判' },
      { path: '/app/capability', icon: '🧠', label: '能力评估' },
      { path: '/app/credit-improvement', icon: '💳', label: '信用提升' },
      { path: '/app/settings', icon: '⚙️', label: '偏好设置' },
    ],
  },
  legal_rep: {
    key: 'legal_rep',
    label: '法务代表',
    icon: '⚖️',
    color: '#EF4444',
    description: '法律事务代理人',
    requires_license: true,
    sidebarItems: [
      { path: '/app/contract-market', icon: '📝', label: '合约市场' },
      { path: '/app/contract-risk', icon: '📋', label: '合同风险评估' },
      { path: '/app/negotiation', icon: '🤝', label: '交易谈判' },
      { path: '/app/risk-center', icon: '🔔', label: '风控中心' },
      { path: '/app/settings', icon: '⚙️', label: '偏好设置' },
    ],
  },
  tax_agent: {
    key: 'tax_agent',
    label: '税务代理',
    icon: '🧾',
    color: '#F59E0B',
    description: '税务申报/合规代理',
    requires_license: true,
    sidebarItems: [
      { path: '/app/tax-settlement', icon: '💱', label: '税务结算' },
      { path: '/app/contract-market', icon: '📝', label: '合约市场' },
      { path: '/app/risk-warning', icon: '⚠️', label: '风险预警' },
      { path: '/app/settings', icon: '⚙️', label: '偏好设置' },
    ],
  },
  logistics: {
    key: 'logistics',
    label: '物流方',
    icon: '📦',
    color: '#10B981',
    description: '实体商品配送',
    requires_license: true,
    sidebarItems: [
      { path: '/app/supply', icon: '🏭', label: '供应链管理' },
      { path: '/app/contract-market', icon: '📝', label: '合约市场' },
      { path: '/app/risk-warning', icon: '⚠️', label: '风险预警' },
      { path: '/app/settings', icon: '⚙️', label: '偏好设置' },
    ],
  },
  insurer: {
    key: 'insurer',
    label: '保险方',
    icon: '🛡️',
    color: '#6366F1',
    description: '版权/履约保险',
    requires_license: true,
    sidebarItems: [
      { path: '/app/insurance', icon: '🛡️', label: '保险市场' },
      { path: '/app/contract-market', icon: '📝', label: '合约市场' },
      { path: '/app/risk-warning', icon: '⚠️', label: '风险预警' },
      { path: '/app/settings', icon: '⚙️', label: '偏好设置' },
    ],
  },
  trader: {
    key: 'trader',
    label: '采购方',
    icon: '🛒',
    color: '#F97316',
    description: '商业授权采购者',
    requires_license: true,
    sidebarItems: [
      { path: '/app/contract-market', icon: '📝', label: '合约市场' },
      { path: '/app/marketplace', icon: '🤝', label: '商业撮合' },
      { path: '/app/multimarket', icon: '🌍', label: '多市场扩展' },
      { path: '/app/capability', icon: '🧠', label: '能力评估' },
      { path: '/app/credit-improvement', icon: '💳', label: '信用提升' },
      { path: '/app/settings', icon: '⚙️', label: '偏好设置' },
    ],
  },
  payment_provider: {
    key: 'payment_provider',
    label: '支付托管方',
    icon: '💳',
    color: '#14B8A6',
    description: '资金托管/结算',
    requires_license: true,
    sidebarItems: [
      { path: '/app/contract-market', icon: '📝', label: '合约市场' },
      { path: '/app/business', icon: '💼', label: '经营管理' },
      { path: '/app/risk-warning', icon: '⚠️', label: '风险预警' },
      { path: '/app/settings', icon: '⚙️', label: '偏好设置' },
    ],
  },
  platform: {
    key: 'platform',
    label: '平台方',
    icon: '🏢',
    color: '#64748B',
    description: 'OriStudio 平台运营',
    requires_license: true,
    sidebarItems: [
      { path: '/app', icon: '📊', label: '工作台' },
      { path: '/app/contract-market', icon: '📝', label: '合约市场' },
      { path: '/app/marketplace', icon: '🤝', label: '商业撮合' },
      { path: '/app/supply', icon: '🏭', label: '供应链管理' },
      { path: '/app/insurance', icon: '🛡️', label: '保险市场' },
      { path: '/app/risk-center', icon: '🔔', label: '风控中心' },
      { path: '/app/enforcement-dashboard', icon: '⚖️', label: '维权流水线' },
      { path: '/app/settings', icon: '⚙️', label: '系统设置' },
    ],
  },
}

export function getParticipantRoleInfo(key: string): ParticipantRoleInfo | null {
  return PARTICIPANT_ROLES[key as ParticipantRole] ?? null
}

export function getAllParticipantRoles(): ParticipantRoleInfo[] {
  return Object.values(PARTICIPANT_ROLES)
}
