<!-- Materio Layout — OriStudio (创作者工作台)
     参照: https://demos.themeselection.com/materio-vuetify-vuejs-admin-template/demo-1/
     左右布局：左侧侧边栏（无嵌套缩进，统一 23px paddingLeft）
     右上透明顶部导航 + 右下内容区
-->
<template>
  <div class="m-layout" :class="{ 'm-layout--collapsed': isCollapsed, 'm-layout--mobile': isMobile }">
    <!-- Mobile overlay -->
    <div v-if="isMobile && sidebarOpen" class="m-layout__overlay" @click="sidebarOpen = false" />

    <!-- Collapsed hover tooltip -->
    <div v-if="isCollapsed && tooltipVisible" ref="tooltipRef" class="m-tooltip">
      {{ tooltipText }}
    </div>

    <!-- ═══════════════ LEFT SIDEBAR ═══════════════ -->
    <aside class="m-sidebar" :class="{ 'm-sidebar--collapsed': isCollapsed, 'm-sidebar--open': sidebarOpen }">
      <!-- Brand + Collapse toggle -->
      <div class="m-sidebar__brand">
        <router-link to="/app" class="m-sidebar__logo">
          <svg width="24" height="24" viewBox="0 0 30 24" fill="none">
            <path d="M1.476 0.435L6.799 3.722C7.084 3.898 7.258 4.21 7.258 4.546V19.56C7.258 19.901 7.079 20.216 6.787 20.391L1.465 23.578C1.006 23.852 0.412 23.703 0.137 23.244C0.047 23.094 0 22.922 0 22.747V1.259C0 0.724 0.433 0.291 0.968 0.291C1.147 0.291 1.323 0.341 1.476 0.435Z" fill="currentColor"/>
            <path d="M28.525 0.432L23.203 3.707C22.916 3.883 22.742 4.196 22.742 4.532V19.56C22.742 19.901 22.921 20.216 23.213 20.391L28.535 23.578C28.994 23.852 29.588 23.703 29.863 23.244C29.952 23.094 30 22.922 30 22.747V1.256C30 0.722 29.567 0.288 29.032 0.288C28.853 0.288 28.678 0.338 28.525 0.432Z" fill="currentColor"/>
            <path d="M1.473 0.427L15 8.722V16.709L0 8.114V1.253C0 0.718 0.433 0.285 0.968 0.285C1.146 0.285 1.321 0.334 1.473 0.427Z" fill="currentColor"/>
            <path d="M28.527 0.427L15 8.722V16.709L30 8.114V1.253C30 0.718 29.567 0.285 29.032 0.285C28.854 0.285 28.679 0.334 28.527 0.427Z" fill="currentColor"/>
          </svg>
          <span class="m-sidebar__title">OriStudio</span>
        </router-link>
        <button v-show="!isCollapsed" class="m-sidebar__collapse-btn" @click="isCollapsed = !isCollapsed" aria-label="折叠侧边栏">
          <i class="material-icons">chevron_left</i>
        </button>
        <button v-show="isCollapsed" class="m-sidebar__expand-btn" @click="isCollapsed = false" aria-label="展开侧边栏">
          <i class="material-icons">chevron_right</i>
        </button>
      </div>

      <!-- Navigation -->
      <nav class="m-sidebar__nav">
        <template v-for="group in navGroups" :key="group.key">
          <!-- Section divider -->
          <div class="m-sidebar__section">{{ group.label }}</div>

          <!-- Items (flat — no nesting) -->
          <ul class="m-sidebar__items">
            <li v-for="item in group.items" :key="item.path">
              <router-link
                :to="item.path"
                class="m-sidebar__link"
                :class="{ 'm-sidebar__link--active': isActive(item.path) }"
                :data-label="item.label"
                :data-badge="item.badge || ''"
                @click="closeMobile()"
                @mouseenter="showTooltip($event, item.label)"
                @mouseleave="hideTooltip"
              >
                <i class="material-icons m-sidebar__link-icon">{{ item.icon }}</i>
                <span class="m-sidebar__link-label">{{ item.label }}</span>
                <span v-if="item.badge" class="m-sidebar__badge">{{ item.badge }}</span>
              </router-link>
            </li>
          </ul>
        </template>
      </nav>

      <!-- Footer — User Card -->
      <div class="m-sidebar__footer">
        <div class="m-sidebar__type-selector" @click="togglePicker" :data-label="pickerTypeInfo?.label ?? '创作者'" :class="{ 'm-sidebar__type-selector--collapsed': isCollapsed }"
          @mouseenter="showTooltip($event, pickerTypeInfo?.label ?? '创作者')"
          @mouseleave="hideTooltip"
        >
          <div class="m-sidebar__avatar" :style="{ background: pickerTypeInfo?.color ?? 'linear-gradient(135deg, #8C57FF, #6C3DD9)' }">
            {{ pickerTypeInfo?.icon ?? '🎨' }}
          </div>
          <div v-show="!isCollapsed" class="m-sidebar__user-info">
            <div class="m-sidebar__user-name">{{ pickerTypeInfo?.label ?? '创作者' }}</div>
            <div class="m-sidebar__user-role">点击切换身份</div>
          </div>
          <span v-show="!isCollapsed" class="m-sidebar__chevron">{{ pickerOpen ? '▲' : '▼' }}</span>
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

    <!-- ═══════════════ MAIN AREA ═══════════════ -->
    <div class="m-main">
      <!-- ══ TOPBAR (transparent + blur, no border/shadow) ══ -->
      <header class="m-topbar">
        <div class="m-topbar__inner">
          <button v-if="isMobile" class="m-topbar__menu-btn" @click="sidebarOpen = true" aria-label="打开菜单">
            <i class="material-icons">menu</i>
          </button>

          <!-- Breadcrumb -->
          <div class="m-topbar__breadcrumb">
            <router-link to="/app" class="m-topbar__crumb">首页</router-link>
            <i class="material-icons m-topbar__sep">chevron_right</i>
            <span class="m-topbar__current">{{ currentBreadcrumb }}</span>
          </div>

          <!-- Right Actions -->
          <div class="m-topbar__actions">
            <button class="m-topbar__icon-btn" @click="toggleTheme" :title="isDark ? '切换亮色' : '切换暗色'">
              <i class="material-icons">{{ isDark ? 'light_mode' : 'dark_mode' }}</i>
            </button>
            <button class="m-topbar__icon-btn" aria-label="通知">
              <i class="material-icons">notifications</i>
              <span class="m-topbar__notif-dot"></span>
            </button>
            <router-link to="/app/messages" class="m-topbar__icon-btn" aria-label="消息">
              <i class="material-icons">mail</i>
            </router-link>
            <button class="m-topbar__icon-btn" aria-label="帮助">
              <i class="material-icons">help_outline</i>
            </button>
            <div class="m-topbar__user-menu" ref="userMenuRef">
              <button class="m-topbar__user-btn" @click="userMenuOpen = !userMenuOpen">
                <div class="m-topbar__avatar" style="background: linear-gradient(135deg, #8C57FF, #6C3DD9);">
                  {{ auth.user?.username?.[0] || auth.user?.email?.[0] || 'U' }}
                </div>
              </button>
              <div v-if="userMenuOpen" class="m-topbar__dropdown">
                <router-link to="/app/settings" class="m-topbar__dropdown-item">
                  <i class="material-icons">settings</i> 设置
                </router-link>
                <router-link to="/app/settings/subscriptions" class="m-topbar__dropdown-item">
                  <i class="material-icons">subscriptions</i> 订阅管理
                </router-link>
                <div class="m-topbar__divider"></div>
                <button class="m-topbar__dropdown-item m-topbar__dropdown-item--danger" @click="handleLogout">
                  <i class="material-icons">logout</i> 退出登录
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      <!-- ══ CONTENT ══ -->
      <main class="m-main__content">
        <router-view v-slot="{ Component }">
          <transition name="m-fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/useAuthStore'
