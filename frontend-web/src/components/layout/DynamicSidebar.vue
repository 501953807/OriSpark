<template>
  <aside
    :class="[
      'dynamic-sidebar',
      { collapsed: isCollapsed, 'mobile-visible': mobileVisible, 'hover-expand': isCollapsed && isHovering },
    ]"
    role="navigation"
    aria-label="动态侧边栏"
    @mouseenter="isCollapsed && (isHovering = true)"
    @mouseleave="isHovering = false"
  >
    <!-- Brand and badge -->
    <router-link to="/app" class="sb-brand" aria-label="OriStudio 首页">
      <div class="sb-logo" aria-hidden="true" :style="{ background: (hasNonCreatorRole ? roleInfo?.color : typeInfo?.color) ?? 'var(--accent)' }">O</div>
      <div v-if="!isCollapsed" class="sb-brand-text-wrap">
        <div class="sb-brand-text">OriStudio</div>
        <div class="sb-brand-sub">{{ hasNonCreatorRole ? (roleInfo?.description ?? '用户工作台') : (typeInfo?.description ?? '创作者全链路助手') }}</div>
      </div>
    </router-link>

    <!-- Role badge for non-creator roles -->
    <div v-if="!isCollapsed && hasNonCreatorRole && roleInfo" class="sb-type-badge">
      <span class="sb-type-dot" :style="{ background: roleInfo.color }"></span>
      <span>{{ roleInfo.label }}</span>
    </div>
    <!-- Type badge for creator roles -->
    <div v-else-if="!isCollapsed && typeInfo" class="sb-type-badge">
      <span class="sb-type-dot" :style="{ background: typeInfo.color }"></span>
      <span>{{ typeInfo.label }}</span>
    </div>

    <nav class="sb-nav">
      <!-- Non-creator role: show role-specific navigation -->
      <template v-if="hasNonCreatorRole && roleInfo?.sidebarItems">
        <router-link
          v-for="item in roleInfo.sidebarItems"
          :key="item.path"
          :to="item.path"
          class="sb-link"
          active-class="active"
        >
          <span class="sb-icon">{{ item.icon }}</span>
          <span v-if="!isCollapsed">{{ item.label }}</span>
        </router-link>
      </template>

      <!-- Creator role: show existing creator-type-based navigation -->
      <template v-else>
        <!-- Core business chain — shared across all types -->
        <div v-if="!isCollapsed" class="sb-section-title">概览</div>
        <router-link to="/app" class="sb-link" active-class="active">
          <span class="sb-icon">📊</span>
          <span v-if="!isCollapsed">工作台</span>
        </router-link>

        <!-- Type-specific core features -->
        <template v-if="typeInfo">
          <div v-if="!isCollapsed" class="sb-section-title">核心功能</div>

          <router-link
            v-for="routeName in typeInfo.routes"
            :key="routeName"
            :to="`/app/${routeName}`"
            class="sb-link"
            active-class="active"
          >
            <span class="sb-icon">{{ routeIcon(routeName) }}</span>
            <span v-if="!isCollapsed">{{ routeLabel(routeName) }}</span>
          </router-link>

          <!-- Creative tools section (shared) -->
          <div v-if="!isCollapsed" class="sb-section-title">创作工具</div>

          <router-link to="/app/projects" class="sb-link" active-class="active">
            <span class="sb-icon">📂</span>
            <span v-if="!isCollapsed">项目分组</span>
          </router-link>
          <router-link to="/app/recycle" class="sb-link" active-class="active">
            <span class="sb-icon">🗑️</span>
            <span v-if="!isCollapsed">回收站</span>
          </router-link>
        </template>

        <!-- Rights & Protection (shared) -->
        <template v-if="!isCollapsed">
          <div class="sb-section-title" v-if="hasSharedSection('rights')">权利保护</div>
          <router-link v-if="hasSharedRoute('rights')" to="/app/rights" class="sb-link" active-class="active">
            <span class="sb-icon">🛡️</span>
            <span v-if="!isCollapsed">权利存证</span>
          </router-link>
          <router-link v-if="hasSharedRoute('monitor')" to="/app/monitor" class="sb-link" active-class="active">
            <span class="sb-icon">👁️</span>
            <span v-if="!isCollapsed">侵权监测</span>
          </router-link>
        </template>

        <!-- Monetization (shared) -->
        <template v-if="!isCollapsed">
          <div class="sb-section-title" v-if="hasSharedSection('supply')">商业变现</div>
          <router-link v-if="hasSharedRoute('supply')" to="/app/supply" class="sb-link" active-class="active">
            <span class="sb-icon">💰</span>
            <span v-if="!isCollapsed">商业转化</span>
          </router-link>
          <router-link v-if="hasSharedRoute('marketplace')" to="/app/marketplace" class="sb-link" active-class="active">
            <span class="sb-icon">🤝</span>
            <span v-if="!isCollapsed">商业撮合</span>
          </router-link>
          <router-link v-if="hasSharedRoute('business')" to="/app/business" class="sb-link" active-class="active">
            <span class="sb-icon">📈</span>
            <span v-if="!isCollapsed">经营管理</span>
          </router-link>
          <router-link v-if="hasSharedRoute('contract-market')" to="/app/contract-market" class="sb-link" active-class="active">
            <span class="sb-icon">{{ routeIcon('contract-market') }}</span>
            <span v-if="!isCollapsed">合约市场</span>
          </router-link>
        </template>

        <!-- AI Growth (shared) -->
        <template v-if="!isCollapsed">
          <div class="sb-section-title" v-if="hasSharedSection('ai')">AI增长引擎</div>
          <router-link v-if="hasSharedRoute('ai-growth')" to="/app/ai-growth" class="sb-link" active-class="active">
            <span class="sb-icon">🤖</span>
            <span v-if="!isCollapsed">AI增长引擎</span>
          </router-link>
        </template>

        <!-- Risk & Compliance (shared) -->
        <template v-if="!isCollapsed">
          <div class="sb-section-title" v-if="hasSharedSection('credit')">风险合规</div>
          <router-link v-if="hasSharedRoute('risk-warning')" to="/app/risk-warning" class="sb-link" active-class="active">
            <span class="sb-icon">⚠️</span>
            <span v-if="!isCollapsed">风险预警</span>
          </router-link>
          <router-link v-if="hasSharedRoute('credit-improvement')" to="/app/credit-improvement" class="sb-link" active-class="active">
            <span class="sb-icon">💳</span>
            <span v-if="!isCollapsed">信用提升</span>
          </router-link>
        </template>

        <!-- Settings section -->
        <div v-if="!isCollapsed" class="sb-section-title">系统设置</div>
        <router-link to="/app/settings" class="sb-link" active-class="active">
          <span class="sb-icon">⚙️</span>
          <span v-if="!isCollapsed">偏好设置</span>
        </router-link>
        <router-link to="/app/settings/watermarks" class="sb-link" active-class="active">
          <span class="sb-icon">💧</span>
          <span v-if="!isCollapsed">水印预设</span>
        </router-link>
        <router-link to="/app/settings/templates" class="sb-link" active-class="active">
          <span class="sb-icon">📐</span>
          <span v-if="!isCollapsed">元数据模板</span>
        </router-link>
        <router-link to="/app/settings/subscriptions" class="sb-link" active-class="active">
          <span class="sb-icon">🏷️</span>
          <span v-if="!isCollapsed">订阅分级</span>
        </router-link>
      </template>
    </nav>

    <!-- Collapse button -->
    <button
      class="sb-collapse-btn"
      @click="appStore.toggleSidebar()"
      :title="isCollapsed ? '展开菜单' : '折叠菜单'"
    >
      {{ isCollapsed ? '>>' : '<<' }}
    </button>

    <!-- Role info footer for non-creator roles -->
    <div v-if="!isCollapsed && hasNonCreatorRole && roleInfo" class="sb-footer">
      <div class="sb-type-selector">
        <div class="sb-avatar" :style="{ background: roleInfo.color }">{{ roleInfo.icon }}</div>
        <div class="sb-user-info">
          <div class="sb-user-name">{{ roleInfo.label }}</div>
          <div class="sb-user-role">{{ roleInfo.description }}</div>
        </div>
      </div>
    </div>

    <!-- User footer for creator roles -->
    <div v-else-if="!isCollapsed" class="sb-footer">
      <div class="sb-type-selector" @click="togglePicker">
        <div class="sb-avatar" :style="{ background: pickerTypeInfo?.color }">创</div>
        <div class="sb-user-info">
          <div class="sb-user-name">{{ pickerTypeInfo?.label ?? '创作者' }}</div>
          <div class="sb-user-role">点击切换身份</div>
        </div>
        <span class="sb-chevron">{{ pickerOpen ? '▲' : '▼' }}</span>
      </div>

      <!-- Type picker popup -->
      <Teleport to="body">
        <div v-if="pickerOpen" class="type-picker-overlay" @click="closePicker"></div>
        <Transition name="picker-fade">
          <div v-if="pickerOpen" class="type-picker">
            <div class="picker-title">选择创作者类型</div>
            <button
              v-for="ct in allTypes"
              :key="ct.type"
              :class="['picker-item', { active: ct.type === currentType }]"
              @click="selectType(ct.type)"
            >
              <span class="picker-dot" :style="{ background: ct.color }"></span>
              <span>{{ ct.label }}</span>
            </button>
          </div>
        </Transition>
      </Teleport>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useAppStore } from '@/stores/useAppStore'
