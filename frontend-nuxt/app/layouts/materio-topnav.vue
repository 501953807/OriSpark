<!-- Materio TopNav Layout for OriSpark
     参照: https://demos.themeselection.com/materio-vuetify-vuejs-admin-template/demo-5/
     双层布局：系统工具栏（上）+ 水平导航栏（下）
     Material Icons 图标系统
     Materio 蓝色主题 (#5585FF)
-->
<template>
  <div class="m-topnav-layout">
    <!-- ═══════════════════════════════════════════════════════════
         LAYER 1: SYSTEM UTILITY BAR — 系统功能导航条
         高度 36px：搜索 + 多语言 + 主题切换 + 收藏 + 通知 + 用户
         ═══════════════════════════════════════════════════════════ -->
    <div class="m-utility-bar" :class="{ 'm-utility-bar--scrolled': isScrolled }">
      <div class="m-utility-bar__inner">
        <!-- Left: Logo -->
        <div class="m-utility-bar__left">
          <NuxtLink to="/" class="m-utility-bar__brand">
            <svg class="m-utility-bar__logo" width="24" height="19" viewBox="0 0 30 24" fill="none">
              <path d="M1.476 0.435L6.799 3.722C7.084 3.898 7.258 4.21 7.258 4.546V19.56C7.258 19.901 7.079 20.216 6.787 20.391L1.465 23.578C1.006 23.852 0.412 23.703 0.137 23.244C0.047 23.094 0 22.922 0 22.747V1.259C0 0.724 0.433 0.291 0.968 0.291C1.147 0.291 1.323 0.341 1.476 0.435Z" fill="currentColor"/>
              <path d="M28.525 0.432L23.203 3.707C22.916 3.883 22.742 4.196 22.742 4.532V19.56C22.742 19.901 22.921 20.216 23.213 20.391L28.535 23.578C28.994 23.852 29.588 23.703 29.863 23.244C29.952 23.094 30 22.922 30 22.747V1.256C30 0.722 29.567 0.288 29.032 0.288C28.853 0.288 28.678 0.338 28.525 0.432Z" fill="currentColor"/>
              <path d="M1.473 0.427L15 8.722V16.709L0 8.114V1.253C0 0.718 0.433 0.285 0.968 0.285C1.146 0.285 1.321 0.334 1.473 0.427Z" fill="currentColor"/>
              <path d="M28.527 0.427L15 8.722V16.709L30 8.114V1.253C30 0.718 29.567 0.285 29.032 0.285C28.854 0.285 28.679 0.334 28.527 0.427Z" fill="currentColor"/>
            </svg>
            <span class="m-utility-bar__logo-text">OriSpark</span>
          </NuxtLink>
        </div>

        <!-- Center: Spacer -->
        <div class="m-utility-bar__spacer" />

        <!-- Right: Utility Actions -->
        <div class="m-utility-bar__actions">
          <!-- Search -->
          <button class="m-util-btn" @click="showSearch = true" aria-label="搜索">
            <i class="material-icons">search</i>
          </button>

          <!-- Language Switcher -->
          <div class="m-util-dropdown" ref="langMenuRef">
            <button class="m-util-btn" @click="langMenuOpen = !langMenuOpen" aria-label="切换语言" :aria-expanded="langMenuOpen">
              <i class="material-icons">translate</i>
              <span class="m-util-lang-label">{{ currentLangLabel }}</span>
              <i class="material-icons m-util-lang-arrow">{{ langMenuOpen ? 'expand_less' : 'expand_more' }}</i>
            </button>
            <div v-if="langMenuOpen" class="m-util-dropdown-menu" @click.outside="langMenuOpen = false">
              <button v-for="lang in langOptions" :key="lang.code"
                class="m-util-dropdown-item"
                :class="{ 'm-util-dropdown-item--active': currentLang === lang.code }"
                @click="switchLanguage(lang.code)"
              >
                <i class="material-icons">{{ lang.icon }}</i>
                <span>{{ lang.label }}</span>
              </button>
            </div>
          </div>

          <!-- Theme Toggle -->
          <button class="m-util-btn" @click="toggleTheme" aria-label="切换主题">
            <i class="material-icons">{{ isDark ? 'light_mode' : 'dark_mode' }}</i>
          </button>

          <!-- Bookmark -->
          <button class="m-util-btn" :class="{ 'm-util-btn--active': isBookmarked }" @click="toggleBookmark" aria-label="收藏">
            <i class="material-icons">{{ isBookmarked ? 'star' : 'star_border' }}</i>
          </button>

          <!-- Notifications -->
          <button class="m-util-btn" aria-label="通知">
            <i class="material-icons">notifications</i>
            <span class="m-util-notif-dot"></span>
          </button>

          <!-- Auth buttons -->
          <template v-if="!auth.isLoggedIn">
            <NuxtLink to="/auth/login" class="m-util-btn m-util-btn--text">登录</NuxtLink>
            <NuxtLink to="/auth/register" class="m-util-btn m-util-btn--primary">注册</NuxtLink>
          </template>
          <template v-else>
            <!-- User Menu -->
            <div class="m-util-user-menu" ref="userMenuRef">
              <button class="m-util-avatar-btn" @click="userMenuOpen = !userMenuOpen" aria-label="用户菜单">
                <div class="m-util-avatar" :style="{ background: 'linear-gradient(135deg, #5585FF, #2A52B0)' }">
                  {{ auth.user?.username?.[0]?.toUpperCase() || auth.user?.email?.[0]?.toUpperCase() || 'U' }}
                </div>
              </button>
              <div v-if="userMenuOpen" class="m-util-user-dropdown" @click.outside="userMenuOpen = false">
                <NuxtLink to="/settings" class="m-util-dropdown-item">
                  <i class="material-icons">settings</i> 设置
                </NuxtLink>
                <div class="m-util-dropdown-divider"></div>
                <button class="m-util-dropdown-item m-util-dropdown-item--danger" @click="handleLogout">
                  <i class="material-icons">logout</i> 退出登录
                </button>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════
         LAYER 2: MAIN NAVIGATION BAR — 主导航栏
         高度 48px：Hamburger + 水平导航菜单 + 下拉
         ═══════════════════════════════════════════════════════════ -->
    <header class="m-topnav" :class="{ 'm-topnav--scrolled': isScrolled }">
      <div class="m-topnav__inner">
        <!-- Left: Hamburger -->
        <div class="m-topnav__left">
          <button class="m-topnav__hamburger" :class="{ 'm-topnav__hamburger--open': mobileMenuOpen }" @click="mobileMenuOpen = !mobileMenuOpen" aria-label="Menu">
            <span class="m-topnav__hamburger-line" />
            <span class="m-topnav__hamburger-line" />
            <span class="m-topnav__hamburger-line" />
          </button>
        </div>

        <!-- Center: Navigation with Dropdowns -->
        <nav class="m-topnav__nav" v-if="!isMobile">
          <template v-for="group in navGroups" :key="group.key">
            <!-- Item with dropdown -->
            <div v-if="group.items" class="m-topnav__nav-item" :class="{ 'm-topnav__nav-item--active': groupItemsActive(group) }">
              <button class="m-topnav__nav-link" @click="toggleDropdown(group.key)" :class="{ 'm-topnav__nav-link--open': openDropdowns.includes(group.key) }">
                <i class="material-icons m-topnav__nav-icon">{{ group.icon }}</i>
                <span class="m-topnav__nav-label">{{ group.label }}</span>
                <span v-if="group.badge" class="m-topnav__nav-badge">{{ group.badge }}</span>
                <i class="material-icons m-topnav__nav-arrow">{{ openDropdowns.includes(group.key) ? 'expand_less' : 'expand_more' }}</i>
              </button>
              <div v-if="openDropdowns.includes(group.key)" class="m-topnav__dropdown" @click.outside="closeDropdown(group.key)">
                <NuxtLink
                  v-for="sub in group.items"
                  :key="sub.path"
                  :to="sub.path"
                  class="m-topnav__dropdown-item"
                  :class="{ 'm-topnav__dropdown-item--active': isActive(sub.path) }"
                  @click="closeAllDropdowns()"
                >
                  <i class="material-icons m-topnav__dropdown-icon">{{ sub.icon }}</i>
                  <span class="m-topnav__dropdown-label">{{ sub.label }}</span>
                  <span v-if="sub.badge" class="m-topnav__dropdown-badge">{{ sub.badge }}</span>
                </NuxtLink>
              </div>
            </div>
            <!-- Simple item -->
            <NuxtLink v-else :to="group.path" class="m-topnav__nav-link" :class="{ 'm-topnav__nav-link--active': isActive(group.path) }">
              <i class="material-icons m-topnav__nav-icon">{{ group.icon }}</i>
              <span>{{ group.label }}</span>
            </NuxtLink>
          </template>
        </nav>

        <!-- Right: Empty spacer for centering -->
        <div class="m-topnav__right" />
      </div>
    </header>

    <!-- Mobile Sidebar Overlay -->
    <div v-if="mobileMenuOpen" class="m-topnav-overlay" @click="mobileMenuOpen = false" />

    <!-- Mobile Sidebar -->
    <aside class="m-mobile-sidebar" :class="{ 'm-mobile-sidebar--open': mobileMenuOpen }">
      <div class="m-mobile-sidebar__header">
        <NuxtLink to="/" class="m-mobile-sidebar__brand">
          <svg class="m-utility-bar__logo" width="24" height="19" viewBox="0 0 30 24" fill="none">
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
          <NuxtLink to="/auth/login" class="m-util-btn m-util-btn--text" @click="mobileMenuOpen = false">登录</NuxtLink>
          <NuxtLink to="/auth/register" class="m-util-btn m-util-btn--primary" @click="mobileMenuOpen = false">注册</NuxtLink>
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
  badge: string
  items?: NavGroupItem[]
}

