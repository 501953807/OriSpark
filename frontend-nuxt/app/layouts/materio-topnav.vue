<!-- Materio TopNav Layout for OriSpark
     两层导航：Layer1 Navbar(64px) + Layer2 Menu Bar(~58px)
     完全参照: https://demos.themeselection.com/materio-vuetify-vuejs-admin-template/demo-5/
     只有登录后才能进入此布局（auth.global.ts 中间件控制）
-->
<template>
  <div class="m-layout">
    <!-- ═══════════════════════════════════════════════════════════
         LAYER 1: NAVBAR — 顶部工具栏 64px
         Logo(左) + 右侧工具按钮(搜索/工具/星/通知/头像)
         ═══════════════════════════════════════════════════════════ -->
    <header class="m-navbar">
      <div class="m-navbar__inner">
        <!-- Left: Logo -->
        <NuxtLink to="/" class="m-navbar__brand">
          <svg class="m-navbar__logo-icon" width="24" height="20" viewBox="0 0 30 24" fill="none">
            <path d="M1.476 0.435L6.799 3.722C7.084 3.898 7.258 4.21 7.258 4.546V19.56C7.258 19.901 7.079 20.216 6.787 20.391L1.465 23.578C1.006 23.852 0.412 23.703 0.137 23.244C0.047 23.094 0 22.922 0 22.747V1.259C0 0.724 0.433 0.291 0.968 0.291C1.147 0.291 1.323 0.341 1.476 0.435Z" fill="currentColor"/>
            <path d="M28.525 0.432L23.203 3.707C22.916 3.883 22.742 4.196 22.742 4.532V19.56C22.742 19.901 22.921 20.216 23.213 20.391L28.535 23.578C28.994 23.852 29.588 23.703 29.863 23.244C29.952 23.094 30 22.922 30 22.747V1.256C30 0.722 29.567 0.288 29.032 0.288C28.853 0.288 28.678 0.338 28.525 0.432Z" fill="currentColor"/>
            <path d="M1.473 0.427L15 8.722V16.709L0 8.114V1.253C0 0.718 0.433 0.285 0.968 0.285C1.146 0.285 1.321 0.334 1.473 0.427Z" fill="currentColor"/>
            <path d="M28.527 0.427L15 8.722V16.709L30 8.114V1.253C30 0.718 29.567 0.285 29.032 0.285C28.854 0.285 28.679 0.334 28.527 0.427Z" fill="currentColor"/>
          </svg>
          <span class="m-navbar__brand-text">OriSpark</span>
        </NuxtLink>

        <!-- Right: Tool Buttons -->
        <div class="m-navbar__right">
          <!-- Search -->
          <button class="m-nav-btn" @click="showSearch = true" aria-label="搜索">
            <i class="material-icons">search</i>
          </button>

          <!-- Tools / Config -->
          <button class="m-nav-btn" aria-label="工具">
            <i class="material-icons">tune</i>
          </button>

          <!-- Bookmark -->
          <button class="m-nav-btn" :class="{ 'm-nav-btn--active': isBookmarked }" @click="isBookmarked = !isBookmarked" aria-label="收藏">
            <i class="material-icons">{{ isBookmarked ? 'star' : 'star_border' }}</i>
          </button>

          <!-- Notifications -->
          <button class="m-nav-btn" aria-label="通知">
            <i class="material-icons">notifications</i>
            <span class="m-nav-btn__dot"></span>
          </button>

          <!-- Divider -->
          <div class="m-nav-divider"></div>

          <!-- User Avatar -->
          <div
            class="m-user-menu"
            ref="userMenuRef"
            @mouseenter="clearUserCloseTimer(); openUserMenu()"
            @mouseleave="startUserCloseTimer()"
          >
            <button class="m-avatar-btn" aria-label="用户菜单">
              <img
                v-if="auth.user?.avatar_url"
                :src="auth.user.avatar_url"
                alt="avatar"
                class="m-avatar-img"
              />
              <div v-else class="m-avatar-placeholder">
                {{ auth.user?.username?.[0]?.toUpperCase() || 'U' }}
              </div>
            </button>
            <div
              class="m-user-dropdown"
              :class="{ 'm-user-dropdown--open': userMenuOpen }"
            >
              <div class="m-user-dropdown__header">
                <div class="m-avatar-btn m-avatar-btn--sm" style="flex-shrink:0">
                  <img v-if="auth.user?.avatar_url" :src="auth.user.avatar_url" alt="avatar" class="m-avatar-img" />
                  <div v-else class="m-avatar-placeholder">{{ auth.user?.username?.[0]?.toUpperCase() || 'U' }}</div>
                </div>
                <div class="m-user-dropdown__info">
                  <div class="m-user-dropdown__name">{{ auth.displayName }}</div>
                  <div class="m-user-dropdown__email">{{ auth.user?.email }}</div>
                </div>
              </div>
              <NuxtLink to="/settings" class="m-user-dropdown__item" @click="userMenuOpen=false">
                <i class="material-icons">settings</i> 设置
              </NuxtLink>
              <button class="m-user-dropdown__item m-user-dropdown__item--danger" @click="handleLogout">
                <i class="material-icons">logout</i> 退出登录
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>

    <!-- ═══════════════════════════════════════════════════════════
         LAYER 2: MENU BAR — 水平导航菜单 ~58px
         平铺一级菜单 + 下拉子菜单，活跃项紫色药丸背景
         毛玻璃容器: rgba(255,255,255,0.85) blur(9px)
         ═══════════════════════════════════════════════════════════ -->
    <div class="m-menu-bar" :class="{ 'm-menu-bar--scrolled': isScrolled }">
      <div class="m-menu-bar__inner">
        <nav class="m-menu">
          <template v-for="group in navGroups" :key="group.key">
            <!-- Group with dropdown (hover-triggered) -->
            <div
              v-if="group.items"
              class="m-menu__item"
              :class="{ 'm-menu__item--active': groupItemsActive(group), 'm-menu__item--open': openDropdowns.includes(group.key) }"
              @mouseenter="clearCloseTimer(group.key); openDropdown(group.key)"
              @mouseleave="startCloseTimer(group.key)"
            >
              <button class="m-menu__link">
                <i class="material-icons m-menu__icon">{{ group.icon }}</i>
                <span class="m-menu__label">{{ group.label }}</span>
                <i class="material-icons m-menu__arrow">{{ openDropdowns.includes(group.key) ? 'expand_less' : 'expand_more' }}</i>
              </button>
              <div
                class="m-menu__dropdown"
                :class="{ 'm-menu__dropdown--open': openDropdowns.includes(group.key) }"
              >
                <NuxtLink
                  v-for="sub in group.items"
                  :key="sub.path"
                  :to="sub.path"
                  class="m-menu__dropdown-item"
                  :class="{ 'm-menu__dropdown-item--active': isActive(sub.path) }"
                  @click="closeAllDropdowns()"
                >
                  <i class="material-icons m-menu__dropdown-icon">{{ sub.icon }}</i>
                  <span>{{ sub.label }}</span>
                  <span v-if="sub.badge" class="m-menu__dropdown-badge">{{ sub.badge }}</span>
                </NuxtLink>
              </div>
            </div>
            <!-- Simple item -->
            <NuxtLink v-else :to="group.path" class="m-menu__item" :class="{ 'm-menu__item--active': isActive(group.path) }">
              <i class="material-icons m-menu__icon">{{ group.icon }}</i>
              <span class="m-menu__label">{{ group.label }}</span>
            </NuxtLink>
          </template>
        </nav>
      </div>
    </div>

    <!-- Mobile Overlay -->
    <div v-if="mobileMenuOpen" class="m-overlay" @click="mobileMenuOpen = false" />

    <!-- Mobile Sidebar -->
    <aside class="m-mobile-sidebar" :class="{ 'm-mobile-sidebar--open': mobileMenuOpen }">
      <div class="m-mobile-sidebar__header">
        <NuxtLink to="/" class="m-mobile-sidebar__brand">
          <svg class="m-navbar__logo-icon" width="24" height="20" viewBox="0 0 30 24" fill="none">
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
              </NuxtLink>
            </div>
          </div>
          <NuxtLink v-else :to="group.path" class="m-mobile-sidebar__link" :class="{ 'm-mobile-sidebar__link--active': isActive(group.path) }" @click="mobileMenuOpen = false">
            <i class="material-icons">{{ group.icon }}</i>
            {{ group.label }}
          </NuxtLink>
        </template>
      </nav>
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
    <div class="m-content-wrapper">
      <main class="m-content">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '~/stores/auth'

