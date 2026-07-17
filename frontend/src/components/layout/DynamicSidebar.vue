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
    <router-link to="/app" class="sb-brand" aria-label="OriStudio 首页">
      <div class="sb-logo" aria-hidden="true" :style="{ background: typeInfo?.color }">O</div>
      <div v-if="!isCollapsed" class="sb-brand-text-wrap">
        <div class="sb-brand-text">OriStudio</div>
        <div class="sb-brand-sub">{{ typeInfo?.description ?? '创作者全链路助手' }}</div>
      </div>
    </router-link>

    <!-- Current type badge -->
    <div v-if="!isCollapsed && typeInfo" class="sb-type-badge">
      <span class="sb-type-dot" :style="{ background: typeInfo.color }"></span>
      <span>{{ typeInfo.label }}</span>
    </div>

    <nav class="sb-nav">
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
        <router-link v-if="hasSharedRoute('business')" to="/app/business" class="sb-link" active-class="active">
          <span class="sb-icon">📈</span>
          <span v-if="!isCollapsed">经营管理</span>
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
      <router-link to="/app/business/commissions" class="sb-link" active-class="active">
        <span class="sb-icon">📦</span>
        <span v-if="!isCollapsed">商单管理</span>
      </router-link>
      <router-link to="/app/risk-warning" class="sb-link" active-class="active">
        <span class="sb-icon">⚠️</span>
        <span v-if="!isCollapsed">风险预警</span>
      </router-link>
      <router-link to="/app/integrations" class="sb-link" active-class="active">
        <span class="sb-icon">🔌</span>
        <span v-if="!isCollapsed">第三方对接</span>
      </router-link>
    </nav>

    <!-- Collapse button -->
    <button
      class="sb-collapse-btn"
      @click="appStore.toggleSidebar()"
      :title="isCollapsed ? '展开菜单' : '折叠菜单'"
    >
      {{ isCollapsed ? '>>' : '<<' }}
    </button>

    <!-- User footer — clickable avatar area -->
    <div v-if="!isCollapsed" class="sb-footer">
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
import { computed, ref } from 'vue'
import { useAppStore } from '@/stores/useAppStore'
import { useCreatorTypeStore } from '@/stores/useCreatorTypeStore'
import { getAllCreators } from '@/types/creator'
import type { CreatorType } from '@/types/creator'

const props = defineProps<{
  creatorType?: CreatorType
  mobileVisible?: boolean
}>()

const appStore = useAppStore()
const typeStore = useCreatorTypeStore()
const isCollapsed = computed(() => appStore.sidebarCollapsed)
const isHovering = ref(false)
const pickerOpen = ref(false)

const allTypes = getAllCreators()
const currentType = computed(() => typeStore.getCurrentType())

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
}

function routeIcon(name: string): string {
  return iconMap[name] ?? '📌'
}

function routeLabel(name: string): string {
  return labelMap[name] ?? name
}

/** Routes that are type-specific should NOT be duplicated in the shared section. */
const ROUTES_WITH_SHARED_DUPLICATE = new Set(['rights', 'monitor', 'supply', 'business'])

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
  background: oklch(96% 0.004 240);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  z-index: 100;
  transition: width 0.3s ease, transform 0.3s ease;
  overflow: hidden;
}
.dynamic-sidebar.collapsed {
  width: 60px;
}
.dynamic-sidebar.collapsed.hover-expand {
  width: var(--sidebar-w, 240px);
}
.dark .dynamic-sidebar {
  background: oklch(22% 0.01 240);
}

.sb-brand {
  padding: 16px 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid var(--border);
  text-decoration: none;
  color: inherit;
  min-height: 64px;
  flex-shrink: 0;
}
.sb-logo {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 800;
  font-size: 1rem;
  flex-shrink: 0;
}
.sb-brand-text {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 0.95rem;
}
.sb-brand-sub {
  font-size: 0.62rem;
  color: var(--muted);
}

.sb-type-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  font-size: 0.75rem;
  color: var(--muted);
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
  color: var(--muted);
}
.sb-link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 14px;
  margin: 1px 6px;
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--muted);
  text-decoration: none;
  transition: all 0.2s ease;
  white-space: nowrap;
}
.sb-link:hover {
  background: oklch(56% 0.12 170 / 0.06);
  color: var(--fg);
}
.sb-link.active {
  background: var(--surface);
  color: var(--accent);
  box-shadow: 0 1px 4px oklch(0 0 0 / 0.04);
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
  color: var(--muted);
  transition: color 0.2s;
  flex-shrink: 0;
}
.sb-collapse-btn:hover {
  color: var(--fg);
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
  border-radius: var(--radius-sm);
  user-select: none;
}
.sb-type-selector:hover {
  background: oklch(56% 0.12 170 / 0.06);
}
.sb-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 600;
  font-size: 0.85rem;
  flex-shrink: 0;
}
.sb-user-info {
  flex: 1;
  min-width: 0;
}
.sb-user-name {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--fg);
}
.sb-user-role {
  font-size: 0.65rem;
  color: var(--muted);
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
  border-radius: var(--radius);
  box-shadow: 0 8px 32px oklch(0 0 0 / 0.12);
  padding: 12px;
  z-index: 200;
  width: 200px;
}
.picker-title {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--muted);
  padding: 4px 8px 8px;
}
.picker-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 10px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--fg);
  text-align: left;
  transition: background 0.15s;
  font-family: var(--font-body);
}
.picker-item:hover {
  background: oklch(56% 0.12 170 / 0.06);
}
.picker-item.active {
  background: var(--surface);
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