const route = useRoute()
const auth = useAuthStore()

const isScrolled = ref(false)
const mobileMenuOpen = ref(false)
const userMenuOpen = ref(false)
const showSearch = ref(false)
const searchQuery = ref('')
const userMenuRef = ref<HTMLElement | null>(null)
const langMenuRef = ref<HTMLElement | null>(null)
const langMenuOpen = ref(false)
const isMobile = ref(false)
const isDark = ref(false)
const isBookmarked = ref(false)

// ═══════════════════════════════════════════════════════════
// LANGUAGE CONFIG
// ═══════════════════════════════════════════════════════════
const langOptions = [
  { code: 'zh', label: '简体中文', icon: 'translate' },
  { code: 'en', label: 'English', icon: 'language' },
]
const currentLang = ref('zh')
const currentLangLabel = computed(() => langOptions.find(l => l.code === currentLang.value)?.label || '简体中文')

function switchLanguage(code: string): void {
  currentLang.value = code
  langMenuOpen.value = false
  // TODO: i18n integration — 后续接入 vue-i18n
  document.documentElement.lang = code
}

// ═══════════════════════════════════════════════════════════
// BOOKMARK
// ═══════════════════════════════════════════════════════════
function toggleBookmark(): void {
  isBookmarked.value = !isBookmarked.value
}

