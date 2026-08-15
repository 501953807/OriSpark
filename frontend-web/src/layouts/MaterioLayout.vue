<!-- Materio Layout — OriStudio (创作者工作台)
     参照: https://demos.themeselection.com/materio-vuetify-vuejs-admin-template/demo-1/
     左右布局：左侧侧边栏（分组菜单）+ 右上导航栏 + 右下内容区
     Material Icons 图标系统
     Materio 蓝色主题 (#5585FF)
-->
<template>
  <div class="m-layout" :class="{ 'm-layout--collapsed': isCollapsed, 'm-layout--mobile': isMobile }">
    <!-- Mobile overlay -->
    <div v-if="isMobile && sidebarOpen" class="m-layout__overlay" @click="sidebarOpen = false" />

    <!-- ═══════════════════════════════════════════════════════════
         LEFT SIDEBAR — Materio 风格
         ═══════════════════════════════════════════════════════════ -->
    <aside class="m-sidebar" :class="{ 'm-sidebar--collapsed': isCollapsed, 'm-sidebar--open': sidebarOpen }">
      <!-- Brand -->
      <div class="m-sidebar__header">
        <router-link to="/app" class="m-sidebar__brand">
          <svg class="m-sidebar__logo" width="28" height="22" viewBox="0 0 30 24" fill="none">
            <path d="M1.476 0.435L6.799 3.722C7.084 3.898 7.258 4.21 7.258 4.546V19.56C7.258 19.901 7.079 20.216 6.787 20.391L1.465 23.578C1.006 23.852 0.412 23.703 0.137 23.244C0.047 23.094 0 22.922 0 22.747V1.259C0 0.724 0.433 0.291 0.968 0.291C1.147 0.291 1.323 0.341 1.476 0.435Z" fill="currentColor"/>
            <path d="M28.525 0.432L23.203 3.707C22.916 3.883 22.742 4.196 22.742 4.532V19.56C22.742 19.901 22.921 20.216 23.213 20.391L28.535 23.578C28.994 23.852 29.588 23.703 29.863 23.244C29.952 23.094 30 22.922 30 22.747V1.256C30 0.722 29.567 0.288 29.032 0.288C28.853 0.288 28.678 0.338 28.525 0.432Z" fill="currentColor"/>
            <path d="M1.473 0.427L15 8.722V16.709L0 8.114V1.253C0 0.718 0.433 0.285 0.968 0.285C1.146 0.285 1.321 0.334 1.473 0.427Z" fill="currentColor"/>
            <path d="M28.527 0.427L15 8.722V16.709L30 8.114V1.253C30 0.718 29.567 0.285 29.032 0.285C28.854 0.285 28.679 0.334 28.527 0.427Z" fill="currentColor"/>
          </svg>
          <span v-show="!isCollapsed" class="m-sidebar__title">OriStudio</span>
        </router-link>
        <button v-show="!isCollapsed" class="m-sidebar__collapse-btn" @click="isCollapsed = !isCollapsed" aria-label="折叠侧边栏">
          <i class="material-icons">chevron_left</i>
        </button>
        <button v-show="isCollapsed" class="m-sidebar__expand-btn" @click="isCollapsed = false" aria-label="展开侧边栏">
          <i class="material-icons">chevron_right</i>
        </button>
      </div>

      <!-- Search -->
      <div v-show="!isCollapsed" class="m-sidebar__search">
        <i class="material-icons m-sidebar__search-icon">search</i>
        <input v-model="searchQuery" class="m-sidebar__search-input" placeholder="搜索功能..." @keydown.enter="handleSearch" />
        <kbd class="m-sidebar__search-kbd">⌘K</kbd>
      </div>

      <!-- Navigation -->
      <nav class="m-sidebar__nav">
        <template v-for="group in navGroups" :key="group.key">
          <!-- Group Header -->
          <div class="m-sidebar__group">
            <button class="m-sidebar__group-header" @click="toggleGroup(group.key)">
              <i class="material-icons m-sidebar__group-icon">{{ group.icon }}</i>
              <span v-show="!isCollapsed" class="m-sidebar__group-label">{{ group.label }}</span>
              <span v-show="!isCollapsed && group.badge" class="m-sidebar__group-badge">{{ group.badge }}</span>
              <i v-show="!isCollapsed" class="material-icons m-sidebar__group-arrow">{{ expandedGroups.includes(group.key) ? 'expand_less' : 'expand_more' }}</i>
            </button>

            <!-- Group Items -->
            <ul v-show="!isCollapsed && expandedGroups.includes(group.key)" class="m-sidebar__group-items">
              <li v-for="item in group.items" :key="item.path">
                <router-link
                  :to="item.path"
                  class="m-sidebar__item"
                  :class="{ 'm-sidebar__item--active': isActive(item.path) }"
                  @click="closeMobile()"
                >
                  <i class="material-icons m-sidebar__item-icon">{{ item.icon }}</i>
                  <span class="m-sidebar__item-label">{{ item.label }}</span>
                  <span v-if="item.badge" class="m-sidebar__badge">{{ item.badge }}</span>
                </router-link>
              </li>
            </ul>
          </div>
        </template>
      </nav>

      <!-- Footer — User Card -->
      <div v-show="!isCollapsed" class="m-sidebar__footer">
        <div class="m-sidebar__user">
          <div class="m-sidebar__avatar" :style="{ background: 'linear-gradient(135deg, #5585FF, #2A52B0)' }">
            {{ auth.user?.username?.[0] || auth.user?.email?.[0] || 'U' }}
          </div>
          <div class="m-sidebar__user-info">
            <div class="m-sidebar__user-name">{{ auth.user?.username || '创作者' }}</div>
            <div class="m-sidebar__user-role">{{ auth.user?.role || 'Creator' }}</div>
          </div>
          <button class="m-sidebar__logout-btn" @click="handleLogout" title="退出登录">
            <i class="material-icons">logout</i>
          </button>
        </div>
      </div>
    </aside>

    <!-- ═══════════════════════════════════════════════════════════
         MAIN AREA
         ═══════════════════════════════════════════════════════════ -->
    <div class="m-main">
      <!-- ══ TOPBAR ══ -->
      <header class="m-topbar">
        <div class="m-topbar__inner">
          <!-- Mobile menu toggle -->
          <button v-if="isMobile" class="m-topbar__menu-btn" @click="sidebarOpen = true" aria-label="打开菜单">
            <i class="material-icons">menu</i>
          </button>

          <!-- Breadcrumb -->
          <div class="m-topbar__breadcrumb">
            <router-link to="/app" class="m-topbar__breadcrumb-item">首页</router-link>
            <i class="material-icons m-topbar__breadcrumb-sep">chevron_right</i>
            <span class="m-topbar__breadcrumb-current">{{ currentBreadcrumb }}</span>
          </div>

          <!-- Right Actions -->
          <div class="m-topbar__actions">
            <!-- Theme Toggle -->
            <button class="m-topbar__icon-btn" @click="toggleTheme" :title="isDark ? '切换亮色' : '切换暗色'">
              <i class="material-icons">{{ isDark ? 'light_mode' : 'dark_mode' }}</i>
            </button>

            <!-- Notifications -->
            <button class="m-topbar__icon-btn" aria-label="通知">
              <i class="material-icons">notifications</i>
              <span class="m-topbar__notif-dot"></span>
            </button>

            <!-- Messages -->
            <router-link to="/app/messages" class="m-topbar__icon-btn" aria-label="消息">
              <i class="material-icons">mail</i>
            </router-link>

            <!-- Help -->
            <button class="m-topbar__icon-btn" aria-label="帮助">
              <i class="material-icons">help_outline</i>
            </button>

            <!-- User Menu -->
            <div class="m-topbar__user-menu" ref="userMenuRef">
              <button class="m-topbar__user-btn" @click="userMenuOpen = !userMenuOpen">
                <div class="m-topbar__avatar" :style="{ background: 'linear-gradient(135deg, #5585FF, #2A52B0)' }">
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
                <div class="m-topbar__dropdown-divider"></div>
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

interface NavItem {
  label: string
  path: string
  icon: string
  badge?: string
}

interface NavGroup {
  key: string
  label: string
  icon: string
  badge?: string
  items: NavItem[]
}

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

// State
const isCollapsed = ref(false)
const sidebarOpen = ref(false)
const userMenuOpen = ref(false)
const isDark = ref(false)
const searchQuery = ref('')
const userMenuRef = ref<HTMLElement | null>(null)
const isMobile = ref(window.innerWidth < 1024)

// Expanded groups (default: all open)
const expandedGroups = ref<string[]>(['dashboards', 'works', 'rights', 'growth', 'business', 'tools', 'system'])

// Breadcrumb
const currentBreadcrumb = computed(() => {
  const name = route.name as string
  if (!name) return '概览'
  const nameMap: Record<string, string> = {
    'dashboard': '概览',
    'works': '作品管理',
    'work-detail': '作品详情',
    'rights': '权益保护',
    'risk-warning': '风险预警',
    'risk-center': '风险中心',
    'messages': '消息中心',
    'revenue': '收入中心',
    'revenue-chart': '收入图表',
    'monitor': '侵权监测',
    'ipr': 'IP登记',
    'ipr-guide': '登记指南',
    'publish': '发布管理',
    'settings': '系统设置',
    'integrations': '平台集成',
    'projects': '项目管理',
    'recycle': '回收站',
    'watermarks': '水印预设',
    'metadata-templates': '元数据模板',
    'work-variants': '作品变体',
    'work-versions': '作品版本',
    'culling': '作品筛选',
    'subscriptions': '订阅管理',
    'commissions': '佣金管理',
    'commission-detail': '佣金详情',
    'illustrator': '插画师',
    'photographer': '摄影师',
    'video': '视频创作者',
    'craftsman': '工匠',
    'musician': '音乐人',
    'writer': '作家',
    'ai-growth': 'AI增长',
    'content-pipeline': '内容管道',
    'growth-stages': '成长阶段',
    'credit-improvement': '信用提升',
    'capability': '能力评估',
    'navigation': '创作者导航',
    'contract-market': '合约市场',
    'supply': '供应端',
    'contract-risk': '合约风险',
    'enforcement': '维权中心',
    'enforcement-roi': '维权ROI',
    'private-traffic': '私域流量',
    'multimarket': '多市场',
    'case-studies': '案例库',
    'copyright-guide': '版权指南',
    'fork-merge': '分支合并',
    'negotiation': '谈判中心',
    'scr-dash': 'SCR看板',
    'tax-settlement': '税务结算',
    'distribution-hub': '分发中心',
    'attribution': '归因分析',
  }
  return nameMap[name] || name
})

// ═══════════════════════════════════════════════════════════
// NAVIGATION GROUPS — Materio Demo-1 风格
// ═══════════════════════════════════════════════════════════
const navGroups: NavGroup[] = [
  // ── Dashboards ──
  {
    key: 'dashboards', label: 'Dashboards', icon: 'dashboard', badge: '',
    items: [
      { label: '概览', path: '/app', icon: 'home', badge: '' },
      { label: '数据看板', path: '/app/dashboard', icon: 'bar_chart', badge: '' },
    ]
  },
  // ── Works ──
  {
    key: 'works', label: 'Works', icon: 'inventory_2', badge: '150',
    items: [
      { label: '作品管理', path: '/app/works', icon: 'grid_view', badge: '' },
      { label: '作品筛选', path: '/app/works/cull', icon: 'filter_list', badge: '' },
      { label: '作品版本', path: '/app/works/:id/versions', icon: 'upgrade', badge: '' },
      { label: '作品变体', path: '/app/works/:id/variants', icon: 'account_tree', badge: '' },
      { label: '回收站', path: '/app/recycle', icon: 'delete_outline', badge: '' },
    ]
  },
  // ── Rights ──
  {
    key: 'rights', label: 'Rights', icon: 'verified_user', badge: '5',
    items: [
      { label: '权益保护', path: '/app/rights', icon: 'security', badge: '' },
      { label: '侵权监测', path: '/app/monitor', icon: 'visibility', badge: '5' },
      { label: '风险预警', path: '/app/risk-warning', icon: 'warning_amber', badge: '' },
      { label: '风险中心', path: '/app/risk-center', icon: 'error_outline', badge: '' },
      { label: '维权中心', path: '/app/enforcement', icon: 'gavel', badge: '' },
      { label: '维权ROI', path: '/app/enforcement-roi', icon: 'analytics', badge: '' },
      { label: 'IP登记', path: '/app/ipr', icon: 'description', badge: '' },
      { label: '登记指南', path: '/app/ipr-guide', icon: 'school', badge: '' },
      { label: '版权指南', path: '/app/copyright-guide', icon: 'menu_book', badge: '' },
    ]
  },
  // ── AI Growth ──
  {
    key: 'growth', label: 'AI Growth', icon: 'psychology', badge: '',
    items: [
      { label: 'AI增长引擎', path: '/app/ai-growth', icon: 'auto_awesome', badge: '' },
      { label: '内容管道', path: '/app/content-pipeline', icon: 'production_quantity_limits', badge: '' },
      { label: '成长阶段', path: '/app/growth-stages', icon: 'trending_up', badge: '' },
      { label: '信用提升', path: '/app/credit-improvement', icon: 'rocket_launch', badge: '' },
      { label: '能力评估', path: '/app/capability', icon: 'assessment', badge: '' },
    ]
  },
  // ── Business ──
  {
    key: 'business', label: 'Business', icon: 'business', badge: '',
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
  // ── Tools ──
  {
    key: 'tools', label: 'Tools', icon: 'build', badge: '',
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
  // ── System ──
  {
    key: 'system', label: 'System', icon: 'settings', badge: '',
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

function toggleGroup(key: string): void {
  const idx = expandedGroups.value.indexOf(key)
  if (idx >= 0) {
    expandedGroups.value.splice(idx, 1)
  } else {
    expandedGroups.value.push(key)
  }
}

function closeMobile(): void {
  if (isMobile.value) sidebarOpen.value = false
}

function handleSearch(): void {
  if (!searchQuery.value.trim()) return
  const q = searchQuery.value.toLowerCase()
  for (const group of navGroups) {
    for (const item of group.items) {
      if (item.label.toLowerCase().includes(q)) {
        router.push(item.path)
        searchQuery.value = ''
        return
      }
    }
  }
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

  // Keyboard shortcut
  const handler = (e: KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault()
      const input = document.querySelector('.m-sidebar__search-input') as HTMLInputElement
      input?.focus()
    }
  }
  document.addEventListener('keydown', handler)
})

onUnmounted(() => {
  document.removeEventListener('resize', () => {})
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

.m-layout--mobile .m-sidebar {
  transform: translateX(0);
}

.m-layout__overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 99;
}

/* ═══════════════════════════════════════════════════════════
   SIDEBAR
   ═══════════════════════════════════════════════════════════ */
.m-sidebar {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: var(--m-sidebar-width, 256px);
  background: var(--m-surface, #FFFFFF);
  border-right: 1px solid var(--m-border, rgba(46, 38, 61, 0.12));
  display: flex;
  flex-direction: column;
  z-index: 100;
  transition: width var(--m-transition, 250ms) cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.m-sidebar--collapsed { width: var(--m-sidebar-collapsed, 80px); }

/* ── Header ── */
.m-sidebar__header {
  display: flex;
  align-items: center;
  padding: 0 var(--m-space-4, 1rem);
  height: var(--m-topbar-height, 64px);
  border-bottom: 1px solid var(--m-border, rgba(46, 38, 61, 0.12));
  gap: 0.5rem;
  flex-shrink: 0;
}

.m-sidebar__brand {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  color: var(--m-on-surface, #2E263D);
  flex: 1;
  min-width: 0;
}

.m-sidebar__logo {
  flex-shrink: 0;
  color: rgb(var(--m-primary-rgb, 85, 133, 255));
}

.m-sidebar__title {
  font-size: 1.125rem;
  font-weight: var(--m-font-weight-bold, 700);
  white-space: nowrap;
  background: linear-gradient(135deg, #5585FF, #2A52B0);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.m-sidebar__collapse-btn,
.m-sidebar__expand-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: var(--m-grey-500, #9E9E9E);
  border-radius: var(--m-radius-sm, 6px);
  cursor: pointer;
  flex-shrink: 0;
  transition: all var(--m-transition-fast, 150ms);
}

.m-sidebar__collapse-btn:hover,
.m-sidebar__expand-btn:hover {
  background: var(--m-bg-subtle, #F4F5FA);
  color: rgb(var(--m-primary-rgb, 85, 133, 255));
}

/* ── Search ── */
.m-sidebar__search {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: var(--m-space-3, 0.75rem) var(--m-space-4, 1rem);
  border-bottom: 1px solid var(--m-border, rgba(46, 38, 61, 0.12));
}

.m-sidebar__search-icon {
  color: var(--m-grey-400, #BDBDBD);
  font-size: 18px;
  flex-shrink: 0;
}

.m-sidebar__search-input {
  flex: 1;
  border: none;
  outline: none;
  font-size: var(--m-font-size-sm, 0.8125rem);
  font-family: var(--m-font-family, 'Inter', sans-serif);
  color: var(--m-on-surface, #2E263D);
  background: transparent;
}

.m-sidebar__search-input::placeholder { color: var(--m-grey-400, #BDBDBD); }

.m-sidebar__search-kbd {
  padding: 0.125rem 0.375rem;
  background: var(--m-bg-subtle, #F4F5FA);
  border: 1px solid var(--m-border, rgba(46, 38, 61, 0.12));
  border-radius: 4px;
  font-size: 0.6875rem;
  font-family: monospace;
  color: var(--m-grey-400, #BDBDBD);
  flex-shrink: 0;
}

/* ── Nav ── */
.m-sidebar__nav {
  flex: 1;
  overflow-y: auto;
  padding: var(--m-space-2, 0.5rem) 0;
}

/* ── Group ── */
.m-sidebar__group { margin-bottom: 2px; }

.m-sidebar__group-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.5rem var(--m-space-4, 1rem);
  border: none;
  background: transparent;
  color: var(--m-grey-500, #9E9E9E);
  font-size: 0.75rem;
  font-weight: var(--m-font-weight-semibold, 600);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  cursor: pointer;
  text-align: left;
  transition: color var(--m-transition-fast, 150ms);
}

.m-sidebar__group-header:hover { color: var(--m-on-surface, #2E263D); }

.m-sidebar__group-icon { font-size: 18px; flex-shrink: 0; }
.m-sidebar__group-label { flex: 1; min-width: 0; }

.m-sidebar__group-badge {
  background: rgb(var(--m-error, 255, 76, 81));
  color: white;
  font-size: 0.625rem;
  font-weight: 600;
  padding: 0.1rem 0.35rem;
  border-radius: 100px;
  flex-shrink: 0;
}

.m-sidebar__group-arrow { font-size: 18px; flex-shrink: 0; }

/* ── Items ── */
.m-sidebar__group-items {
  list-style: none;
  margin: 0;
  padding: var(--m-space-1, 0.25rem) 0;
}

.m-sidebar__item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem var(--m-space-4, 1rem);
  font-size: var(--m-font-size-base, 0.9375rem);
  color: var(--m-grey-700, #616161);
  text-decoration: none;
  transition: all var(--m-transition-fast, 150ms);
  position: relative;
  cursor: pointer;
}

.m-sidebar__item:hover {
  background: var(--m-sidebar-hover-bg, #F4F5FA);
  color: var(--m-on-surface, #2E263D);
}

.m-sidebar__item--active {
  background: rgba(var(--m-primary-rgb, 85, 133, 255), 0.12);
  color: rgb(var(--m-primary-rgb, 85, 133, 255));
  font-weight: var(--m-font-weight-medium, 500);
}

.m-sidebar__item--active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 60%;
  background: rgb(var(--m-primary-rgb, 85, 133, 255));
  border-radius: 0 2px 2px 0;
}

.m-sidebar__item-icon {
  font-size: 18px;
  flex-shrink: 0;
  width: 20px;
  text-align: center;
}

.m-sidebar__item-label { flex: 1; min-width: 0; white-space: nowrap; }

.m-sidebar__badge {
  background: rgb(var(--m-primary-rgb, 85, 133, 255));
  color: white;
  font-size: 0.6875rem;
  font-weight: 600;
  padding: 0.125rem 0.375rem;
  border-radius: 100px;
  flex-shrink: 0;
}

/* ── Footer ── */
.m-sidebar__footer {
  padding: var(--m-space-4, 1rem);
  border-top: 1px solid var(--m-border, rgba(46, 38, 61, 0.12));
  flex-shrink: 0;
}

.m-sidebar__user { display: flex; align-items: center; gap: 0.75rem; }

.m-sidebar__avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--m-font-size-sm, 0.8125rem);
  font-weight: 600;
  color: white;
  flex-shrink: 0;
}

.m-sidebar__user-info { min-width: 0; flex: 1; }

.m-sidebar__user-name {
  font-size: var(--m-font-size-sm, 0.8125rem);
  font-weight: var(--m-font-weight-semibold, 600);
  color: var(--m-on-surface, #2E263D);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.m-sidebar__user-role {
  font-size: var(--m-font-size-xs, 0.6875rem);
  color: var(--m-grey-500, #9E9E9E);
}

.m-sidebar__logout-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: var(--m-grey-400, #BDBDBD);
  border-radius: var(--m-radius-sm, 6px);
  cursor: pointer;
  flex-shrink: 0;
  transition: all var(--m-transition-fast, 150ms);
}

.m-sidebar__logout-btn:hover {
  background: rgba(var(--m-error, 255, 76, 81), 0.08);
  color: rgb(var(--m-error, 255, 76, 81));
}

/* ═══════════════════════════════════════════════════════════
   MAIN
   ═══════════════════════════════════════════════════════════ */
.m-main {
  flex: 1;
  margin-inline-start: var(--m-sidebar-width, 256px);
  display: flex;
  flex-direction: column;
  min-height: 100dvh;
  transition: margin-inline-start var(--m-transition, 250ms);
}

.m-layout--collapsed .m-main {
  margin-inline-start: var(--m-sidebar-collapsed, 80px);
}

/* ══ TOPBAR ══ */
.m-topbar {
  position: sticky;
  top: 0;
  z-index: var(--m-z-sticky, 200);
  height: var(--m-topbar-height, 64px);
  background: var(--m-surface, #FFFFFF);
  border-bottom: 1px solid var(--m-border, rgba(46, 38, 61, 0.12));
  box-shadow: var(--m-shadow-xs, 0 0.125rem 0.25rem rgba(46, 38, 61, 0.16));
}

.m-topbar__inner {
  display: flex;
  align-items: center;
  gap: var(--m-space-4, 1rem);
  padding: 0 var(--m-space-6, 1.5rem);
  height: 100%;
}

.m-topbar__menu-btn {
  display: none;
  width: 36px;
  height: 36px;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: var(--m-grey-600, #757575);
  border-radius: var(--m-radius-sm, 6px);
  cursor: pointer;
}

/* ── Breadcrumb ── */
.m-topbar__breadcrumb {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: var(--m-font-size-sm, 0.8125rem);
  color: var(--m-grey-500, #9E9E9E);
}

.m-topbar__breadcrumb-item {
  color: var(--m-grey-500, #9E9E9E);
  text-decoration: none;
  transition: color var(--m-transition-fast, 150ms);
}

.m-topbar__breadcrumb-item:hover { color: rgb(var(--m-primary-rgb, 85, 133, 255)); }
.m-topbar__breadcrumb-sep { font-size: 16px; color: var(--m-grey-400, #BDBDBD); }
.m-topbar__breadcrumb-current {
  color: var(--m-on-surface, #2E263D);
  font-weight: var(--m-font-weight-medium, 500);
}

/* ── Actions ── */
.m-topbar__actions {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  margin-inline-start: auto;
}

.m-topbar__icon-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: var(--m-grey-600, #757575);
  border-radius: var(--m-radius-sm, 6px);
  cursor: pointer;
  position: relative;
  transition: all var(--m-transition-fast, 150ms);
  text-decoration: none;
}

.m-topbar__icon-btn:hover { background: var(--m-bg-subtle, #F4F5FA); color: rgb(var(--m-primary-rgb, 85, 133, 255)); }

.m-topbar__notif-dot {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 8px;
  height: 8px;
  background: rgb(var(--m-error, 255, 76, 81));
  border-radius: 50%;
  border: 2px solid var(--m-surface, #FFFFFF);
}

/* ── User Menu ── */
.m-topbar__user-menu { position: relative; }
.m-topbar__user-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  border-radius: 50%;
  cursor: pointer;
  padding: 0;
  overflow: hidden;
}
.m-topbar__user-btn:hover { opacity: 0.8; }

.m-topbar__avatar {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--m-font-size-sm, 0.8125rem);
  font-weight: 600;
  color: white;
}

.m-topbar__dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 200px;
  background: var(--m-surface, #FFFFFF);
  border: 1px solid var(--m-border, rgba(46, 38, 61, 0.12));
  border-radius: var(--m-radius-lg, 12px);
  box-shadow: var(--m-shadow-md, 0 0.5rem 1rem rgba(46, 38, 61, 0.20));
  padding: var(--m-space-2, 0.5rem);
  z-index: var(--m-z-dropdown, 100);
}

.m-topbar__dropdown-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  padding: 0.5rem 0.75rem;
  font-size: var(--m-font-size-sm, 0.8125rem);
  color: var(--m-on-surface, #2E263D);
  border: none;
  background: transparent;
  text-align: left;
  cursor: pointer;
  border-radius: var(--m-radius-sm, 6px);
  transition: background var(--m-transition-fast, 150ms);
  text-decoration: none;
}

.m-topbar__dropdown-item:hover { background: var(--m-bg-subtle, #F4F5FA); }
.m-topbar__dropdown-item--danger { color: rgb(var(--m-error, 255, 76, 81)); }
.m-topbar__dropdown-item--danger:hover { background: rgba(var(--m-error, 255, 76, 81), 0.08); }

.m-topbar__dropdown-divider {
  height: 1px;
  background: var(--m-border, rgba(46, 38, 61, 0.12));
  margin: var(--m-space-2, 0.5rem) 0;
}

/* ══ CONTENT ══ */
.m-main__content {
  flex: 1;
  padding: var(--m-space-6, 1.5rem);
  overflow-y: auto;
}

/* ═══════════════════════════════════════════════════════════
   TRANSITIONS
   ═══════════════════════════════════════════════════════════ */
.m-fade-enter-active,
.m-fade-leave-active { transition: opacity var(--m-transition-fast, 150ms); }
.m-fade-enter-from,
.m-fade-leave-to { opacity: 0; }

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
/* ═══════════════════════════════════════════════════════════
   GLOBAL MATERIO UTILITIES
   注入到所有视图页面
   ═══════════════════════════════════════════════════════════ */

/* ── Materio Card Base ── */
.m-card {
  background: var(--m-surface, #FFFFFF);
  border-radius: var(--m-radius-lg, 12px);
  border: 1px solid var(--m-border, rgba(46, 38, 61, 0.12));
  box-shadow: var(--m-shadow-xs, 0 0.125rem 0.25rem rgba(46, 38, 61, 0.16));
  overflow: hidden;
}

.m-card__header {
  padding: var(--m-space-4, 1rem) var(--m-space-6, 1.5rem);
  border-bottom: 1px solid var(--m-border, rgba(46, 38, 61, 0.12));
  display: flex;
  align-items: center;
  gap: var(--m-space-3, 0.75rem);
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
  border: 1px solid var(--m-border, rgba(46, 38, 61, 0.12));
  box-shadow: var(--m-shadow-xs, 0 0.125rem 0.25rem rgba(46, 38, 61, 0.16));
  padding: var(--m-space-6, 1.5rem);
  display: flex;
  flex-direction: column;
  gap: var(--m-space-2, 0.5rem);
}

.m-stat-card__label {
  font-size: var(--m-font-size-sm, 0.8125rem);
  color: var(--m-grey-500, #9E9E9E);
  font-weight: var(--m-font-weight-medium, 500);
}

.m-stat-card__value {
  font-size: var(--m-font-size-xl, 1.5rem);
  font-weight: var(--m-font-weight-bold, 700);
  color: var(--m-on-surface, #2E263D);
  line-height: 1.2;
}

.m-stat-card__change { font-size: var(--m-font-size-xs, 0.6875rem); font-weight: 500; }
.m-stat-card__change--up { color: rgb(var(--m-success, 86, 202, 0)); }
.m-stat-card__change--down { color: rgb(var(--m-error, 255, 76, 81)); }

/* ── Page Header ── */
.m-page-header { margin-bottom: var(--m-space-6, 1.5rem); }
.m-page-header__title {
  font-size: 1.5rem;
  font-weight: var(--m-font-weight-bold, 700);
  color: var(--m-on-surface, #2E263D);
  margin: 0 0 var(--m-space-2, 0.5rem);
}
.m-page-header__desc {
  font-size: var(--m-font-size-sm, 0.8125rem);
  color: var(--m-grey-500, #9E9E9E);
  margin: 0;
}

/* ── Section Title ── */
.m-section-title {
  font-size: var(--m-font-size-md, 1.0625rem);
  font-weight: var(--m-font-weight-semibold, 600);
  color: var(--m-on-surface, #2E263D);
  margin: 0 0 var(--m-space-4, 1rem);
  padding-bottom: var(--m-space-2, 0.5rem);
  border-bottom: 2px solid rgb(var(--m-primary-rgb, 85, 133, 255));
  display: inline-block;
}

/* ── Chip ── */
.m-chip {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.625rem;
  border-radius: 100px;
  font-size: 0.6875rem;
  font-weight: 500;
  gap: 0.25rem;
}
.m-chip--primary { background: rgba(var(--m-primary-rgb, 85, 133, 255), 0.12); color: rgb(var(--m-primary-rgb, 85, 133, 255)); }
.m-chip--success { background: rgba(var(--m-success-rgb, 86, 202, 0), 0.12); color: rgb(var(--m-success, 86, 202, 0)); }
.m-chip--warning { background: rgba(var(--m-warning-rgb, 255, 180, 0), 0.12); color: rgb(var(--m-warning, 255, 180, 0)); }
.m-chip--error { background: rgba(var(--m-error-rgb, 255, 76, 81), 0.12); color: rgb(var(--m-error, 255, 76, 81)); }
.m-chip--info { background: rgba(var(--m-info-rgb, 22, 177, 255), 0.12); color: rgb(var(--m-info, 22, 177, 255)); }
</style>