import { useCreatorTypeStore } from '@/stores/useCreatorTypeStore'
import { useAuthStore } from '@/stores/useAuthStore'
import { getAllCreators } from '@/types/creator'
import { PARTICIPANT_ROLES, getParticipantRoleInfo } from '@/types/roles'
import type { CreatorType } from '@/types/creator'
import type { ParticipantRole } from '@/types/roles'

const props = defineProps<{
  creatorType?: CreatorType
  mobileVisible?: boolean
}>()

const appStore = useAppStore()
const typeStore = useCreatorTypeStore()
const authStore = useAuthStore()

// Derive participant role from auth store; prefer non-creator roles
const derivedRole = computed<ParticipantRole>(() => {
  const roles = authStore.participantRoles
  if (!roles || roles.length === 0) return 'creator'
  const nonCreator = roles.find((r: string) => r !== 'creator')
  return (nonCreator || 'creator') as ParticipantRole
})

const participantRole = ref<ParticipantRole>(derivedRole.value)

// Watch auth changes and update sidebar role
watch(() => authStore.participantRoles, (newRoles) => {
  if (newRoles && newRoles.length > 0) {
    const nonCreator = newRoles.find((r: string) => r !== 'creator')
    participantRole.value = (nonCreator || 'creator') as ParticipantRole
  }
}, { immediate: false })

