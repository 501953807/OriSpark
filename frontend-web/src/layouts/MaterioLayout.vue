<!-- Materio Sidebar Layout for OriStudio -->
<template>
  <div class="m-sidebar-layout" :class="{ 'm-sidebar-layout--collapsed': isCollapsed, 'm-sidebar-layout--mobile-open': mobileOpen }">
    <!-- Mobile Overlay -->
    <div v-if="mobileOpen" class="m-sidebar-overlay" @click="mobileOpen = false" />

    <!-- Sidebar -->
    <aside class="m-sidebar" :class="{ 'm-sidebar--collapsed': isCollapsed }">
      <!-- Sidebar Header -->
      <div class="m-sidebar__header">
        <NuxtLink to="/" class="m-sidebar__brand">
          <span class="m-sidebar__logo">🎨</span>
          <span v-show="!isCollapsed" class="m-sidebar__title">OriStudio</span>
        </NuxtLink>
        <button
          v-show="!isCollapsed"
          class="m-sidebar__collapse-btn"
          @click="isCollapsed = !isCollapsed"
          aria-label="折叠侧边栏"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>
      </div>

      <!-- Navigation -->
      <nav class="m-sidebar__nav">
        <template v-for="group in navGroups" :key="group.key">
          <!-- Group Header -->
          <div class="m-sidebar__group">
            <button
              class="m-sidebar__group-header"
              @click="toggleGroup(group.key)"
            >
              <span class="m-sidebar__group-icon">{{ group.icon }}</span>
              <span v-show="!isCollapsed" class="m-sidebar__group-label">{{ group.label }}</span>
              <svg
                v-show="!isCollapsed"
                class="m-sidebar__group-arrow"
                width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
              >
                <polyline :points="expandedGroups.includes(group.key) ? '6 9 12 15 18 9' : '9 6 15 12 9 18'" />
              </svg>
            </button>

            <!-- Group Items -->
            <ul v-show="!isCollapsed && expandedGroups.includes(group.key)" class="m-sidebar__group-items">
              <li v-for="item in group.items" :key="item.path">
                <NuxtLink
                  :to="item.path"
                  class="m-sidebar__item"
                  :class="{ 'm-sidebar__item--active': isActive(item.path) }"
                  @click="closeMobile()"
                >
                  <span class="m-sidebar__item-icon">{{ item.icon }}</span>
                  <span class="m-sidebar__item-label">{{ item.label }}</span>
                  <span v-if="item.badge" class="m-sidebar__badge">{{ item.badge }}</span>
                </NuxtLink>
              </li>
            </ul>

            <!-- Flat item (no group) -->
            <NuxtLink
              v-if="!group.items && group.path"
              :to="group.path"
              class="m-sidebar__item"
              :class="{ 'm-sidebar__item--active': isActive(group.path) }"
              @click="closeMobile()"
            >
              <span class="m-sidebar__item-icon">{{ group.icon }}</span>
              <span v-show="!isCollapsed" class="m-sidebar__item-label">{{ group.label }}</span>
            </NuxtLink>
          </div>
        </template>
      </nav>

      <!-- Sidebar Footer -->
      <div v-show="!isCollapsed" class="m-sidebar__footer">
        <div class="m-sidebar__user">
          <div class="m-sidebar__avatar" :style="{ background: 'linear-gradient(135deg, #8C57FF, #6A3FCC)' }">
            {{ auth.user?.username?.[0] || auth.user?.email?.[0] || 'U' }}
          </div>
          <div class="m-sidebar__user-info">
            <div class="m-sidebar__user-name">{{ auth.user?.username || '创作者' }}</div>
            <div class="m-sidebar__user-role">{{ auth.user?.role || 'Creator' }}</div>
          </div>
        </div>
      </div>
    </aside>

    <!-- Main Area -->
    <div class="m-main">
      <!-- Topbar -->
      <header class="m-topbar">
        <div class="m-topbar__inner">
          <button class="m-topbar__menu-btn" @click="mobileOpen = true" aria-label="打开菜单">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
              <line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </button>

          <!-- Search -->
          <div class="m-topbar__search">
            <svg class="m-topbar__search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <input class="m-topbar__search-input" placeholder="搜索..." />
            <kbd class="m-topbar__search-kbd">⌘K</kbd>
          </div>

          <!-- Right Actions -->
          <div class="m-topbar__actions">
            <!-- Theme Toggle -->
            <button class="m-topbar__icon-btn" @click="toggleTheme" aria-label="切换主题">
              <svg v-if="isDark" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
              </svg>
              <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="5" /><line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" /><line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" /><line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" /><line x1="4.22" y1="19.78" x2="5.64" y2="18.36" /><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
              </svg>
            </button>

            <!-- Notifications -->
            <button class="m-topbar__icon-btn" aria-label="通知">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.73 21a2 2 0 0 1-3.46 0" />
              </svg>
              <span class="m-topbar__notif-badge">3</span>
            </button>

            <!-- User Menu -->
            <div class="m-topbar__user-menu" ref="userMenuRef">
              <button class="m-topbar__user-btn" @click="userMenuOpen = !userMenuOpen">
                <div class="m-topbar__avatar" :style="{ background: 'linear-gradient(135deg, #8C57FF, #6A3FCC)' }">
                  {{ auth.user?.username?.[0] || auth.user?.email?.[0] || 'U' }}
                </div>
              </button>
              <div v-if="userMenuOpen" class="m-topbar__dropdown">
                <NuxtLink to="/settings" class="m-topbar__dropdown-item">设置</NuxtLink>
                <button class="m-topbar__dropdown-item m-topbar__dropdown-item--danger" @click="handleLogout">退出登录</button>
              </div>
            </div>
          </div>
        </div>
      </header>

      <!-- Content -->
      <main class="m-main__content">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/useAuthStore'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const isCollapsed = ref(false)
