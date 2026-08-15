<!-- Materio TopNav Layout for OriSpark
     参照: https://demos.themeselection.com/materio-vuetify-vuejs-admin-template/demo-5/
     上下布局：顶部水平导航栏（含下拉菜单）+ 下部内容区
     Material Icons 图标系统
     Materio 蓝色主题 (#5585FF)
-->
<template>
  <div class="m-topnav-layout">
    <!-- ═══════════════════════════════════════════════════════════
         TOP NAVIGATION BAR — Demo-5 风格
         ═══════════════════════════════════════════════════════════ -->
    <header class="m-topbar" :class="{ 'm-topbar--scrolled': isScrolled }">
      <div class="m-topbar__inner">
        <!-- Left: Logo + Hamburger -->
        <div class="m-topbar__left">
          <button class="m-topbar__hamburger" :class="{ 'm-topbar__hamburger--open': mobileMenuOpen }" @click="mobileMenuOpen = !mobileMenuOpen" aria-label="Menu">
            <span class="m-topbar__hamburger-line" />
            <span class="m-topbar__hamburger-line" />
            <span class="m-topbar__hamburger-line" />
          </button>
          <NuxtLink to="/" class="m-topbar__brand">
            <svg class="m-topbar__logo" width="28" height="22" viewBox="0 0 30 24" fill="none">
              <path d="M1.476 0.435L6.799 3.722C7.084 3.898 7.258 4.21 7.258 4.546V19.56C7.258 19.901 7.079 20.216 6.787 20.391L1.465 23.578C1.006 23.852 0.412 23.703 0.137 23.244C0.047 23.094 0 22.922 0 22.747V1.259C0 0.724 0.433 0.291 0.968 0.291C1.147 0.291 1.323 0.341 1.476 0.435Z" fill="currentColor"/>
              <path d="M28.525 0.432L23.203 3.707C22.916 3.883 22.742 4.196 22.742 4.532V19.56C22.742 19.901 22.921 20.216 23.213 20.391L28.535 23.578C28.994 23.852 29.588 23.703 29.863 23.244C29.952 23.094 30 22.922 30 22.747V1.256C30 0.722 29.567 0.288 29.032 0.288C28.853 0.288 28.678 0.338 28.525 0.432Z" fill="currentColor"/>
              <path d="M1.473 0.427L15 8.722V16.709L0 8.114V1.253C0 0.718 0.433 0.285 0.968 0.285C1.146 0.285 1.321 0.334 1.473 0.427Z" fill="currentColor"/>
              <path d="M28.527 0.427L15 8.722V16.709L30 8.114V1.253C30 0.718 29.567 0.285 29.032 0.285C28.854 0.285 28.679 0.334 28.527 0.427Z" fill="currentColor"/>
            </svg>
            <span class="m-topbar__logo-text">OriSpark</span>
          </NuxtLink>
        </div>

        <!-- Center: Desktop Navigation with Dropdowns -->
        <nav class="m-topbar__nav" v-if="!isMobile">
          <template v-for="group in navGroups" :key="group.key">
            <!-- Item with dropdown -->
            <div v-if="group.items" class="m-topbar__nav-item" :class="{ 'm-topbar__nav-item--active': groupItemsActive(group) }">
              <button class="m-topbar__nav-link" @click="toggleDropdown(group.key)" :class="{ 'm-topbar__nav-link--open': openDropdowns.includes(group.key) }">
                <i class="material-icons m-topbar__nav-icon">{{ group.icon }}</i>
                <span class="m-topbar__nav-label">{{ group.label }}</span>
                <span v-if="group.badge" class="m-topbar__nav-badge">{{ group.badge }}</span>
                <i class="material-icons m-topbar__nav-arrow">{{ openDropdowns.includes(group.key) ? 'expand_less' : 'expand_more' }}</i>
              </button>
              <div v-if="openDropdowns.includes(group.key)" class="m-topbar__dropdown" @click.outside="closeDropdown(group.key)">
                <NuxtLink
                  v-for="sub in group.items"
                  :key="sub.path"
                  :to="sub.path"
                  class="m-topbar__dropdown-item"
                  :class="{ 'm-topbar__dropdown-item--active': isActive(sub.path) }"
                  @click="closeAllDropdowns()"
                >
                  <i class="material-icons m-topbar__dropdown-icon">{{ sub.icon }}</i>
                  <span class="m-topbar__dropdown-label">{{ sub.label }}</span>
                  <span v-if="sub.badge" class="m-topbar__dropdown-badge">{{ sub.badge }}</span>
                </NuxtLink>
              </div>
            </div>
            <!-- Simple item -->
            <NuxtLink v-else :to="group.path" class="m-topbar__nav-link" :class="{ 'm-topbar__nav-link--active': isActive(group.path) }">
              <i class="material-icons m-topbar__nav-icon">{{ group.icon }}</i>
              <span>{{ group.label }}</span>
            </NuxtLink>
          </template>
        </nav>

        <!-- Right: Actions -->
        <div class="m-topbar__actions">
          <!-- Search -->
          <button class="m-topbar__action-btn" @click="showSearch = true" aria-label="Search">
            <i class="material-icons">search</i>
          </button>

          <!-- Theme Toggle -->
          <button class="m-topbar__action-btn" @click="toggleTheme" aria-label="切换主题">
            <i class="material-icons">{{ isDark ? 'light_mode' : 'dark_mode' }}</i>
          </button>

          <!-- Notifications -->
          <button class="m-topbar__action-btn" aria-label="通知">
            <i class="material-icons">notifications</i>
            <span class="m-topbar__notif-dot"></span>
          </button>

          <!-- Auth buttons -->
          <template v-if="!auth.isLoggedIn">
            <NuxtLink to="/auth/login" class="m-topbar__btn m-topbar__btn--ghost">登录</NuxtLink>
            <NuxtLink to="/auth/register" class="m-topbar__btn m-topbar__btn--primary">注册</NuxtLink>
          </template>
          <template v-else>
            <!-- User Menu -->
            <div class="m-topbar__user-menu" ref="userMenuRef">
              <button class="m-topbar__user-btn" @click="userMenuOpen = !userMenuOpen">
                <div class="m-topbar__avatar" :style="{ background: 'linear-gradient(135deg, #5585FF, #2A52B0)' }">
                  {{ auth.user?.name?.[0] || 'U' }}
                </div>
              </button>
              <div v-if="userMenuOpen" class="m-topbar__user-dropdown" @click.outside="userMenuOpen = false">
                <NuxtLink to="/settings" class="m-topbar__dropdown-item">
                  <i class="material-icons">settings</i> 设置
                </NuxtLink>
                <div class="m-topbar__dropdown-divider"></div>
                <button class="m-topbar__dropdown-item m-topbar__dropdown-item--danger" @click="handleLogout">
                  <i class="material-icons">logout</i> 退出登录
                </button>
              </div>
            </div>
          </template>
        </div>
      </div>
    </header>

    <!-- Mobile Sidebar Overlay -->
    <div v-if="mobileMenuOpen" class="m-topnav-overlay" @click="mobileMenuOpen = false" />

    <!-- Mobile Sidebar -->
    <aside class="m-mobile-sidebar" :class="{ 'm-mobile-sidebar--open': mobileMenuOpen }">
      <div class="m-mobile-sidebar__header">
        <NuxtLink to="/" class="m-mobile-sidebar__brand">
          <svg class="m-topbar__logo" width="28" height="22" viewBox="0 0 30 24" fill="none">
            <path d="M1.476 0.435L6.799 3.722C7.084 3.898 7.258 4.21 7.258 4.546V19.56C7.258 19.901 7.079 20.216 6.787 20.391L1.465 23.578C1.006 23.852 0.412 23.703 0.137 23.244C0.047 23.094 0 22.922 0 22.747V1.259C0 0.724 0.433 0.291 0.968 0.291C1.147 0.291 1.323 0.341 1.476 0.435Z" fill="currentColor"/>
            <path d="M28.525 0.432L23.203 3.707C22.916 3.883 22.742 4.196 22.742 4.532V19.56C22.742 19.901 22.921 20.216 23.213 20.391L28.535 23.578C28.994 23.852 29.588 23.703 29.863 23.244C29.952 23.094 30 22.922 30 22.747V1.256C30 0.722 29.567 0.288 29.032 0.288C28.853 0.288 28.678 0.338 28.525 0.432Z" fill="currentColor"/>
            <path d="M1.473 0.427L15 8.722V16.709L0 8.114V1.253C0 0.718 0.433 0.285 0.968 0.285C1.146 0.285 1.321 0.334 1.473 0.427Z" fill="currentColor"/>
            <path d="M28.527 0.427L15 8.722V16.709L30 8.114V1.253C30 0.718 29.567 0.285 29.032 0.285C28.854 0.285 28.679 0.334 28.527 0.427Z" fill="currentColor"/>
          </svg>
          <span>OriSpark</span>
        </NuxtLink>
        <button class="m-mobile-sidebar__close" @click="mobileMenuOpen = false">
          <i class="material-icons">close</i>
        </button>
      </div>
      <nav class="m-mobile-sidebar__nav">
        <template v-for="group in navGroups" :key="group.key">
          <!-- Group with items -->
          <div v-if="group.items" class="m-mobile-sidebar__group">
            <button class="m-mobile-sidebar__group-header" @click="toggleMobileGroup(group.key)">
              <i class="material-icons">{{ group.icon }}</i>
              <span>{{ group.label }}</span>
              <i class="material-icons">{{ mobileExpanded.includes(group.key) ? 'expand_less' : 'expand_more' }}</i>
            </button>
            <div v-show="mobileExpanded.includes(group.key)" class="m-mobile-sidebar__group-items">
              <NuxtLink
                v-for="sub in group.items"
                :key="sub.path"
                :to="sub.path"
                class="m-mobile-sidebar__link"
                :class="{ 'm-mobile-sidebar__link--active': isActive(sub.path) }"
                @click="mobileMenuOpen = false"
              >
                <i class="material-icons">{{ sub.icon }}</i>
                {{ sub.label }}
                <span v-if="sub.badge" class="m-mobile-sidebar__badge">{{ sub.badge }}</span>
              </NuxtLink>
            </div>
          </div>
          <!-- Simple item -->
          <NuxtLink v-else :to="group.path" class="m-mobile-sidebar__link" :class="{ 'm-mobile-sidebar__link--active': isActive(group.path) }" @click="mobileMenuOpen = false">
            <i class="material-icons">{{ group.icon }}</i>
            {{ group.label }}
          </NuxtLink>
        </template>
      </nav>
      <div class="m-mobile-sidebar__footer">
        <template v-if="!auth.isLoggedIn">
          <NuxtLink to="/auth/login" class="m-topbar__btn m-topbar__btn--ghost" @click="mobileMenuOpen = false">登录</NuxtLink>
          <NuxtLink to="/auth/register" class="m-topbar__btn m-topbar__btn--primary" @click="mobileMenuOpen = false">注册</NuxtLink>
        </template>
      </div>
    </aside>

    <!-- Search Modal -->
    <Teleport to="body">
      <div v-if="showSearch" class="m-search-modal">
        <div class="m-search-modal__backdrop" @click="showSearch = false" />
        <div class="m-search-modal__content">
          <i class="material-icons m-search-modal__icon">search</i>
          <input
            v-model="searchQuery"
            class="m-search-modal__input"
            placeholder="搜索合约、作品、数据..."
            autofocus
            @keydown.esc="showSearch = false"
          />
          <div class="m-search-modal__hint"><kbd>ESC</kbd> 关闭</div>
        </div>
      </div>
    </Teleport>

    <!-- Main Content -->
    <main class="m-topnav-main">
      <slot />
    </main>

    <!-- Footer -->
    <footer class="m-topnav-footer">
      <p>© 2026 OriSpark — AI Creator Trust Hub</p>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '~/stores/auth'

const route = useRoute()
const auth = useAuthStore()

const isScrolled = ref(false)
const mobileMenuOpen = ref(false)
const userMenuOpen = ref(false)
const showSearch = ref(false)
const searchQuery = ref('')
const userMenuRef = ref<HTMLElement | null>(null)
const isMobile = ref(window.innerWidth < 1024)
const isDark = ref(false)

// Desktop dropdowns
const openDropdowns = ref<string[]>([])
// Mobile expanded groups
const mobileExpanded = ref<string[]>(['dashboards', 'contracts', 'market', 'operations', 'data'])

// ═══════════════════════════════════════════════════════════
// NAV GROUPS — Demo-5 风格（顶部导航 + 下拉菜单）
// ═══════════════════════════════════════════════════════════
const navGroups: NavGroup[] = [
  {
    key: 'dashboards', label: '数据看板', icon: 'dashboard', badge: '',
    items: [
      { label: '概览', path: '/data', icon: 'bar_chart', badge: '' },
      { label: '合约行情', path: '/market', icon: 'trending_up', badge: '' },
      { label: '作品画廊', path: '/gallery', icon: 'image', badge: '' },
    ]
  },
  {
    key: 'contracts', label: '合约市场', icon: 'handshake', badge: '',
    items: [
      { label: '所有合约', path: '/contracts', icon: 'list', badge: '' },
      { label: '我的认购', path: '/contracts?mine=1', icon: 'assignment', badge: '12' },
      { label: '合约详情', path: '/contracts/[id]', icon: 'description', badge: '' },
    ]
  },
  {
    key: 'market', label: '行情数据', icon: 'show_chart', badge: '',
    items: [
      { label: '行情看板', path: '/market', icon: 'equalizer', badge: '' },
      { label: '供需分析', path: '/supply', icon: 'scale', badge: '' },
      { label: '机会发现', path: '/opportunities', icon: 'lightbulb', badge: '新' },
    ]
  },
  {
    key: 'operations', label: '运营合作', icon: 'business', badge: '',
    items: [
      { label: '运营面板', path: '/operations', icon: 'dashboard', badge: '' },
      { label: '包装授权', path: '/operations?type=packaging', icon: 'package', badge: '' },
      { label: '分润管理', path: '/operations?type=revenue', icon: 'money', badge: '' },
    ]
  },
  {
    key: 'data', label: '数据报表', icon: 'assessment', badge: '',
    items: [
      { label: '创作者排行', path: '/data?type=ranking', icon: 'emoji_events', badge: '' },
      { label: '品类趋势', path: '/data?type=trends', icon: 'trending_up', badge: '' },
      { label: '行业报告', path: '/data?type=reports', icon: 'article', badge: '' },
    ]
  },
]

function isActive(path: string): boolean {
  const currentPath = route.path
  if (path.includes('[')) {
    const base = path.replace(/\[.*?\]/, '[^/]+')
    return currentPath.startsWith('/' + base.split('/')[0])
  }
  return currentPath === path || currentPath.startsWith(path + '/')
}

function groupItemsActive(group: NavGroup): boolean {
  if (!group.items) return false
  return group.items.some((item) => isActive(item.path))
}

function toggleDropdown(key: string): void {
  const idx = openDropdowns.value.indexOf(key)
  if (idx >= 0) {
    openDropdowns.value.splice(idx, 1)
  } else {
    closeAllDropdowns()
    openDropdowns.value.push(key)
  }
}

function closeDropdown(key: string): void {
  const idx = openDropdowns.value.indexOf(key)
  if (idx >= 0) openDropdowns.value.splice(idx, 1)
}

function closeAllDropdowns(): void {
  openDropdowns.value = []
}

function toggleMobileGroup(key: string): void {
  const idx = mobileExpanded.value.indexOf(key)
  if (idx >= 0) {
    mobileExpanded.value.splice(idx, 1)
  } else {
    mobileExpanded.value.push(key)
  }
}

function toggleTheme(): void {
  isDark.value = !isDark.value
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
}

function handleLogout(): void {
  auth.logout()
  navigateTo('/auth/login')
}

function handleClickOutside(e: MouseEvent): void {
  if (userMenuRef.value && !userMenuRef.value.contains(e.target as Node)) {
    userMenuOpen.value = false
  }
}

onMounted(() => {
  window.addEventListener('scroll', () => { isScrolled.value = window.scrollY > 10 })
  window.addEventListener('resize', () => {
    isMobile.value = window.innerWidth < 1024
    if (!isMobile.value) mobileMenuOpen.value = false
  })
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  window.removeEventListener('scroll', () => {})
  window.removeEventListener('resize', () => {})
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
/* ═══════════════════════════════════════════════════════════
   LAYOUT
   ═══════════════════════════════════════════════════════════ */
.m-topnav-layout {
  display: flex;
  flex-direction: column;
  min-height: 100dvh;
  background: var(--m-bg-subtle, #F4F5FA);
  font-family: var(--m-font-family, 'Inter', sans-serif);
}

/* ═══════════════════════════════════════════════════════════
   TOPBAR — Demo-5 风格
   ═══════════════════════════════════════════════════════════ */
.m-topbar {
  position: sticky;
  top: 0;
  z-index: var(--m-z-sticky, 200);
  height: var(--m-topbar-height, 64px);
  background: var(--m-surface, #FFFFFF);
  border-bottom: 1px solid var(--m-border, rgba(46, 38, 61, 0.12));
  transition: box-shadow var(--m-transition, 250ms);
}

.m-topbar--scrolled {
  box-shadow: var(--m-shadow-sm, 0 0.25rem 0.5rem rgba(46, 38, 61, 0.18));
}

.m-topbar__inner {
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 var(--m-space-6, 1.5rem);
  height: 100%;
  display: flex;
  align-items: center;
  gap: var(--m-space-6, 1.5rem);
}

/* ── Left ── */
.m-topbar__left {
  display: flex;
  align-items: center;
  gap: var(--m-space-4, 1rem);
  flex-shrink: 0;
}

.m-topbar__brand {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  color: var(--m-on-surface, #2E263D);
}

.m-topbar__logo {
  flex-shrink: 0;
  color: rgb(var(--m-primary-rgb, 85, 133, 255));
}

.m-topbar__logo-text {
  font-size: 1.125rem;
  font-weight: var(--m-font-weight-bold, 700);
  background: linear-gradient(135deg, #5585FF, #2A52B0);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  white-space: nowrap;
}

/* ── Hamburger ── */
.m-topbar__hamburger {
  display: none;
  width: 36px;
  height: 36px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 5px;
  border: none;
  background: transparent;
  cursor: pointer;
  padding: 0;
}

.m-topbar__hamburger-line {
  display: block;
  width: 20px;
  height: 2px;
  background: var(--m-grey-600, #757575);
  border-radius: 2px;
  transition: all var(--m-transition-fast, 150ms);
}

.m-topbar__hamburger--open .m-topbar__hamburger-line:nth-child(1) {
  transform: translateY(7px) rotate(45deg);
}
.m-topbar__hamburger--open .m-topbar__hamburger-line:nth-child(2) { opacity: 0; }
.m-topbar__hamburger--open .m-topbar__hamburger-line:nth-child(3) {
  transform: translateY(-7px) rotate(-45deg);
}

/* ── Nav ── */
.m-topbar__nav {
  display: flex;
  align-items: stretch;
  gap: 2px;
  flex: 1;
}

.m-topbar__nav-item { position: relative; }

.m-topbar__nav-link {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 0.875rem;
  font-size: var(--m-font-size-sm, 0.8125rem);
  font-weight: var(--m-font-weight-medium, 500);
  color: var(--m-grey-600, #757575);
  border-radius: var(--m-radius-sm, 6px);
  border: none;
  background: transparent;
  cursor: pointer;
  transition: all var(--m-transition-fast, 150ms);
  white-space: nowrap;
  font-family: inherit;
  text-decoration: none;
}

.m-topbar__nav-link:hover {
  color: rgb(var(--m-primary-rgb, 85, 133, 255));
  background: rgba(var(--m-primary-rgb, 85, 133, 255), 0.08);
}

.m-topbar__nav-link--active {
  color: rgb(var(--m-primary-rgb, 85, 133, 255));
  background: rgba(var(--m-primary-rgb, 85, 133, 255), 0.12);
}

.m-topbar__nav-link--open {
  color: rgb(var(--m-primary-rgb, 85, 133, 255));
  background: rgba(var(--m-primary-rgb, 85, 133, 255), 0.12);
}

.m-topbar__nav-icon { font-size: 18px; }
.m-topbar__nav-arrow { font-size: 18px; }
.m-topbar__nav-badge {
  background: rgb(var(--m-error, 255, 76, 81));
  color: white;
  font-size: 0.625rem;
  font-weight: 600;
  padding: 0.1rem 0.35rem;
  border-radius: 100px;
  margin-inline-start: 0.25rem;
}

/* ── Dropdown ── */
.m-topbar__dropdown {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  min-width: 220px;
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
  padding: 0.5rem 0.75rem;
  font-size: var(--m-font-size-sm, 0.8125rem);
  color: var(--m-on-surface, #2E263D);
  border: none;
  background: transparent;
  width: 100%;
  text-align: left;
  cursor: pointer;
  border-radius: var(--m-radius-sm, 6px);
  transition: background var(--m-transition-fast, 150ms);
  text-decoration: none;
}

.m-topbar__dropdown-item:hover { background: var(--m-bg-subtle, #F4F5FA); }
.m-topbar__dropdown-item--active {
  background: rgba(var(--m-primary-rgb, 85, 133, 255), 0.12);
  color: rgb(var(--m-primary-rgb, 85, 133, 255));
}
.m-topbar__dropdown-icon { font-size: 18px; flex-shrink: 0; width: 20px; text-align: center; }
.m-topbar__dropdown-label { flex: 1; }
.m-topbar__dropdown-badge {
  background: rgb(var(--m-primary-rgb, 85, 133, 255));
  color: white;
  font-size: 0.625rem;
  font-weight: 600;
  padding: 0.1rem 0.35rem;
  border-radius: 100px;
  flex-shrink: 0;
}

/* ── Actions ── */
.m-topbar__actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.m-topbar__action-btn {
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
  transition: all var(--m-transition-fast, 150ms);
  position: relative;
}

.m-topbar__action-btn:hover { background: var(--m-bg-subtle, #F4F5FA); color: rgb(var(--m-primary-rgb, 85, 133, 255)); }

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

.m-topbar__btn {
  height: 36px;
  padding: 0 16px;
  border-radius: var(--m-radius-sm, 6px);
  font-size: var(--m-font-size-sm, 0.8125rem);
  font-weight: var(--m-font-weight-medium, 500);
  text-decoration: none;
  transition: all var(--m-transition-fast, 150ms);
  display: inline-flex;
  align-items: center;
}

.m-topbar__btn--ghost { color: var(--m-grey-700, #616161); }
.m-topbar__btn--ghost:hover { background: var(--m-bg-subtle, #F4F5FA); }
.m-topbar__btn--primary {
  background: rgb(var(--m-primary-rgb, 85, 133, 255));
  color: white;
}
.m-topbar__btn--primary:hover { background: rgb(var(--m-primary-darken-1-rgb, 61, 109, 214)); }

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
  font-size: 0.875rem;
  font-weight: 600;
  color: white;
}

.m-topbar__user-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 180px;
  background: var(--m-surface, #FFFFFF);
  border: 1px solid var(--m-border, rgba(46, 38, 61, 0.12));
  border-radius: var(--m-radius-lg, 12px);
  box-shadow: var(--m-shadow-md, 0 0.5rem 1rem rgba(46, 38, 61, 0.20));
  padding: var(--m-space-2, 0.5rem);
  z-index: var(--m-z-dropdown, 100);
}

.m-topbar__dropdown-divider {
  height: 1px;
  background: var(--m-border, rgba(46, 38, 61, 0.12));
  margin: var(--m-space-2, 0.5rem) 0;
}

.m-topbar__dropdown-item--danger { color: rgb(var(--m-error, 255, 76, 81)); }
.m-topbar__dropdown-item--danger:hover { background: rgba(var(--m-error, 255, 76, 81), 0.08); }

/* ═══════════════════════════════════════════════════════════
   MOBILE SIDEBAR
   ═══════════════════════════════════════════════════════════ */
.m-topnav-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: calc(var(--m-z-modal, 400) - 1);
}

.m-mobile-sidebar {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: 280px;
  background: var(--m-surface, #FFFFFF);
  z-index: var(--m-z-modal, 400);
  transform: translateX(-100%);
  transition: transform var(--m-transition, 250ms);
  display: flex;
  flex-direction: column;
  box-shadow: var(--m-shadow-xl, 0 1.5rem 3rem rgba(46, 38, 61, 0.24));
}

.m-mobile-sidebar--open { transform: translateX(0); }

.m-mobile-sidebar__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--m-space-4, 1rem);
  border-bottom: 1px solid var(--m-border, rgba(46, 38, 61, 0.12));
}

.m-mobile-sidebar__brand {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.125rem;
  font-weight: var(--m-font-weight-bold, 700);
  color: var(--m-on-surface, #2E263D);
  text-decoration: none;
}

.m-mobile-sidebar__close {
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
}

.m-mobile-sidebar__close:hover { background: var(--m-bg-subtle, #F4F5FA); }

.m-mobile-sidebar__nav {
  flex: 1;
  padding: var(--m-space-2, 0.5rem);
  overflow-y: auto;
}

.m-mobile-sidebar__group-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.625rem 0.75rem;
  border: none;
  background: transparent;
  color: var(--m-grey-600, #757575);
  font-size: var(--m-font-size-sm, 0.8125rem);
  font-weight: var(--m-font-weight-medium, 500);
  border-radius: var(--m-radius-sm, 6px);
  cursor: pointer;
  text-align: left;
  transition: all var(--m-transition-fast, 150ms);
  font-family: inherit;
}

.m-mobile-sidebar__group-header:hover { background: var(--m-bg-subtle, #F4F5FA); color: var(--m-on-surface, #2E263D); }

.m-mobile-sidebar__group-items { padding-left: 1rem; }

.m-mobile-sidebar__link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.75rem;
  font-size: var(--m-font-size-sm, 0.8125rem);
  font-weight: var(--m-font-weight-medium, 500);
  color: var(--m-grey-700, #616161);
  border-radius: var(--m-radius-sm, 6px);
  text-decoration: none;
  transition: all var(--m-transition-fast, 150ms);
}

.m-mobile-sidebar__link:hover { background: var(--m-bg-subtle, #F4F5FA); color: rgb(var(--m-primary-rgb, 85, 133, 255)); }
.m-mobile-sidebar__link--active { background: rgba(var(--m-primary-rgb, 85, 133, 255), 0.12); color: rgb(var(--m-primary-rgb, 85, 133, 255)); }
.m-mobile-sidebar__badge {
  background: rgb(var(--m-primary-rgb, 85, 133, 255));
  color: white;
  font-size: 0.625rem;
  font-weight: 600;
  padding: 0.1rem 0.35rem;
  border-radius: 100px;
  margin-inline-start: auto;
}

.m-mobile-sidebar__footer {
  padding: var(--m-space-4, 1rem);
  border-top: 1px solid var(--m-border, rgba(46, 38, 61, 0.12));
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

/* ═══════════════════════════════════════════════════════════
   MAIN CONTENT
   ═══════════════════════════════════════════════════════════ */
.m-topnav-main { flex: 1; min-height: calc(100dvh - var(--m-topbar-height, 64px)); }

/* ═══════════════════════════════════════════════════════════
   SEARCH MODAL
   ═══════════════════════════════════════════════════════════ */
.m-search-modal {
  position: fixed;
  inset: 0;
  z-index: var(--m-z-modal, 400);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 15vh;
}

.m-search-modal__backdrop {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
}

.m-search-modal__content {
  position: relative;
  width: 90%;
  max-width: 560px;
  background: var(--m-surface, #FFFFFF);
  border-radius: var(--m-radius-lg, 12px);
  box-shadow: var(--m-shadow-xl, 0 1.5rem 3rem rgba(46, 38, 61, 0.24));
  padding: 1rem 1.25rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.m-search-modal__icon { color: var(--m-grey-400, #BDBDBD); font-size: 20px; flex-shrink: 0; }

.m-search-modal__input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 1rem;
  font-family: var(--m-font-family, 'Inter', sans-serif);
  color: var(--m-on-surface, #2E263D);
  background: transparent;
}

.m-search-modal__hint {
  font-size: 0.75rem;
  color: var(--m-grey-400, #BDBDBD);
  margin-top: 0.5rem;
}

.m-search-modal__hint kbd {
  padding: 0.125rem 0.375rem;
  background: var(--m-bg-subtle, #F4F5FA);
  border: 1px solid var(--m-border, rgba(46, 38, 61, 0.12));
  border-radius: 4px;
  font-family: monospace;
}

/* ═══════════════════════════════════════════════════════════
   FOOTER
   ═══════════════════════════════════════════════════════════ */
.m-topnav-footer {
  padding: var(--m-space-4, 1rem);
  text-align: center;
  font-size: var(--m-font-size-sm, 0.8125rem);
  color: var(--m-grey-500, #9E9E9E);
  border-top: 1px solid var(--m-border, rgba(46, 38, 61, 0.12));
}

/* ═══════════════════════════════════════════════════════════
   RESPONSIVE
   ═══════════════════════════════════════════════════════════ */
@media (max-width: 1023px) {
  .m-topbar__nav { display: none; }
  .m-topbar__hamburger { display: flex; }
}

@media (min-width: 1024px) {
  .m-topbar__hamburger { display: none; }
}
</style>

<style>
/* ═══════════════════════════════════════════════════════════
   GLOBAL MATERIO UTILITIES (Nuxt)
   ═══════════════════════════════════════════════════════════ */
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

.m-row { display: grid; gap: var(--m-space-6, 1.5rem); }
.m-row--2 { grid-template-columns: repeat(2, 1fr); }
.m-row--3 { grid-template-columns: repeat(3, 1fr); }
.m-row--4 { grid-template-columns: repeat(4, 1fr); }

.m-stat-card {
  background: var(--m-surface, #FFFFFF);
  border-radius: var(--m-radius-lg, 12px);
  border: 1px solid var(--m-border, rgba(46, 38, 61, 0.12));
  box-shadow: var(--m-shadow-xs, 0 0.125rem 0.25rem rgba(46, 38, 61, 0.16));
  padding: var(--m-space-6, 1.5rem);
}
.m-stat-card__label { font-size: var(--m-font-size-sm, 0.8125rem); color: var(--m-grey-500, #9E9E9E); font-weight: 500; }
.m-stat-card__value { font-size: var(--m-font-size-xl, 1.5rem); font-weight: 700; color: var(--m-on-surface, #2E263D); line-height: 1.2; }

.m-page-header { margin-bottom: var(--m-space-6, 1.5rem); }
.m-page-header__title { font-size: 1.5rem; font-weight: 700; color: var(--m-on-surface, #2E263D); margin: 0 0 var(--m-space-2, 0.5rem); }
.m-page-header__desc { font-size: var(--m-font-size-sm, 0.8125rem); color: var(--m-grey-500, #9E9E9E); margin: 0; }

.m-section-title {
  font-size: var(--m-font-size-md, 1.0625rem);
  font-weight: 600;
  color: var(--m-on-surface, #2E263D);
  margin: 0 0 var(--m-space-4, 1rem);
  padding-bottom: var(--m-space-2, 0.5rem);
  border-bottom: 2px solid rgb(var(--m-primary-rgb, 85, 133, 255));
  display: inline-block;
}

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
</style>