const isCollapsed = computed(() => appStore.sidebarCollapsed)
const isHovering = ref(false)
const pickerOpen = ref(false)

const allTypes = getAllCreators()
const currentType = computed(() => typeStore.getCurrentType())

const roleInfo = computed(() => {
  if (!participantRole.value) return null
  return getParticipantRoleInfo(participantRole.value)
})

const iconEmoji: Record<string, string> = {
  illustrator: '🖌️',
  photographer: '📸',
  video: '🎬',
  craftsman: '🔨',
  musician: '🎵',
  writer: '✒️',
}

const pickerTypeInfo = computed(() => {
  const info = typeStore.getTypeInfo(currentType.value)
  return info ? { ...info, icon: iconEmoji[info.type] ?? '🎨' } : null
})

const typeInfo = computed(() =>
  props.creatorType
    ? typeStore.getTypeInfo(props.creatorType)
    : typeStore.getCurrentType()
      ? typeStore.getTypeInfo(typeStore.getCurrentType())
      : null,
)

// Dynamic: show non-creator navigation when user has business roles
// Creator role always uses the creator-type navigation below
const hasNonCreatorRole = computed(() => {
  const roles = authStore.participantRoles
  if (!roles || roles.length === 0) return false
  return roles.some((r: string) => r !== 'creator' && PARTICIPANT_ROLES[r as ParticipantRole])
})

function togglePicker() {
  pickerOpen.value = !pickerOpen.value
}

function closePicker() {
  pickerOpen.value = false
}

function selectType(type: CreatorType) {
  typeStore.switchType(type)
  pickerOpen.value = false
}