interface NavGroupItem {
  label: string
  path: string
  icon: string
  badge: string
}

interface NavGroup {
  key: string
  label: string
  icon: string
  items?: NavGroupItem[]
}

const route = useRoute()
const auth = useAuthStore()

const isScrolled = ref(false)
const mobileMenuOpen = ref(false)
const userMenuOpen = ref(false)
const showSearch = ref(false)
const searchQuery = ref('')
const isBookmarked = ref(false)
const userMenuRef = ref<HTMLElement | null>(null)
const isMobile = ref(false)

// Desktop dropdowns
const openDropdowns = ref<string[]>([])
// Mobile expanded groups
const mobileExpanded = ref<string[]>(['dashboards', 'contracts', 'market', 'operations', 'data'])

// Hover intent timers
const closeTimers = ref<Record<string, ReturnType<typeof setTimeout>>>({})
const userCloseTimer = ref<ReturnType<typeof setTimeout> | null>(null)

// ═══════════════════════════════════════════════════════════
// NAV GROUPS — 平铺一级菜单
// ═══════════════════════════════════════════════════════════
const navGroups: NavGroup[] = [
  {
    key: 'dashboards', label: '数据看板', icon: 'dashboard',
    items: [
      { label: '概览', path: '/data', icon: 'bar_chart', badge: '' },
      { label: '合约行情', path: '/market', icon: 'trending_up', badge: '' },
      { label: '作品画廊', path: '/gallery', icon: 'image', badge: '' },
    ]
  },
  {
    key: 'contracts', label: '合约市场', icon: 'handshake',
    items: [
      { label: '所有合约', path: '/contracts', icon: 'list', badge: '' },
      { label: '我的认购', path: '/contracts?mine=1', icon: 'assignment', badge: '12' },
    ]
  },
  {
    key: 'market', label: '行情数据', icon: 'show_chart',
    items: [
      { label: '行情看板', path: '/market', icon: 'equalizer', badge: '' },
      { label: '供需分析', path: '/supply', icon: 'scale', badge: '' },
      { label: '机会发现', path: '/opportunities', icon: 'lightbulb', badge: '新' },
    ]
  },
  {
    key: 'operations', label: '运营合作', icon: 'business',
    items: [
      { label: '运营面板', path: '/operations', icon: 'dashboard', badge: '' },
      { label: '包装授权', path: '/operations?type=packaging', icon: 'package', badge: '' },
      { label: '分润管理', path: '/operations?type=revenue', icon: 'money', badge: '' },
    ]
  },
  {
    key: 'data', label: '数据报表', icon: 'assessment',
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

function openDropdown(key: string): void {
  if (!openDropdowns.value.includes(key)) {
    openDropdowns.value.push(key)
  }
}

function closeAllDropdowns(): void {
  openDropdowns.value = []
  Object.values(closeTimers.value).forEach(clearTimeout)
  closeTimers.value = {}
}

function startCloseTimer(key: string): void {
  closeTimers.value[key] = setTimeout(() => {
    const idx = openDropdowns.value.indexOf(key)
    if (idx >= 0) openDropdowns.value.splice(idx, 1)
    delete closeTimers.value[key]
  }, 150)
}

function clearCloseTimer(key: string): void {
  if (closeTimers.value[key]) {
    clearTimeout(closeTimers.value[key])
    delete closeTimers.value[key]
  }
}

function openUserMenu(): void {
  userMenuOpen.value = true
}

function startUserCloseTimer(): void {
  userCloseTimer.value = setTimeout(() => {
    userMenuOpen.value = false
    userCloseTimer.value = null
  }, 150)
}

function clearUserCloseTimer(): void {
  if (userCloseTimer.value) {
    clearTimeout(userCloseTimer.value)
    userCloseTimer.value = null
  }
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

function toggleMobileGroup(key: string): void {
  const idx = mobileExpanded.value.indexOf(key)
  if (idx >= 0) {
    mobileExpanded.value.splice(idx, 1)
  } else {
    mobileExpanded.value.push(key)
  }
}

function handleLogout(): void {
  auth.logout()
  navigateTo('/auth/login')
}

onMounted(() => {
  window.addEventListener('scroll', () => { isScrolled.value = window.scrollY > 10 })
  window.addEventListener('resize', () => {
    isMobile.value = window.innerWidth < 1024
    if (!isMobile.value) mobileMenuOpen.value = false
  })
})

onUnmounted(() => {
  window.removeEventListener('scroll', () => {})
  window.removeEventListener('resize', () => {})
  Object.values(closeTimers.value).forEach(clearTimeout)
  if (userCloseTimer.value) clearTimeout(userCloseTimer.value)
})
</script>

<style scoped>
/* ═══════════════════════════════════════════════════════════
   LAYOUT
   ═══════════════════════════════════════════════════════════ */
.m-layout {
  display: flex;
  flex-direction: column;
  min-height: 100dvh;
}

/* ═══════════════════════════════════════════════════════════
   LAYER 1: NAVBAR — 64px
   白色背景，无阴影，Logo(左) + 右侧工具按钮
   ═══════════════════════════════════════════════════════════ */
.m-navbar {
  height: 64px;
  background: #FFFFFF;
  border-bottom: 1px solid var(--m-border);
  position: sticky;
  top: 0;
  z-index: 200;
  flex-shrink: 0;
}

.m-navbar__inner {
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 24px;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* ── Logo ── */
.m-navbar__brand {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: var(--m-primary);
}

.m-navbar__logo-icon {
  flex-shrink: 0;
  color: var(--m-primary);
}

.m-navbar__brand-text {
  font-size: 15px;
  font-weight: 500;
  letter-spacing: -0.01em;
  color: var(--m-primary);
}

/* ── Right Tool Buttons ── */
.m-navbar__right {
  display: flex;
  align-items: center;
  gap: 4px;
}

.m-nav-btn {
  width: 38px;
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: var(--m-on-surface);
  border-radius: 50%;
  cursor: pointer;
  transition: all 150ms ease;
  position: relative;
  font-size: 16px;
}

.m-nav-btn:hover {
  background: var(--m-primary-light);
  color: var(--m-primary);
}

.m-nav-btn--active {
  color: rgb(255, 180, 0);
}

.m-nav-btn .material-icons {
  font-size: 20px;
}

.m-nav-btn__dot {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 8px;
  height: 8px;
  background: var(--m-error);
  border-radius: 50%;
  border: 2px solid #FFFFFF;
}

.m-nav-divider {
  width: 1px;
  height: 24px;
  background: var(--m-border);
  margin: 0 4px;
}

/* ── User Avatar ── */
.m-user-menu { position: relative; }

.m-avatar-btn {
  width: 38px;
  height: 38px;
  border: none;
  background: linear-gradient(135deg, var(--m-primary), var(--m-primary-dark));
  border-radius: 50%;
  cursor: pointer;
  padding: 0;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 150ms, transform 150ms;
  box-shadow: 0 2px 8px rgba(140, 87, 255, 0.3);
}

.m-avatar-btn:hover {
  opacity: 0.85;
  transform: scale(1.05);
}

.m-avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.m-avatar-placeholder {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  color: white;
  background: linear-gradient(135deg, var(--m-primary), var(--m-primary-dark));
}

.m-avatar-btn--sm {
  width: 36px;
  height: 36px;
}

/* ── User Dropdown ── */
.m-user-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 240px;
  background: #FFFFFF;
  border: 1px solid var(--m-border);
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(46, 38, 61, 0.16);
  padding: 8px;
  z-index: 300;
  opacity: 0;
  visibility: hidden;
  transform: translateY(8px);
  transition: opacity 200ms ease, transform 200ms ease, visibility 200ms ease;
  pointer-events: none;
}

.m-user-dropdown--open {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
  pointer-events: auto;
}

.m-user-dropdown__header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 8px 12px;
  border-bottom: 1px solid var(--m-grey-100);
  margin-bottom: 4px;
}

.m-user-dropdown__info {
  flex: 1;
  min-width: 0;
}

.m-user-dropdown__name {
  font-size: 14px;
  font-weight: 600;
  color: var(--m-on-surface);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.m-user-dropdown__email {
  font-size: 12px;
  color: var(--m-grey-500);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.m-user-dropdown__item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  font-size: 14px;
  color: rgba(46, 38, 61, 0.8);
  border: none;
  background: transparent;
  width: 100%;
  text-align: left;
  cursor: pointer;
  border-radius: 8px;
  transition: all 150ms;
  font-family: inherit;
  text-decoration: none;
}

.m-user-dropdown__item:hover {
  background: rgba(140, 87, 255, 0.08);
  color: var(--m-primary);
}

.m-user-dropdown__item .material-icons { font-size: 18px; }
.m-user-dropdown__item--danger { color: var(--m-error); }
.m-user-dropdown__item--danger:hover { background: rgba(255, 76, 81, 0.08); }

/* ═══════════════════════════════════════════════════════════
   LAYER 2: MENU BAR — 水平导航菜单
   毛玻璃容器, sticky, 阴影
   ═══════════════════════════════════════════════════════════ */
.m-menu-bar {
  position: sticky;
  top: 64px;
  z-index: 199;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(9px);
  -webkit-backdrop-filter: blur(9px);
  border-bottom: 1px solid var(--m-grey-100);
  box-shadow: 0 4px 8px -4px rgba(46, 38, 61, 0.26);
  transition: box-shadow 250ms;
  flex-shrink: 0;
}

.m-menu-bar--scrolled {
  box-shadow: 0 8px 16px -4px var(--m-grey-300);
}

.m-menu-bar__inner {
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 24px;
  height: 58px;
  display: flex;
  align-items: center;
}

/* ── Horizontal Menu ── */
.m-menu {
  display: flex;
  align-items: stretch;
  gap: 2px;
  flex: 1;
  height: 100%;
}

.m-menu__item {
  position: relative;
  display: flex;
  align-items: center;
}

.m-menu__item--active > .m-menu__link {
  background: rgba(140, 87, 255, 0.16);
  border-radius: 100px;
  color: var(--m-primary);
}

.m-menu__link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  font-size: 14px;
  font-weight: 500;
  color: var(--m-on-surface);
  border-radius: 100px;
  border: none;
  background: transparent;
  cursor: pointer;
  transition: all 150ms ease;
  white-space: nowrap;
  font-family: inherit;
  text-decoration: none;
  position: relative;
}

.m-menu__link:hover {
  background: rgba(140, 87, 255, 0.08);
  color: var(--m-primary);
}

.m-menu__link--open {
  background: rgba(140, 87, 255, 0.08);
  color: var(--m-primary);
}

.m-menu__icon { font-size: 16px; flex-shrink: 0; }
.m-menu__arrow { font-size: 16px; opacity: 0.6; }

/* ── Dropdown ── */
.m-menu__dropdown {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  min-width: 200px;
  background: #FFFFFF;
  border: 1px solid var(--m-border);
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(46, 38, 61, 0.16);
  padding: 6px;
  z-index: 300;
  opacity: 0;
  visibility: hidden;
  transform: translateY(8px);
  transition: opacity 200ms ease, transform 200ms ease, visibility 200ms ease;
  pointer-events: none;
}

.m-menu__dropdown--open {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
  pointer-events: auto;
}

.m-menu__dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  font-size: 14px;
  color: rgba(46, 38, 61, 0.8);
  border: none;
  background: transparent;
  width: 100%;
  text-align: left;
  cursor: pointer;
  border-radius: 8px;
  transition: all 150ms;
  text-decoration: none;
}

.m-menu__dropdown-item:hover {
  background: rgba(140, 87, 255, 0.08);
  color: var(--m-primary);
}

.m-menu__dropdown-item--active {
  background: var(--m-primary-light);
  color: var(--m-primary);
  font-weight: 500;
}

.m-menu__dropdown-icon { font-size: 18px; flex-shrink: 0; width: 20px; text-align: center; }

.m-menu__dropdown-badge {
  background: var(--m-primary);
  color: white;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 100px;
  margin-inline-start: auto;
}

/* ═══════════════════════════════════════════════════════════
   MOBILE SIDEBAR
   ═══════════════════════════════════════════════════════════ */
.m-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 400;
}