import { useCreatorTypeStore } from '@/stores/useCreatorTypeStore'
import { getAllCreators } from '@/types/creator'
import type { CreatorType } from '@/types/creator'

interface NavItem {
  label: string
  path: string
  icon: string
  badge?: string
}

interface NavGroup {
  key: string
  label: string
  items: NavItem[]
}

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const typeStore = useCreatorTypeStore()

// Creator type picker
const allTypes = getAllCreators()
const currentType = computed(() => typeStore.getCurrentType())
const pickerOpen = ref(false)

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

function togglePicker() { pickerOpen.value = !pickerOpen.value }
function closePicker() { pickerOpen.value = false }
function selectType(type: CreatorType) { typeStore.switchType(type); pickerOpen.value = false }

function showTooltip(event: MouseEvent, text: string): void {
  if (!isCollapsed.value) return
  tooltipText.value = text
  tooltipVisible.value = true
  tooltipTarget.value = event.currentTarget as HTMLElement
  requestAnimationFrame(() => positionTooltip())
}

function hideTooltip(): void {
  tooltipVisible.value = false
  tooltipTarget.value = null
}

function positionTooltip(): void {
  if (!tooltipRef.value || !tooltipTarget.value || !isCollapsed.value) return
  const target = tooltipTarget.value.getBoundingClientRect()
  const sidebarRect = document.querySelector('.m-sidebar')?.getBoundingClientRect()
  if (!sidebarRect) return
  const top = target.top + target.height / 2 - 18
  tooltipRef.value.style.left = `${sidebarRect.right + 6}px`
  tooltipRef.value.style.top = `${top}px`
}