// Desktop dropdowns
const openDropdowns = ref<string[]>([])
// Mobile expanded groups
const mobileExpanded = ref<string[]>(['dashboards', 'contracts', 'market', 'operations', 'data'])

// ═══════════════════════════════════════════════════════════
// NAV GROUPS
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
  if (langMenuRef.value && !langMenuRef.value.contains(e.target as Node)) {
    langMenuOpen.value = false
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
   LAYER 1: UTILITY BAR — 系统工具栏
   高度 36px，白色背景，细边框
   ═══════════════════════════════════════════════════════════ */
.m-utility-bar {
  position: sticky;
  top: 0;
  z-index: var(--m-z-sticky, 200);
  height: 36px;
  background: var(--m-surface, #FFFFFF);
  border-bottom: 1px solid var(--m-border, rgba(46, 38, 61, 0.08));
  transition: box-shadow var(--m-transition, 250ms);
}

.m-utility-bar--scrolled {
  box-shadow: var(--m-shadow-sm, 0 0.25rem 0.5rem rgba(46, 38, 61, 0.12));
}

.m-utility-bar__inner {
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 var(--m-space-6, 1.5rem);
  height: 100%;
  display: flex;
  align-items: center;
  gap: var(--m-space-6, 1.5rem);
}

/* ── Logo ── */
.m-utility-bar__left {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.m-utility-bar__brand {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  text-decoration: none;
  color: var(--m-on-surface, #2E263D);
}

.m-utility-bar__logo {
  flex-shrink: 0;
  color: rgb(var(--m-primary-rgb, 85, 133, 255));
}

.m-utility-bar__logo-text {
  font-size: 1rem;
  font-weight: var(--m-font-weight-bold, 700);
  background: linear-gradient(135deg, #5585FF, #2A52B0);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  white-space: nowrap;
}

.m-utility-bar__spacer { flex: 1; }

/* ── Utility Buttons ── */
.m-util-btn {
  height: 28px;
  min-width: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  padding: 0 0.5rem;
  border: none;
  background: transparent;
  color: var(--m-grey-600, #757575);
  border-radius: var(--m-radius-sm, 6px);
  cursor: pointer;
  transition: all var(--m-transition-fast, 150ms);
  font-family: inherit;
  font-size: var(--m-font-size-xs, 0.75rem);
  white-space: nowrap;
  text-decoration: none;
  position: relative;
}

.m-util-btn:hover {
  background: var(--m-bg-subtle, #F4F5FA);
  color: rgb(var(--m-primary-rgb, 85, 133, 255));
}

.m-util-btn--text { color: var(--m-grey-700, #616161); font-size: 0.8125rem; padding: 0 0.75rem; }
.m-util-btn--text:hover { background: var(--m-bg-subtle, #F4F5FA); color: rgb(var(--m-primary-rgb, 85, 133, 255)); }
.m-util-btn--primary {
  background: rgb(var(--m-primary-rgb, 85, 133, 255));
  color: white;
  font-size: 0.8125rem;
  padding: 0 0.75rem;
}
.m-util-btn--primary:hover { background: rgb(var(--m-primary-darken-1-rgb, 61, 109, 214)); }
.m-util-btn--active { color: rgb(var(--m-warning, 255, 180, 0)); }

.m-util-btn .material-icons { font-size: 18px; }

.m-util-lang-label {
  font-size: 0.75rem;
  font-weight: 500;
  max-width: 48px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.m-util-lang-arrow { font-size: 18px; }

.m-util-notif-dot {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 6px;
  height: 6px;
  background: rgb(var(--m-error, 255, 76, 81));
  border-radius: 50%;
  border: 2px solid var(--m-surface, #FFFFFF);
}

/* ── Utility Dropdowns ── */
.m-util-dropdown { position: relative; }

.m-util-dropdown-menu {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  min-width: 140px;
  background: var(--m-surface, #FFFFFF);
  border: 1px solid var(--m-border, rgba(46, 38, 61, 0.12));
  border-radius: var(--m-radius-md, 8px);
  box-shadow: var(--m-shadow-md, 0 0.5rem 1rem rgba(46, 38, 61, 0.18));
  padding: var(--m-space-1, 0.25rem);
  z-index: var(--m-z-dropdown, 100);
}

.m-util-dropdown-item {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.375rem 0.625rem;
  font-size: 0.8125rem;
  color: var(--m-on-surface, #2E263D);
  border: none;
  background: transparent;
  width: 100%;
  text-align: left;
  cursor: pointer;
  border-radius: var(--m-radius-sm, 6px);
  transition: background var(--m-transition-fast, 150ms);
  font-family: inherit;
}

.m-util-dropdown-item:hover { background: var(--m-bg-subtle, #F4F5FA); }
.m-util-dropdown-item--active { background: rgba(var(--m-primary-rgb, 85, 133, 255), 0.12); color: rgb(var(--m-primary-rgb, 85, 133, 255)); }
.m-util-dropdown-item .material-icons { font-size: 18px; flex-shrink: 0; }

.m-util-dropdown-divider {
  height: 1px;
  background: var(--m-border, rgba(46, 38, 61, 0.12));
  margin: 0.25rem 0;
}

.m-util-dropdown-item--danger { color: rgb(var(--m-error, 255, 76, 81)); }
.m-util-dropdown-item--danger:hover { background: rgba(var(--m-error, 255, 76, 81), 0.08); }

/* ── User Avatar ── */
.m-util-user-menu { position: relative; }

.m-util-avatar-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  border-radius: 50%;
  cursor: pointer;
  padding: 0;
  overflow: hidden;
  transition: opacity var(--m-transition-fast, 150ms);
}
.m-util-avatar-btn:hover { opacity: 0.8; }

.m-util-avatar {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 600;
  color: white;
}

.m-util-user-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  min-width: 160px;
  background: var(--m-surface, #FFFFFF);
  border: 1px solid var(--m-border, rgba(46, 38, 61, 0.12));
  border-radius: var(--m-radius-md, 8px);
  box-shadow: var(--m-shadow-md, 0 0.5rem 1rem rgba(46, 38, 61, 0.18));
  padding: var(--m-space-1, 0.25rem);
  z-index: var(--m-z-dropdown, 100);
}

/* ═══════════════════════════════════════════════════════════
   LAYER 2: MAIN NAVBAR — 主导航栏
   高度 48px，白色背景，顶部细边框
   ═══════════════════════════════════════════════════════════ */
.m-topnav {
  position: sticky;
  top: 36px;
  z-index: var(--m-z-sticky, 200);
  height: 48px;
  background: var(--m-surface, #FFFFFF);
  border-bottom: 1px solid var(--m-border, rgba(46, 38, 61, 0.10));
  transition: box-shadow var(--m-transition, 250ms);
}

.m-topnav--scrolled {
  box-shadow: var(--m-shadow-sm, 0 0.25rem 0.5rem rgba(46, 38, 61, 0.14));
}

.m-topnav__inner {
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 var(--m-space-6, 1.5rem);
  height: 100%;
  display: flex;
  align-items: center;
  gap: var(--m-space-6, 1.5rem);
}

/* ── Hamburger ── */
.m-topnav__left { display: flex; align-items: center; flex-shrink: 0; }

.m-topnav__hamburger {
  display: none;
  width: 32px;
  height: 32px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  border: none;
  background: transparent;
  cursor: pointer;
  padding: 0;
}

.m-topnav__hamburger-line {
  display: block;
  width: 18px;
  height: 2px;
  background: var(--m-grey-600, #757575);
  border-radius: 2px;
  transition: all var(--m-transition-fast, 150ms);
}

.m-topnav__hamburger--open .m-topnav__hamburger-line:nth-child(1) {
  transform: translateY(6px) rotate(45deg);
}
.m-topnav__hamburger--open .m-topnav__hamburger-line:nth-child(2) { opacity: 0; }
.m-topnav__hamburger--open .m-topnav__hamburger-line:nth-child(3) {
  transform: translateY(-6px) rotate(-45deg);
}

.m-topnav__right { flex: 1; }

/* ── Nav ── */
.m-topnav__nav {
  display: flex;
  align-items: stretch;
  gap: 2px;
  flex: 1;
}

.m-topnav__nav-item { position: relative; }

.m-topnav__nav-link {
  display: flex;
  align-items: center;
  gap: 0.3125rem;
  padding: 0.375rem 0.75rem;
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

.m-topnav__nav-link:hover {
  color: rgb(var(--m-primary-rgb, 85, 133, 255));
  background: rgba(var(--m-primary-rgb, 85, 133, 255), 0.08);
}

.m-topnav__nav-link--active {
  color: rgb(var(--m-primary-rgb, 85, 133, 255));
  background: rgba(var(--m-primary-rgb, 85, 133, 255), 0.12);
}

.m-topnav__nav-link--open {
  color: rgb(var(--m-primary-rgb, 85, 133, 255));
  background: rgba(var(--m-primary-rgb, 85, 133, 255), 0.12);
}

.m-topnav__nav-icon { font-size: 16px; }
.m-topnav__nav-arrow { font-size: 16px; }
.m-topnav__nav-badge {
  background: rgb(var(--m-error, 255, 76, 81));
  color: white;
  font-size: 0.6rem;
  font-weight: 600;
  padding: 0.05rem 0.3rem;
  border-radius: 100px;
  margin-inline-start: 0.125rem;
}

/* ── Dropdown ── */
.m-topnav__dropdown {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  min-width: 220px;
  background: var(--m-surface, #FFFFFF);
  border: 1px solid var(--m-border, rgba(46, 38, 61, 0.12));
  border-radius: var(--m-radius-lg, 12px);
  box-shadow: var(--m-shadow-md, 0 0.5rem 1rem rgba(46, 38, 61, 0.20));
  padding: var(--m-space-2, 0.5rem);
  z-index: var(--m-z-dropdown, 100);
}

.m-topnav__dropdown-item {
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

.m-topnav__dropdown-item:hover { background: var(--m-bg-subtle, #F4F5FA); }
.m-topnav__dropdown-item--active {
  background: rgba(var(--m-primary-rgb, 85, 133, 255), 0.12);
  color: rgb(var(--m-primary-rgb, 85, 133, 255));
}
.m-topnav__dropdown-icon { font-size: 18px; flex-shrink: 0; width: 20px; text-align: center; }
.m-topnav__dropdown-label { flex: 1; }
.m-topnav__dropdown-badge {
  background: rgb(var(--m-primary-rgb, 85, 133, 255));
  color: white;
  font-size: 0.625rem;
  font-weight: 600;
  padding: 0.1rem 0.35rem;
  border-radius: 100px;
  flex-shrink: 0;
}

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
  padding: var(--m-space-3, 0.75rem) var(--m-space-4, 1rem);
  border-bottom: 1px solid var(--m-border, rgba(46, 38, 61, 0.12));
  height: 52px;
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
  width: 32px;
  height: 32px;
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
.m-topnav-main {
  flex: 1;
  min-height: calc(100dvh - 36px - 48px);
}

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
  .m-topnav__nav { display: none; }
  .m-topnav__hamburger { display: flex; }
}

@media (min-width: 1024px) {
  .m-topnav__hamburger { display: none; }
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