.m-mobile-sidebar {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: 280px;
  background: #FFFFFF;
  z-index: 500;
  transform: translateX(-100%);
  transition: transform 250ms ease;
  display: flex;
  flex-direction: column;
  box-shadow: 0 16px 48px rgba(46, 38, 61, 0.24);
}

.m-mobile-sidebar--open { transform: translateX(0); }

.m-mobile-sidebar__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--m-border);
  height: 56px;
}

.m-mobile-sidebar__brand {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--m-primary);
  text-decoration: none;
}

.m-mobile-sidebar__close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: rgba(46, 38, 61, 0.6);
  border-radius: 50%;
  cursor: pointer;
}

.m-mobile-sidebar__close:hover { background: rgba(140, 87, 255, 0.08); }

.m-mobile-sidebar__nav {
  flex: 1;
  padding: 8px;
  overflow-y: auto;
}

.m-mobile-sidebar__group-header {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 12px;
  border: none;
  background: transparent;
  color: rgba(46, 38, 61, 0.8);
  font-size: 14px;
  font-weight: 500;
  border-radius: 8px;
  cursor: pointer;
  text-align: left;
  transition: all 150ms;
  font-family: inherit;
}

.m-mobile-sidebar__group-header:hover { background: rgba(140, 87, 255, 0.08); }
.m-mobile-sidebar__group-items { padding-left: 16px; }