const iconMap: Record<string, string> = {
  works: '🎨',
  illustrator: '🖌️',
  rights: '🛡️',
  monitor: '👁️',
  ipr: '📋',
  supply: '💰',
  publish: '📱',
  business: '📈',
  photographer: '📸',
  video: '🎬',
  craftsman: '🔨',
  musician: '🎵',
  writer: '✒️',
  settings: '⚙️',
  'settings/watermarks': '💧',
  'settings/templates': '📐',
  'settings/subscriptions': '🏷️',
  'business/commissions': '📦',
  'risk-warning': '⚠️',
  integrations: '🔌',
  projects: '📂',
  recycle: '🗑️',
  marketplace: '🤝',
  tax: '💱',
  distribution: '📡',
  'pod-profit': '📦',
  'case-studies': '📚',
  'copyright-guide': '📜',
  attribution: '🔗',
  'fork-merge': '🍴',
  negotiation: '🤝',
  'scr-dash': '⭐',
  'tax-settlement': '💱',
  'ai-growth': '🤖',
  capability: '🧠',
  'growth-stages': '📈',
  insurance: '🛡️',
  'contract-market': '📝',
  'content-pipeline': '📡',
  'contract-risk': '📋',
  'enforcement-dashboard': '⚖️',
  'enforcement-roi': '💰',
  'credit-improvement': '💳',
  'risk-center': '🔔',
  'private-traffic': '👥',
  multimarket: '🌍',
  culling: '✂️',
}

const labelMap: Record<string, string> = {
  works: '作品管理',
  illustrator: '插画工作台',
  rights: '权利保护',
  monitor: '侵权监测',
  ipr: 'IP登记',
  supply: '商业转化',
  publish: '内容分发',
  business: '经营管理',
  photographer: '摄影师工作台',
  video: '视频工作室',
  craftsman: '手工艺工坊',
  musician: '音乐工作台',
  writer: '文字工作台',
  settings: '偏好设置',
  'settings/watermarks': '水印预设',
  'settings/templates': '元数据模板',
  'settings/subscriptions': '订阅分级',
  'business/commissions': '商单管理',
  'risk-warning': '风险预警',
  integrations: '第三方对接',
  projects: '项目分组',
  recycle: '回收站',
  marketplace: '商业撮合',
  tax: '全球税务',
  distribution: '分发回流',
  'pod-profit': 'POD 利润计算器',
  'case-studies': '案例库',
  'copyright-guide': '版权登记指南',
  attribution: '归因分析',
  'fork-merge': 'Fork & Merge',
  negotiation: '交易谈判',
  'scr-dash': 'SCR 信誉分',
  'tax-settlement': '税务结算',
  'ai-growth': 'AI 增长引擎',
  capability: '能力评估',
  'growth-stages': '成长阶段',
  insurance: '保险市场',
  'contract-market': '合约市场',
  'content-pipeline': '内容分发流水线',
  'contract-risk': '合同风险评估',
  'enforcement-dashboard': '维权流水线',
  'enforcement-roi': '维权 ROI',
  'credit-improvement': '信用提升',
  'risk-center': '风控中心',
  'private-traffic': '私域流量',
  multimarket: '多市场扩展',
  culling: '作品筛选',
}

function routeIcon(name: string): string {
  return iconMap[name] ?? '📌'
}

function routeLabel(name: string): string {
  return labelMap[name] ?? name
}

function hasSharedRoute(routeName: string): boolean {
  if (!typeInfo.value) return true
  return !typeInfo.value.routes.includes(routeName)
}

function hasSharedSection(sectionRoute: string): boolean {
  return hasSharedRoute(sectionRoute)
}
</script>

<style scoped>
.dynamic-sidebar {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: var(--sidebar-w, 240px);
  background: var(--sidebar-bg);
  border-right: 1px solid var(--border);
  box-shadow: 2px 0 12px var(--shadow-color);
  display: flex;
  flex-direction: column;
  z-index: 100;
  transition: width var(--transition-slow, 0.3s) ease, transform 0.3s ease;
  overflow: hidden;
}
.dynamic-sidebar.collapsed {
  width: var(--sidebar-collapsed, 60px);
}
.dynamic-sidebar.collapsed.hover-expand {
  width: var(--sidebar-w, 240px);
}