const mobileOpen = ref(false)
const userMenuOpen = ref(false)
const isDark = ref(false)
const userMenuRef = ref<HTMLElement | null>(null)

const expandedGroups = ref<string[]>(['dashboards', 'apps', 'pages'])

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
  items?: NavItem[]
  path?: string
}

const navGroups: NavGroup[] = [
  {
    key: 'dashboards', label: 'Dashboards', icon: '📊',
    items: [
      { label: '概览', path: '/app/dashboard', icon: '○' },
      { label: '数据看板', path: '/app/data', icon: '○' },
    ]
  },
  {
    key: 'apps', label: 'Apps', icon: '📱',
    items: [
      { label: '作品管理', path: '/app/works', icon: '○', badge: '150' },
      { label: '合约市场', path: '/app/contract-market', icon: '○' },
      { label: '版权登记', path: '/app/ipr', icon: '○' },
      { label: '存证服务', path: '/app/notary', icon: '○' },
      { label: '侵权监测', path: '/app/monitor', icon: '○', badge: '5' },
      { label: '维权中心', path: '/app/enforcement', icon: '○' },
    ]
  },
  {
    key: 'pages', label: 'Pages', icon: '📄',
    items: [
      { label: '登录', path: '/login', icon: '○' },
      { label: '注册', path: '/register', icon: '○' },
      { label: '404', path: '/error', icon: '○' },
    ]
  },
  {
    key: 'ai', label: 'AI Growth', icon: '🤖',
    items: [
      { label: 'AI 增长', path: '/app/ai-growth', icon: '○' },
      { label: '内容管道', path: '/app/content-pipeline', icon: '○' },
      { label: '成长阶段', path: '/app/growth-stages', icon: '○' },
    ]
  },
]

function isActive(path: string) {
  return route.path === path || route.path.startsWith(path + '/')
}

function toggleGroup(key: string) {
  const idx = expandedGroups.value.indexOf(key)
  idx >= 0 ? expandedGroups.value.splice(idx, 1) : expandedGroups.value.push(key)
}

function closeMobile() {
  if (window.innerWidth < 1024) mobileOpen.value = false
}

function toggleTheme() {
  isDark.value = !isDark.value
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
}

function handleLogout() {
  auth.logout()
  router.push('/login')
}