.m-mobile-sidebar__link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  font-size: 14px;
  font-weight: 500;
  color: rgba(46, 38, 61, 0.8);
  border-radius: 8px;
  text-decoration: none;
  transition: all 150ms;
}

.m-mobile-sidebar__link:hover { background: rgba(140, 87, 255, 0.08); color: var(--m-primary); }
.m-mobile-sidebar__link--active { background: var(--m-primary-light); color: var(--m-primary); }

/* ═══════════════════════════════════════════════════════════
   SEARCH MODAL
   ═══════════════════════════════════════════════════════════ */
.m-search-modal {
  position: fixed;
  inset: 0;
  z-index: 600;
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
  background: #FFFFFF;
  border-radius: 12px;
  box-shadow: 0 16px 48px rgba(46, 38, 61, 0.24);
  padding: 16px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.m-search-modal__icon { color: rgba(46, 38, 61, 0.4); font-size: 20px; flex-shrink: 0; }

.m-search-modal__input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 16px;
  font-family: inherit;
  color: var(--m-on-surface);
  background: transparent;
}

.m-search-modal__hint {
  font-size: 12px;
  color: rgba(46, 38, 61, 0.4);
  margin-top: 4px;
}

.m-search-modal__hint kbd {
  padding: 2px 6px;
  background: rgba(46, 38, 61, 0.06);
  border: 1px solid var(--m-border);
  border-radius: 4px;
  font-family: monospace;
}