// State
const isCollapsed = ref(false)
const sidebarOpen = ref(false)
const userMenuOpen = ref(false)
const isDark = ref(false)
const userMenuRef = ref<HTMLElement | null>(null)
const isMobile = ref(window.innerWidth < 1024)

// Tooltip for collapsed state
const tooltipVisible = ref(false)
const tooltipText = ref('')
const tooltipRef = ref<HTMLElement | null>(null)
const tooltipTarget = ref<HTMLElement | null>(null)

// Breadcrumb
const currentBreadcrumb = computed(() => {
  const name = route.name as string
  if (!name) return '概览'
  const nameMap: Record<string, string> = {
    'dashboard': '概览', 'works': '作品管理', 'work-detail': '作品详情',
    'rights': '权益保护', 'risk-warning': '风险预警', 'risk-center': '风险中心',
    'messages': '消息中心', 'revenue': '收入中心', 'revenue-chart': '收入图表',
    'monitor': '侵权监测', 'ipr': 'IP登记', 'ipr-guide': '登记指南',
    'publish': '发布管理', 'settings': '系统设置', 'integrations': '平台集成',
    'projects': '项目管理', 'recycle': '回收站', 'watermarks': '水印预设',
    'metadata-templates': '元数据模板', 'work-variants': '作品变体',
    'work-versions': '作品版本', 'culling': '作品筛选', 'subscriptions': '订阅管理',
    'commissions': '佣金管理', 'commission-detail': '佣金详情',
    'illustrator': '插画师', 'photographer': '摄影师', 'video': '视频创作者',
    'craftsman': '工匠', 'musician': '音乐人', 'writer': '作家',
    'ai-growth': 'AI增长', 'content-pipeline': '内容管道', 'growth-stages': '成长阶段',
    'credit-improvement': '信用提升', 'capability': '能力评估', 'navigation': '创作者导航',
    'contract-market': '合约市场', 'supply': '供应端', 'contract-risk': '合约风险',
    'enforcement': '维权中心', 'enforcement-roi': '维权ROI', 'private-traffic': '私域流量',
    'multimarket': '多市场', 'case-studies': '案例库', 'copyright-guide': '版权指南',
    'fork-merge': '分支合并', 'negotiation': '谈判中心', 'scr-dash': 'SCR看板',
    'tax-settlement': '税务结算', 'distribution-hub': '分发中心', 'attribution': '归因分析',
  }
  return nameMap[name] || name
})