.sb-brand {
  padding: var(--space-2) 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid var(--border);
  text-decoration: none;
  color: var(--sidebar-fg, var(--fg));
  min-height: var(--topbar-h, 64px);
  flex-shrink: 0;
}
.sb-logo {
  width: 34px;
  height: 34px;
  border-radius: var(--m-radius-sm);
  background: linear-gradient(135deg, #5585FF, #2A52B0);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #FFFFFF;
  font-weight: 800;
  font-size: 1rem;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(85, 133, 255, 0.1);
}
.sb-brand-text {
  font-family: Inter;
  font-weight: 700;
  font-size: 0.95rem;
  color: var(--sidebar-fg, var(--fg));
}
.sb-brand-sub {
  font-size: 0.62rem;
  color: var(--sidebar-fg-dim, var(--muted));
}

.sb-type-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  font-size: 0.75rem;
  color: var(--sidebar-fg-dim, var(--muted));
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.sb-type-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.sb-nav {
  flex: 1;
  padding: 8px 0;
  overflow-y: auto;
  overflow-x: hidden;
}
.sb-section-title {
  padding: 8px 14px 4px;
  font-size: 0.62rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--sidebar-fg-dim, var(--muted));
}
.sb-link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 14px;
  margin: 1px 6px;
  border-radius: var(--m-radius-sm);
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--sidebar-fg-dim, var(--muted));
  text-decoration: none;
  transition: all 0.2s ease;
  white-space: nowrap;
  border-left: 3px solid transparent;
}
.sb-link:hover {
  background: var(--surface-2);
  color: var(--sidebar-fg, var(--fg));
}
.sb-link.active {
  background: var(--sidebar-active);
  color: var(--accent);
  border-left-color: var(--accent);
  font-weight: 600;
}
.collapsed .sb-link {
  padding: 12px;
  justify-content: center;
}
.collapsed .sb-link .sb-icon {
  margin: 0;
  font-size: 1.2rem;
}
.sb-icon {
  font-size: 1.05rem;
  width: 22px;
  text-align: center;
  flex-shrink: 0;
}

.sb-collapse-btn {
  padding: 10px;
  border: none;
  border-top: 1px solid var(--border);
  background: transparent;
  cursor: pointer;
  font-size: 0.75rem;
  color: var(--sidebar-fg-dim, var(--muted));
  transition: color 0.2s;
  flex-shrink: 0;
}
.sb-collapse-btn:hover {
  color: var(--sidebar-fg, var(--fg));
}

.sb-footer {
  padding: 10px 14px;
  border-top: 1px solid var(--border);
  flex-shrink: 0;
}

/* Creator type selector (footer) */
.sb-type-selector {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: background 0.2s;
  padding: 6px 8px;
  margin: -6px -8px;
  border-radius: var(--m-radius-sm);
  user-select: none;
}
.sb-type-selector:hover {
  background: var(--surface-2);
}
.sb-avatar {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  background: linear-gradient(135deg, #5585FF, #2A52B0);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #FFFFFF;
  font-weight: 600;
  font-size: 0.85rem;
  flex-shrink: 0;
  box-shadow: 0 2px 6px rgba(85, 133, 255, 0.1);
}
.sb-user-info {
  flex: 1;
  min-width: 0;
}
.sb-user-name {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--sidebar-fg, var(--fg));
}
.sb-user-role {
  font-size: 0.65rem;
  color: var(--sidebar-fg-dim, var(--muted));
}
.sb-chevron {
  font-size: 0.6rem;
  color: var(--muted);
  flex-shrink: 0;
}

/* Type picker popup */
.type-picker-overlay {
  position: fixed;
  inset: 0;
  z-index: 199;
}
.type-picker {
  position: fixed;
  bottom: 80px;
  left: 10px;
  max-height: 320px;
  overflow-y: auto;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--m-radius-sm);
  box-shadow: var(--shadow-lg);
  padding: 12px;
  z-index: 200;
  width: 200px;
}
.picker-title {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--sidebar-fg-dim, var(--muted));
  padding: 4px 8px 8px;
}
.picker-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 10px;
  border: none;
  border-radius: var(--m-radius-sm);
  background: transparent;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--fg);
  text-align: left;
  transition: background 0.15s;
  font-family: Inter;
}
.picker-item:hover {
  background: var(--surface-2);
}
.picker-item.active {
  background: var(--sidebar-active);
  color: var(--accent);
  font-weight: 600;
}
.picker-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

/* Picker transitions */
.picker-fade-enter-active,
.picker-fade-leave-active {
  transition: opacity 0.15s ease;
}
.picker-fade-enter-from,
.picker-fade-leave-to {
  opacity: 0;
}
</style>