/* ═══════════════════════════════════════════════════════════
   MAIN CONTENT
   ═══════════════════════════════════════════════════════════ */
.m-content-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.m-content {
  flex: 1;
  padding: 24px;
  max-width: 1440px;
  width: 100%;
  margin: 0 auto;
}

/* ═══════════════════════════════════════════════════════════
   RESPONSIVE
   ═══════════════════════════════════════════════════════════ */
@media (max-width: 1023px) {
  .m-menu { display: none; }
}
</style>

<style>
/* ═══════════════════════════════════════════════════════════
   GLOBAL MATERIO DESIGN TOKENS (Nuxt)
   ═══════════════════════════════════════════════════════════ */
:root {
  /* Materio Purple Theme */
  --m-primary: rgb(140, 87, 255);
  --m-primary-light: rgba(140, 87, 255, 0.12);
  --m-primary-dark: rgb(110, 57, 220);
  --m-success: rgb(86, 202, 0);
  --m-success-light: rgba(86, 202, 0, 0.12);
  --m-warning: rgb(255, 180, 0);
  --m-warning-light: rgba(255, 180, 0, 0.12);
  --m-error: rgb(255, 76, 81);
  --m-error-light: rgba(255, 76, 81, 0.12);
  --m-info: rgb(0, 177, 255);
  --m-info-light: rgba(0, 177, 255, 0.12);

  /* Neutrals */
  --m-surface: #FFFFFF;
  --m-bg: #F4F5FA;
  --m-on-surface: rgba(46, 38, 61, 0.9);
  --m-grey-900: rgba(46, 38, 61, 0.9);
  --m-grey-700: rgba(46, 38, 61, 0.7);
  --m-grey-500: rgba(46, 38, 61, 0.5);
  --m-grey-300: rgba(46, 38, 61, 0.3);
  --m-grey-100: rgba(46, 38, 61, 0.08);
  --m-border: rgba(46, 38, 61, 0.12);

  /* Spacing */
  --m-space-1: 0.25rem;
  --m-space-2: 0.5rem;
  --m-space-3: 0.75rem;
  --m-space-4: 1rem;
  --m-space-5: 1.25rem;
  --m-space-6: 1.5rem;

  /* Radius */
  --m-radius-sm: 6px;
  --m-radius-md: 12px;
  --m-radius-lg: 16px;
  --m-radius-full: 100px;

  /* Shadows */
  --m-shadow-xs: 0 1px 3px var(--m-border);
  --m-shadow-sm: 0 2px 8px rgba(46, 38, 61, 0.16);
  --m-shadow-md: 0 4px 16px rgba(46, 38, 61, 0.2);
  --m-shadow-lg: 0 8px 32px rgba(46, 38, 61, 0.24);

  /* Transition */
  --m-transition: 250ms;
  --m-transition-fast: 150ms;
}