// ═══════════════════════════════════════════════════════════
// NAVIGATION GROUPS (flat structure — no nesting)
// ═══════════════════════════════════════════════════════════
const navGroups: NavGroup[] = [
  {
    key: 'dashboards', label: '概览',
    items: [
      { label: '首页', path: '/app', icon: 'home', badge: '' },
      { label: '数据看板', path: '/app/dashboard', icon: 'bar_chart', badge: '' },
    ]
  },
  {
    key: 'works', label: '作品管理',
    items: [
      { label: '作品管理', path: '/app/works', icon: 'grid_view', badge: '150' },
      { label: '作品筛选', path: '/app/works/cull', icon: 'filter_list', badge: '' },
      { label: '作品版本', path: '/app/works/:id/versions', icon: 'upgrade', badge: '' },
      { label: '作品变体', path: '/app/works/:id/variants', icon: 'account_tree', badge: '' },
      { label: '回收站', path: '/app/recycle', icon: 'delete_outline', badge: '' },
    ]
  },
  {
    key: 'rights', label: '权益保护',
    items: [
      { label: '权益保护', path: '/app/rights', icon: 'security', badge: '5' },
      { label: '侵权监测', path: '/app/monitor', icon: 'visibility', badge: '' },
      { label: '风险预警', path: '/app/risk-warning', icon: 'warning_amber', badge: '' },
      { label: '风险中心', path: '/app/risk-center', icon: 'error_outline', badge: '' },
      { label: '维权中心', path: '/app/enforcement', icon: 'gavel', badge: '' },
      { label: '维权ROI', path: '/app/enforcement-roi', icon: 'analytics', badge: '' },
      { label: 'IP登记', path: '/app/ipr', icon: 'description', badge: '' },
      { label: '登记指南', path: '/app/ipr-guide', icon: 'school', badge: '' },
      { label: '版权指南', path: '/app/copyright-guide', icon: 'menu_book', badge: '' },
    ]
  },
  {
    key: 'growth', label: 'AI增长',
    items: [
      { label: 'AI增长引擎', path: '/app/ai-growth', icon: 'auto_awesome', badge: '' },
      { label: '内容管道', path: '/app/content-pipeline', icon: 'production_quantity_limits', badge: '' },
      { label: '成长阶段', path: '/app/growth-stages', icon: 'trending_up', badge: '' },
      { label: '信用提升', path: '/app/credit-improvement', icon: 'rocket_launch', badge: '' },
      { label: '能力评估', path: '/app/capability', icon: 'assessment', badge: '' },
    ]
  },
  {
    key: 'business', label: '商业转化',
    items: [
      { label: '合约市场', path: '/app/contract-market', icon: 'handshake', badge: '' },
      { label: '供应端', path: '/app/supply', icon: 'warehouse', badge: '' },
      { label: '合约风险', path: '/app/contract-risk', icon: 'warning', badge: '' },
      { label: '多市场', path: '/app/multimarket', icon: 'public', badge: '' },
      { label: '私域流量', path: '/app/private-traffic', icon: 'people_outline', badge: '' },
      { label: '保险市场', path: '/app/insurance', icon: 'shield', badge: '' },
      { label: '发布管理', path: '/app/publish', icon: 'publish', badge: '' },
      { label: '收入中心', path: '/app/revenue', icon: 'payments', badge: '' },
      { label: '收入图表', path: '/app/revenue/chart', icon: 'show_chart', badge: '' },
      { label: '案例库', path: '/app/case-studies', icon: 'folder_special', badge: '' },
      { label: '归因分析', path: '/app/attribution', icon: 'source', badge: '' },
    ]
  },
  {
    key: 'tools', label: '工具',
    items: [
      { label: '插画师', path: '/app/illustrator', icon: 'brush', badge: '' },
      { label: '摄影师', path: '/app/photographer', icon: 'photo_camera', badge: '' },
      { label: '视频创作者', path: '/app/video', icon: 'videocam', badge: '' },
      { label: '音乐人', path: '/app/musician', icon: 'music_note', badge: '' },
      { label: '作家', path: '/app/writer', icon: 'edit', badge: '' },
      { label: '工匠', path: '/app/craftsman', icon: 'handyman', badge: '' },
      { label: '创作者导航', path: '/app/navigation', icon: 'navigation', badge: '' },
      { label: '项目', path: '/app/projects', icon: 'folder', badge: '' },
      { label: 'Fork/Merge', path: '/app/fork-merge', icon: 'merge_type', badge: '' },
      { label: '谈判中心', path: '/app/negotiation', icon: 'chat', badge: '' },
      { label: 'SCR看板', path: '/app/scr', icon: 'view_agenda', badge: '' },
      { label: '税务结算', path: '/app/tax', icon: 'tax_alert', badge: '' },
      { label: '分发中心', path: '/app/distribution', icon: 'send', badge: '' },
      { label: '佣金管理', path: '/app/business/commissions', icon: 'account_balance_wallet', badge: '' },
    ]
  },
  {
    key: 'system', label: '系统',
    items: [
      { label: '设置', path: '/app/settings', icon: 'settings', badge: '' },
      { label: '订阅管理', path: '/app/settings/subscriptions', icon: 'subscriptions', badge: '' },
      { label: '水印预设', path: '/app/settings/watermarks', icon: 'water_drop', badge: '' },
      { label: '元数据模板', path: '/app/settings/templates', icon: 'template', badge: '' },
      { label: '平台集成', path: '/app/integrations', icon: 'integration_instructions', badge: '' },
      { label: '消息中心', path: '/app/messages', icon: 'mail', badge: '3' },
    ]
  },
]

// ═══════════════════════════════════════════════════════════
// INTERACTIONS
// ═══════════════════════════════════════════════════════════
function isActive(path: string): boolean {
  const currentPath = route.path
  if (path.includes(':')) {
    const base = path.replace(/\/:[^/]+/g, '/[^/]+')
    return new RegExp(`^${base}`).test(currentPath)
  }
  return currentPath === `/app${path}` || currentPath.startsWith(`/app${path}/`)
}

function closeMobile(): void {
  if (isMobile.value) sidebarOpen.value = false
}

function toggleTheme(): void {
  isDark.value = !isDark.value
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
}

function handleLogout(): void {
  auth.logout()
  router.push('/login')
}

function handleClickOutside(e: MouseEvent): void {
  if (userMenuRef.value && !userMenuRef.value.contains(e.target as Node)) {
    userMenuOpen.value = false
  }
}