function handleClickOutside(e: MouseEvent) {
  if (userMenuRef.value && !userMenuRef.value.contains(e.target as Node)) {
    userMenuOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
/* ── Layout ── */
.m-sidebar-layout {
  display: flex;
  min-height: 100dvh;
  background: var(--m-bg-subtle);
}
.m-sidebar-layout--mobile-open .m-sidebar {
  transform: translateX(0);
}

/* ── Overlay ── */
.m-sidebar-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 99;
}

/* ── Sidebar ── */
.m-sidebar {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: var(--m-sidebar-width);
  background: var(--m-surface);
  border-right: 1px solid var(--m-border);
  display: flex;
  flex-direction: column;
  z-index: 100;
  transition: width var(--m-transition);
  overflow: hidden;
}
.m-sidebar--collapsed { width: var(--m-sidebar-collapsed); }

/* ── Sidebar Header ── */
.m-sidebar__header {
  display: flex;
  align-items: center;
  padding: 0 var(--m-space-4);
  height: var(--m-topbar-height);
  border-bottom: 1px solid var(--m-border);
  gap: 0.75rem;
  flex-shrink: 0;
}
.m-sidebar__brand {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  color: var(--m-on-surface);
  flex: 1;
  min-width: 0;
}
.m-sidebar__logo { font-size: 1.5rem; flex-shrink: 0; }
.m-sidebar__title {
  font-size: 1.125rem;
  font-weight: var(--m-font-weight-bold);
  white-space: nowrap;
  background: linear-gradient(135deg, #8C57FF, #6A3FCC);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.m-sidebar__collapse-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: var(--m-grey-500);
  border-radius: var(--m-radius-sm);
  cursor: pointer;
  flex-shrink: 0;
}
.m-sidebar__collapse-btn:hover { background: var(--m-bg-subtle); color: var(--m-primary); }

/* ── Nav ── */
.m-sidebar__nav {
  flex: 1;
  overflow-y: auto;
  padding: var(--m-space-2) 0;
}

/* ── Group ── */
.m-sidebar__group { margin-bottom: 0.25rem; }
.m-sidebar__group-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.5rem var(--m-space-4);
  border: none;
  background: transparent;
  color: var(--m-grey-500);
  font-size: 0.75rem;
  font-weight: var(--m-font-weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  cursor: pointer;
  text-align: left;
  transition: color var(--m-transition-fast);
}
.m-sidebar__group-header:hover { color: var(--m-on-surface); }
.m-sidebar__group-arrow {
  margin-inline-start: auto;
  transition: transform var(--m-transition-fast);
}

/* ── Items ── */
.m-sidebar__group-items {
  list-style: none;
  margin: 0;
  padding: 0.25rem 0;
}
.m-sidebar__item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem var(--m-space-4);
  font-size: 0.875rem;
  color: var(--m-grey-700);
  text-decoration: none;
  border-radius: 0;
  transition: all var(--m-transition-fast);
  position: relative;
  cursor: pointer;
}
.m-sidebar__item:hover {
  background: var(--m-bg-subtle);
  color: var(--m-on-surface);
}
.m-sidebar__item--active {
  background: rgba(140, 87, 255, 0.12);
  color: rgb(140, 87, 255);
  font-weight: var(--m-font-weight-medium);
}
.m-sidebar__item--active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 60%;
  background: rgb(140, 87, 255);
  border-radius: 0 2px 2px 0;
}
.m-sidebar__item-icon { flex-shrink: 0; font-size: 1rem; }
.m-sidebar__item-label { flex: 1; min-width: 0; white-space: nowrap; }
.m-sidebar__badge {
  background: rgb(140, 87, 255);
  color: white;
  font-size: 0.6875rem;
  font-weight: 600;
  padding: 0.125rem 0.375rem;
  border-radius: 100px;
  flex-shrink: 0;
}