/* ── Global Card ── */
.m-card {
  background: var(--m-surface);
  border-radius: var(--m-radius-sm, 6px);
  border: none;
  box-shadow: var(--m-shadow-md);
  overflow: hidden;
}

.m-card__header {
  padding: var(--m-space-4, 1rem) var(--m-space-6, 1.5rem);
  border-bottom: 1px solid var(--m-border, var(--m-grey-100));
  display: flex;
  align-items: center;
  gap: var(--m-space-3, 0.75rem);
}

.m-card__title {
  font-size: 18px;
  font-weight: 500;
  color: var(--m-on-surface, var(--m-on-surface));
  margin: 0;
}

.m-card__body { padding: var(--m-space-6, 1.5rem); }

/* ── Stat Cards ── */
.m-stat-card {
  background: var(--m-surface);
  border-radius: var(--m-radius-sm, 6px);
  border: none;
  box-shadow: var(--m-shadow-md);
  padding: var(--m-space-6, 1.5rem);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.m-stat-card__label {
  font-size: 14px;
  font-weight: 500;
  color: var(--m-grey-500, var(--m-grey-500));
}

.m-stat-card__value {
  font-size: 28px;
  font-weight: 700;
  color: var(--m-on-surface, var(--m-on-surface));
  line-height: 1.1;
}

.m-stat-card__change {
  font-size: 13px;
  font-weight: 500;
}

.m-stat-card__change--up { color: var(--m-success, var(--m-success)); }
.m-stat-card__change--down { color: var(--m-error, var(--m-error)); }

.m-stat-card__tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  background: var(--m-primary-light, var(--m-primary-light));
  color: var(--m-primary, var(--m-primary));
  border-radius: var(--m-radius-full, 100px);
  font-size: 12px;
  font-weight: 500;
}