onMounted(() => {
  window.addEventListener('resize', () => {
    isMobile.value = window.innerWidth < 1024
    if (!isMobile.value) sidebarOpen.value = false
  })
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
/* ═══════════════════════════════════════════════════════════
   LAYOUT
   ═══════════════════════════════════════════════════════════ */
.m-layout {
  display: flex;
  min-height: 100dvh;
  background: var(--m-bg-subtle, #F4F5FA);
  font-family: var(--m-font-family, 'Inter', sans-serif);
}

.m-layout--mobile .m-sidebar { transform: translateX(0); }

.m-layout__overlay {
  position: fixed; inset: 0;
  background: rgba(0, 0, 0, 0.5); z-index: 99;
}

/* ═══════════════════════════════════════════════════════════
   SIDEBAR — 与页面同色，无 border-right，无缝衔接
   ═══════════════════════════════════════════════════════════ */
.m-sidebar {
  position: fixed;
  top: 0; left: 0; bottom: 0;
  width: var(--m-sidebar-width, 256px);
  background: var(--m-bg-subtle, #F4F5FA);  /* 同页面背景色 */
  display: flex; flex-direction: column;
  z-index: 100;
  transition: width 250ms cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}
.m-sidebar--collapsed { width: var(--m-sidebar-collapsed, 80px); overflow: visible; }

/* ── Brand Row ── */
.m-sidebar__brand {
  display: flex; align-items: center; gap: 8px;
  padding: 0 20px; height: 64px; flex-shrink: 0;
}
.m-sidebar--collapsed .m-sidebar__brand { justify-content: center; padding: 0 16px; }

.m-sidebar__logo {
  display: flex; align-items: center; gap: 8px;
  text-decoration: none; color: var(--m-on-surface, #2E263D); flex: 1; min-width: 0;
}
.m-sidebar--collapsed .m-sidebar__logo { flex: none; }
.m-sidebar--collapsed .m-sidebar__title { display: none; }

.m-sidebar__logo svg { flex-shrink: 0; color: var(--m-primary, #8C57FF); }

.m-sidebar__title {
  font-size: 1.125rem; font-weight: 700;
  white-space: nowrap;
  background: linear-gradient(135deg, #8C57FF, #6C3DD9);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}

.m-sidebar__collapse-btn,
.m-sidebar__expand-btn {
  width: 28px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  border: none; background: transparent;
  color: var(--m-grey-500, #9E9E9E);
  border-radius: 8px; cursor: pointer;
  flex-shrink: 0;
  transition: all 150ms;
}
.m-sidebar__collapse-btn:hover,
.m-sidebar__expand-btn:hover {
  background: rgba(140, 87, 255, 0.08); color: var(--m-primary, #8C57FF);
}

/* ── Nav ── */
.m-sidebar__nav {
  flex: 1; overflow-y: auto;
  padding: 0 12px 16px;
  scrollbar-width: none;
}
.m-sidebar__nav::-webkit-scrollbar { display: none; }

/* ── Section Divider (Materio nav-section-title) ── */
.m-sidebar__section {
  font-size: 0.6875rem; font-weight: 500;
  letter-spacing: 0.05em; text-transform: uppercase;
  color: var(--m-on-surface, #2E263D);
  opacity: 0.4;
  padding: 16px 12px 6px;
  user-select: none;
}

/* ── Items ── */
.m-sidebar__items {
  list-style: none; margin: 0; padding: 0;
}

.m-sidebar__link {
  display: flex; align-items: center; gap: 10px;
  padding: 0 12px;               /* 统一内边距 */
  height: 38px;
  font-size: 0.9375rem;
  color: var(--m-grey-700, #616161);
  text-decoration: none;
  transition: all 150ms cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  cursor: pointer;
  /* 所有层级统一的 paddingLeft，消除缩进差异 */
  margin-left: 0;
}

.m-sidebar__link:hover {
  background: rgba(var(--m-primary-rgb, 140, 87, 255), 0.06);
  color: var(--m-on-surface, #2E263D);
}

/* ── Active state — Materio 风格：底色加深 + 左侧竖线 + 白色文字 ── */
.m-sidebar__link--active {
  background: rgba(var(--m-primary-rgb, 140, 87, 255), 0.12);
  color: var(--m-primary, #8C57FF);
  font-weight: 600;
}
.m-sidebar__link--active::before {
  content: '';
  position: absolute;
  left: 0; top: 50%;
  transform: translateY(-50%);
  width: 3px; height: 60%;
  background: var(--m-primary, #8C57FF);
  border-radius: 0 2px 2px 0;
}

.m-sidebar__link-icon {
  font-size: 18px; flex-shrink: 0; width: 20px; text-align: center;
  opacity: 0.85;
  transition: opacity 150ms;
}
.m-sidebar__link:hover .m-sidebar__link-icon { opacity: 1; }
.m-sidebar__link--active .m-sidebar__link-icon { opacity: 1; }

.m-sidebar__link-label { flex: 1; min-width: 0; white-space: nowrap; }

.m-sidebar__badge {
  background: rgba(255, 255, 255, 0.25);
  color: inherit;
  font-size: 0.6875rem; font-weight: 600;
  padding: 1px 6px; border-radius: 100px;
  flex-shrink: 0;
}
.m-sidebar__link--active .m-sidebar__badge {
  background: rgba(255, 255, 255, 0.3);
}

/* ── Collapsed hover tooltip ── */
.m-sidebar--collapsed .m-sidebar__link-label,
.m-sidebar--collapsed .m-sidebar__badge { display: none; }
.m-sidebar--collapsed .m-sidebar__nav ul { padding: 0 12px; }

.m-sidebar--collapsed .m-sidebar__link {
  position: relative;
  justify-content: center;
  padding: 0 16px;
}
.m-sidebar--collapsed .m-sidebar__section { display: none; }

/* JS tooltip */
.m-tooltip {
  position: fixed;
  white-space: nowrap;
  background: var(--m-surface, #FFFFFF);
  border: 1px solid var(--m-border, rgba(46,38,61,0.12));
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--m-on-surface, #2E263D);
  box-shadow: var(--m-shadow-sm, 0 1px 2px rgba(46,38,61,0.08));
  z-index: 300;
  pointer-events: none;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* ── Footer — Type Selector ── */
.m-sidebar__footer {
  padding: 12px; margin: 0 4px 8px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 12px;
  flex-shrink: 0;
}
.m-sidebar__type-selector {
  display: flex; align-items: center; gap: 10px;
  cursor: pointer; padding: 6px 8px; margin: -6px -8px;
  border-radius: var(--m-radius-sm, 8px);
  transition: background 150ms; user-select: none;
  position: relative;
}
.m-sidebar__type-selector:hover { background: rgba(var(--m-primary-rgb, 140, 87, 255), 0.08); }
.m-sidebar__avatar {
  width: 36px; height: 36px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.1rem; flex-shrink: 0;
  background: linear-gradient(135deg, #8C57FF, #6C3DD9);
}
.m-sidebar__user-info { min-width: 0; flex: 1; }
.m-sidebar__user-name {
  font-size: 0.8125rem; font-weight: 600; color: var(--m-on-surface, #2E263D);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.m-sidebar__user-role { font-size: 0.6875rem; color: var(--m-grey-500, #9E9E9E); }
.m-sidebar__chevron { font-size: 0.6rem; color: var(--m-grey-400, #BDBDBD); flex-shrink: 0; }

/* Footer collapsed state */
.m-sidebar--collapsed .m-sidebar__type-selector--collapsed { justify-content: center; padding: 8px; }

/* Type picker popup */
.type-picker-overlay { position: fixed; inset: 0; z-index: 199; }
.type-picker {
  position: fixed; bottom: 80px; left: 10px;
  max-height: 320px; overflow-y: auto;
  background: var(--m-bg-subtle, #F4F5FA);
  border: 1px solid var(--m-border, rgba(46,38,61,0.12));
  border-radius: var(--m-radius-sm, 8px);
  box-shadow: var(--m-shadow-lg, 0 10px 15px -3px rgba(46,38,61,0.1));
  padding: 12px; z-index: 200; width: 200px;
}
.picker-title {
  font-size: 0.6875rem; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.05em;
  color: var(--m-grey-500, #9E9E9E);
  padding: 4px 8px 8px;
}
.picker-item {
  display: flex; align-items: center; gap: 10px;
  width: 100%; padding: 10px;
  border: none; border-radius: var(--m-radius-sm, 8px);
  background: transparent; cursor: pointer;
  font-size: 0.85rem; font-weight: 500;
  color: var(--m-on-surface, #2E263D);
  text-align: left; transition: background 150ms;
}
.picker-item:hover { background: rgba(var(--m-primary-rgb, 140, 87, 255), 0.08); }
.picker-item.active { background: rgba(var(--m-primary-rgb, 140, 87, 255), 0.12); color: var(--m-primary, #8C57FF); font-weight: 600; }
.picker-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.picker-fade-enter-active, .picker-fade-leave-active { transition: opacity 150ms ease; }
.picker-fade-enter-from, .picker-fade-leave-to { opacity: 0; }

/* ═══════════════════════════════════════════════════════════
   MAIN — 透明顶部导航
   ═══════════════════════════════════════════════════════════ */
.m-main {
  flex: 1;
  margin-inline-start: var(--m-sidebar-width, 256px);
  display: flex; flex-direction: column;
  height: 100dvh;
  background: var(--m-bg-subtle, #F4F5FA);
  transition: margin-inline-start 250ms cubic-bezier(0.4, 0, 0.2, 1);
}

.m-layout--collapsed .m-main { margin-inline-start: var(--m-sidebar-collapsed, 80px); }

/* ── Topbar — transparent, no border, no shadow ── */
.m-topbar {
  position: sticky; top: 0;
  z-index: 200;
  height: 64px;
  background: transparent;          /* 透明，不遮挡侧边栏 */
  border-bottom: none;              /* 无边框 */
  flex-shrink: 0;
}

.m-topbar__inner {
  display: flex; align-items: center; gap: 16px;
  padding: 0 24px; height: 100%;
}

.m-topbar__menu-btn {
  display: none;
  width: 36px; height: 36px;
  align-items: center; justify-content: center;
  border: none; background: transparent;
  color: var(--m-grey-600, #757575);
  border-radius: 8px; cursor: pointer;
}

/* ── Breadcrumb ── */
.m-topbar__breadcrumb {
  display: flex; align-items: center; gap: 4px;
  font-size: 0.8125rem;
  color: var(--m-grey-500, #9E9E9E);
}
.m-topbar__crumb {
  color: var(--m-grey-500, #9E9E9E); text-decoration: none;
  transition: color 150ms;
}
.m-topbar__crumb:hover { color: var(--m-primary, #8C57FF); }
.m-topbar__sep { font-size: 16px; color: var(--m-grey-400, #BDBDBD); }
.m-topbar__current {
  color: var(--m-on-surface, #2E263D); font-weight: 500;
}

/* ── Actions ── */
.m-topbar__actions {
  display: flex; align-items: center; gap: 4px;
  margin-inline-start: auto;
}
.m-topbar__icon-btn {
  width: 36px; height: 36px;
  display: flex; align-items: center; justify-content: center;
  border: none; background: transparent;
  color: var(--m-grey-600, #757575);
  border-radius: 8px; cursor: pointer;
  position: relative;
  transition: all 150ms;
  text-decoration: none;
}
.m-topbar__icon-btn:hover { background: rgba(var(--m-primary-rgb, 140, 87, 255), 0.08); color: var(--m-primary, #8C57FF); }

.m-topbar__notif-dot {
  position: absolute; top: 6px; right: 6px;
  width: 8px; height: 8px;
  background: var(--m-error, #FF4C51);
  border-radius: 50%;
  border: 2px solid transparent;  /* 透明底，不切到 topbar */
}

/* ── User Menu ── */
.m-topbar__user-menu { position: relative; }
.m-topbar__user-btn {
  width: 36px; height: 36px;
  border: none; background: transparent;
  border-radius: 50%; cursor: pointer; padding: 0; overflow: hidden;
}
.m-topbar__user-btn:hover { opacity: 0.8; }
.m-topbar__avatar {
  width: 100%; height: 100%; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.8125rem; font-weight: 600; color: white;
}
.m-topbar__dropdown {
  position: absolute; top: calc(100% + 8px); right: 0;
  min-width: 200px;
  background: var(--m-surface, #FFFFFF);
  border: 1px solid var(--m-border, rgba(46, 38, 61, 0.12));
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(46, 38, 61, 0.12);
  padding: 8px; z-index: 300;
}
.m-topbar__dropdown-item {
  display: flex; align-items: center; gap: 10px;
  width: 100%; padding: 8px 12px;
  font-size: 0.875rem; color: var(--m-on-surface, #2E263D);
  border: none; background: transparent;
  text-align: left; cursor: pointer;
  border-radius: 8px;
  transition: background 150ms;
  text-decoration: none;
}
.m-topbar__dropdown-item:hover { background: var(--m-bg-subtle, #F4F5FA); }
.m-topbar__dropdown-item--danger { color: var(--m-error, #FF4C51); }
.m-topbar__dropdown-item--danger:hover { background: rgba(255, 76, 81, 0.08); }
.m-topbar__divider { height: 1px; background: var(--m-border, rgba(46, 38, 61, 0.12)); margin: 8px 0; }

/* ══ CONTENT ══ */
.m-main__content { flex: 1; padding: 24px; overflow-y: auto; background: var(--m-bg-subtle, #F4F5FA); scrollbar-width: none; }
.m-main__content::-webkit-scrollbar { display: none; }

/* ═══════════════════════════════════════════════════════════
   TRANSITIONS
   ═══════════════════════════════════════════════════════════ */

/* ═══════════════════════════════════════════════════════════
   TRANSITIONS
   ═══════════════════════════════════════════════════════════ */
.m-fade-enter-active, .m-fade-leave-active { transition: opacity 150ms; }
.m-fade-enter-from, .m-fade-leave-to { opacity: 0; }

/* ═══════════════════════════════════════════════════════════
   RESPONSIVE
   ═══════════════════════════════════════════════════════════ */
@media (max-width: 1023px) {
  .m-sidebar { transform: translateX(-100%); }
  .m-main { margin-inline-start: 0 !important; }
  .m-topbar__menu-btn { display: flex; }
  .m-topbar__breadcrumb { display: none; }
}
</style>

<style>
/* ── Materio Layout Global Overrides ── */
/* 内容区卡片使用浅紫底，与页面背景色统一 */
.m-main__content .m-card,
.m-main__content .card,
.m-main__content .stat-card {
  background: var(--m-bg-subtle, #F4F5FA) !important;
  border-color: var(--m-border, rgba(46, 38, 61, 0.12));
}
/* ── Materio Card Base ── */
.m-card {
  background: var(--m-surface, #FFFFFF);
  border-radius: var(--m-radius-lg, 12px);
  border: none;
  box-shadow: var(--m-shadow-xs, 0 0.125rem 0.25rem rgba(46, 38, 61, 0.16));
  overflow: hidden;
}
.m-card__header {
  padding: var(--m-space-4, 1rem) var(--m-space-6, 1.5rem);
  border-bottom: 1px solid var(--m-border, rgba(46, 38, 61, 0.12));
  display: flex; align-items: center; gap: var(--m-space-3, 0.75rem);
}
.m-card__body { padding: var(--m-space-6, 1.5rem); }

/* ── Grid ── */
.m-row { display: grid; gap: var(--m-space-6, 1.5rem); }
.m-row--2 { grid-template-columns: repeat(2, 1fr); }
.m-row--3 { grid-template-columns: repeat(3, 1fr); }
.m-row--4 { grid-template-columns: repeat(4, 1fr); }

/* ── Stat Card ── */
.m-stat-card {
  background: var(--m-surface, #FFFFFF);
  border-radius: var(--m-radius-lg, 12px);
  border: none;
  box-shadow: var(--m-shadow-xs, 0 0.125rem 0.25rem rgba(46, 38, 61, 0.16));
  padding: var(--m-space-6, 1.5rem);
  display: flex; flex-direction: column; gap: var(--m-space-2, 0.5rem);
}
.m-stat-card__label { font-size: var(--m-font-size-sm, 0.8125rem); color: var(--m-grey-500, #9E9E9E); font-weight: 500; }
.m-stat-card__value { font-size: var(--m-font-size-xl, 1.5rem); font-weight: 700; color: var(--m-on-surface, #2E263D); line-height: 1.2; }
.m-stat-card__change { font-size: var(--m-font-size-xs, 0.6875rem); font-weight: 500; }
.m-stat-card__change--up { color: var(--m-success, #56CA00); }
.m-stat-card__change--down { color: var(--m-error, #FF4C51); }

/* ── Page Header ── */
.m-page-header { margin-bottom: var(--m-space-6, 1.5rem); }
.m-page-header__title { font-size: 1.5rem; font-weight: 700; color: var(--m-on-surface, #2E263D); margin: 0 0 var(--m-space-2, 0.5rem); }
.m-page-header__desc { font-size: var(--m-font-size-sm, 0.8125rem); color: var(--m-grey-500, #9E9E9E); margin: 0; }

/* ── Section Title ── */
.m-section-title {
  font-size: var(--m-font-size-md, 1.0625rem); font-weight: 600;
  color: var(--m-on-surface, #2E263D);
  margin: 0 0 var(--m-space-4, 1rem); padding-bottom: var(--m-space-2, 0.5rem);
  border-bottom: 2px solid var(--m-primary, #8C57FF);
  display: inline-block;
}

/* ── Chip ── */
.m-chip {
  display: inline-flex; align-items: center;
  padding: 0.25rem 0.625rem; border-radius: 100px;
  font-size: 0.6875rem; font-weight: 500; gap: 0.25rem;
}
.m-chip--primary { background: rgba(var(--m-primary-rgb, 140, 87, 255), 0.12); color: var(--m-primary, #8C57FF); }
.m-chip--success { background: rgba(var(--m-success-rgb, 86, 202, 0), 0.12); color: var(--m-success, #56CA00); }
.m-chip--warning { background: rgba(var(--m-warning-rgb, 255, 180, 0), 0.12); color: var(--m-warning, #FFB400); }
.m-chip--error { background: rgba(var(--m-error-rgb, 255, 76, 81), 0.12); color: var(--m-error, #FF4C51); }
.m-chip--info { background: rgba(var(--m-info-rgb, 22, 177, 255), 0.12); color: var(--m-info, #16B1FF); }
</style>