/* ── Footer ── */
.m-sidebar__footer {
  padding: var(--m-space-4);
  border-top: 1px solid var(--m-border);
}
.m-sidebar__user {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.m-sidebar__avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.875rem;
  font-weight: 600;
  color: white;
  flex-shrink: 0;
}
.m-sidebar__user-info { min-width: 0; }
.m-sidebar__user-name {
  font-size: 0.875rem;
  font-weight: var(--m-font-weight-semibold);
  color: var(--m-on-surface);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.m-sidebar__user-role {
  font-size: 0.75rem;
  color: var(--m-grey-500);
}

/* ── Main ── */
.m-main {
  flex: 1;
  margin-inline-start: var(--m-sidebar-width);
  display: flex;
  flex-direction: column;
  min-height: 100dvh;
  transition: margin-inline-start var(--m-transition);
}
.m-sidebar--collapsed ~ .m-main,
.m-sidebar-layout--collapsed .m-main {
  margin-inline-start: var(--m-sidebar-collapsed);
}

/* ── Topbar ── */
.m-topbar {
  position: sticky;
  top: 0;
  z-index: var(--m-z-sticky);
  height: var(--m-topbar-height);
  background: var(--m-surface);
  border-bottom: 1px solid var(--m-border);
  box-shadow: var(--m-shadow-xs);
}
.m-topbar__inner {
  display: flex;
  align-items: center;
  gap: var(--m-space-4);
  padding: 0 var(--m-space-6);
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
  color: var(--m-grey-600);
  border-radius: var(--m-radius-sm);
  cursor: pointer;
}
.m-topbar__search {
  flex: 1;
  max-width: 400px;
  position: relative;
}
.m-topbar__search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--m-grey-400);
}
.m-topbar__search-input {
  width: 100%;
  height: 36px;
  padding: 0 48px 0 36px;
  border: 1px solid var(--m-border);
  border-radius: var(--m-radius-sm);
  font-size: 0.875rem;
  font-family: var(--m-font-family);
  color: var(--m-on-surface);
  background: var(--m-bg-subtle);
  outline: none;
  transition: all var(--m-transition-fast);
}
.m-topbar__search-input:focus {
  border-color: rgb(140, 87, 255);
  background: var(--m-surface);
  box-shadow: 0 0 0 3px rgba(140, 87, 255, 0.1);
}
.m-topbar__search-kbd {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  padding: 0.125rem 0.375rem;
  background: var(--m-bg-subtle);
  border: 1px solid var(--m-border);
  border-radius: 4px;
  font-size: 0.6875rem;
  font-family: monospace;
  color: var(--m-grey-400);
}
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
  color: var(--m-grey-600);
  border-radius: var(--m-radius-sm);
  cursor: pointer;
  position: relative;
  transition: all var(--m-transition-fast);
}
.m-topbar__icon-btn:hover { background: var(--m-bg-subtle); color: var(--m-primary); }
.m-topbar__notif-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 8px;
  height: 8px;
  background: var(--m-error);
  border-radius: 50%;
  border: 2px solid var(--m-surface);
}
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
.m-topbar__dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 160px;
  background: var(--m-surface);
  border: 1px solid var(--m-border);
  border-radius: var(--m-radius-lg);
  box-shadow: var(--m-shadow-md);
  padding: 0.5rem;
  z-index: var(--m-z-dropdown);
}
.m-topbar__dropdown-item {
  display: block;
  width: 100%;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  color: var(--m-on-surface);
  border: none;
  background: transparent;
  text-align: left;
  cursor: pointer;
  border-radius: var(--m-radius-sm);
  transition: background var(--m-transition-fast);
  text-decoration: none;
}
.m-topbar__dropdown-item:hover { background: var(--m-bg-subtle); }
.m-topbar__dropdown-item--danger { color: var(--m-error); }
.m-topbar__dropdown-item--danger:hover { background: rgba(255, 76, 81, 0.08); }

/* ── Content ── */
.m-main__content {
  flex: 1;
  padding: var(--m-space-6);
  overflow-y: auto;
}

/* ── Responsive ── */
@media (max-width: 1023px) {
  .m-sidebar { transform: translateX(-100%); }
  .m-main { margin-inline-start: 0 !important; }
  .m-topbar__menu-btn { display: flex; }
  .m-topbar__search { display: none; }
}
</style>