/* ── Page Header ── */
.m-page-header { margin-bottom: var(--m-space-6, 1.5rem); }
.m-page-header__title {
  font-size: 24px;
  font-weight: 700;
  color: var(--m-on-surface, var(--m-on-surface));
  margin: 0 0 var(--m-space-2, 0.5rem);
}
.m-page-header__desc {
  font-size: 14px;
  color: var(--m-grey-500, var(--m-grey-500));
  margin: 0;
}

/* ── Section Title ── */
.m-section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--m-on-surface, var(--m-on-surface));
  margin: 0 0 var(--m-space-4, 1rem);
  padding-bottom: var(--m-space-2, 0.5rem);
  border-bottom: 2px solid var(--m-primary, var(--m-primary));
  display: inline-block;
}

/* ── Chips ── */
.m-chip {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: var(--m-radius-full, 100px);
  font-size: 12px;
  font-weight: 500;
  gap: 4px;
}
.m-chip--primary { background: var(--m-primary-light); color: var(--m-primary); }
.m-chip--success { background: var(--m-success-light); color: var(--m-success); }
.m-chip--warning { background: var(--m-warning-light); color: var(--m-warning); }
.m-chip--error { background: var(--m-error-light); color: var(--m-error); }
.m-chip--info { background: var(--m-info-light); color: var(--m-info); }

/* ── Grid Layouts ── */
.m-row { display: grid; gap: var(--m-space-6, 1.5rem); }
.m-row--2 { grid-template-columns: repeat(2, 1fr); }
.m-row--3 { grid-template-columns: repeat(3, 1fr); }
.m-row--4 { grid-template-columns: repeat(4, 1fr); }

@media (max-width: 1023px) {
  .m-row--4 { grid-template-columns: repeat(2, 1fr); }
  .m-row--3 { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 639px) {
  .m-row--2, .m-row--3, .m-row--4 { grid-template-columns: 1fr; }
}

/* ── Table ── */
.m-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--m-surface);
  border-radius: var(--m-radius-sm, 6px);
  overflow: hidden;
  box-shadow: var(--m-shadow-md);
}

.m-table th {
  padding: 12px 16px;
  text-align: left;
  font-size: 13px;
  font-weight: 600;
  color: var(--m-grey-500, var(--m-grey-500));
  background: var(--m-bg, #F4F5FA);
  border-bottom: 1px solid var(--m-border);
}

.m-table td {
  padding: 12px 16px;
  font-size: 14px;
  color: var(--m-on-surface, var(--m-on-surface));
  border-bottom: 1px solid var(--m-border);
}

.m-table tr:last-child td { border-bottom: none; }
.m-table tr:hover td { background: rgba(140, 87, 255, 0.04); }

/* ── Button ── */
.m-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  border-radius: var(--m-radius-sm, 6px);
  border: none;
  cursor: pointer;
  transition: all 150ms;
  font-family: inherit;
  text-decoration: none;
}

.m-btn--primary {
  background: var(--m-primary, var(--m-primary));
  color: white;
}
.m-btn--primary:hover { background: var(--m-primary-dark, rgb(110, 57, 220)); }

.m-btn--outline {
  background: transparent;
  color: var(--m-primary, var(--m-primary));
  border: 1px solid var(--m-primary, var(--m-primary));
}
.m-btn--outline:hover { background: var(--m-primary-light, rgba(140, 87, 255, 0.08)); }

.m-btn--ghost {
  background: transparent;
  color: var(--m-grey-700, var(--m-grey-700));
}
.m-btn--ghost:hover { background: var(--m-grey-100, rgba(46, 38, 61, 0.06)); }

/* ── Mono font for numbers ── */
.m-mono { font-family: 'JetBrains Mono', 'Fira Code', monospace; }
</style>
