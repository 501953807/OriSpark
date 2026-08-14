<!-- Materio TopNav Layout for OriSpark -->
<template>
  <div class="m-topnav-layout">
    <!-- Top Navigation Bar -->
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
            <span class="m-topbar__logo">⚡</span>
            <span class="m-topbar__logo-text">OriSpark</span>
          </NuxtLink>
        </div>

        <!-- Center: Desktop Navigation -->
        <nav class="m-topbar__nav" v-if="!isMobile">
          <NuxtLink
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            class="m-topbar__nav-link"
            :class="{ 'm-topbar__nav-link--active': isActive(item.path) }"
          >
            {{ item.label }}
          </NuxtLink>
        </nav>

        <!-- Right: Actions -->
        <div class="m-topbar__actions">
          <!-- Search -->
          <button class="m-topbar__action-btn" @click="showSearch = true" aria-label="Search">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
              <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
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
                <div class="m-topbar__avatar" :style="{ background: 'linear-gradient(135deg, #8C57FF, #6A3FCC)' }">
                  {{ auth.user?.name?.[0] || 'U' }}
                </div>
                <span class="m-topbar__user-name">{{ auth.user?.name || '用户' }}</span>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline :points="userMenuOpen ? '6 9 12 15 18 9' : '9 6 15 12 9 18'" />
                </svg>
              </button>
              <div v-if="userMenuOpen" class="m-topbar__user-dropdown">
                <NuxtLink to="/settings" class="m-topbar__dropdown-item">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
                  </svg>
                  设置
                </NuxtLink>
                <button class="m-topbar__dropdown-item m-topbar__dropdown-item--danger" @click="handleLogout">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
                  </svg>
                  退出登录
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
          <span class="m-topbar__logo">⚡</span>
          <span>OriSpark</span>
        </NuxtLink>
        <button class="m-mobile-sidebar__close" @click="mobileMenuOpen = false">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
      <nav class="m-mobile-sidebar__nav">
        <NuxtLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="m-mobile-sidebar__link"
          :class="{ 'm-mobile-sidebar__link--active': isActive(item.path) }"
          @click="mobileMenuOpen = false"
        >
          {{ item.label }}
        </NuxtLink>
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
          <svg class="m-search-modal__icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input
            v-model="searchQuery"
            class="m-search-modal__input"
            placeholder="搜索页面、合约、作品..."
            autofocus
            @keydown.esc="showSearch = false"
          />
          <div class="m-search-modal__hint">
            <kbd>ESC</kbd> 关闭
          </div>
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

const navItems = [
  { label: '数据看板', path: '/data' },
  { label: '作品画廊', path: '/gallery' },
  { label: '合约市场', path: '/contracts' },
  { label: '行情数据', path: '/market' },
  { label: '运营合作', path: '/operations' },
  { label: '供应链', path: '/supply' },
]

function isActive(path: string) {
  return route.path === path || route.path.startsWith(path + '/')
}

function handleLogout() {
  auth.logout()
  navigateTo('/auth/login')
}

function handleClickOutside(e: MouseEvent) {
  if (userMenuRef.value && !userMenuRef.value.contains(e.target as Node)) {
    userMenuOpen.value = false
  }
}

onMounted(() => {
  window.addEventListener('scroll', () => { isScrolled.value = window.scrollY > 10 })
  window.addEventListener('resize', () => { isMobile.value = window.innerWidth < 1024 })
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  window.removeEventListener('scroll', () => {})
  window.removeEventListener('resize', () => {})
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
/* ── Topbar ── */
.m-topbar {
  position: sticky;
  top: 0;
  z-index: var(--m-z-sticky);
  height: var(--m-topbar-height);
  background: var(--m-surface);
  border-bottom: 1px solid var(--m-border);
  transition: box-shadow var(--m-transition);
}
.m-topbar--scrolled {
  box-shadow: var(--m-shadow-sm);
}
.m-topbar__inner {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 var(--m-space-6);
  height: 100%;
  display: flex;
  align-items: center;
  gap: var(--m-space-6);
}
.m-topbar__left {
  display: flex;
  align-items: center;
  gap: var(--m-space-4);
  flex-shrink: 0;
}
.m-topbar__brand {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  color: var(--m-on-surface);
}
.m-topbar__logo { font-size: 1.5rem; }
.m-topbar__logo-text {
  font-size: 1.125rem;
  font-weight: var(--m-font-weight-bold);
  background: linear-gradient(135deg, #8C57FF, #6A3FCC);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.m-topbar__nav {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  flex: 1;
}
.m-topbar__nav-link {
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
  font-weight: var(--m-font-weight-medium);
  color: var(--m-grey-600);
  border-radius: var(--m-radius-sm);
  transition: all var(--m-transition-fast);
}
.m-topbar__nav-link:hover {
  color: var(--m-primary);
  background: rgba(140, 87, 255, 0.08);
}
.m-topbar__nav-link--active {
  color: var(--m-primary);
  background: rgba(140, 87, 255, 0.12);
}
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
  color: var(--m-grey-600);
  border-radius: var(--m-radius-sm);
  cursor: pointer;
  transition: all var(--m-transition-fast);
}
.m-topbar__action-btn:hover {
  background: var(--m-bg-subtle);
  color: var(--m-primary);
}
.m-topbar__btn {
  height: 36px;
  padding: 0 16px;
  border-radius: var(--m-radius-sm);
  font-size: 0.875rem;
  font-weight: var(--m-font-weight-medium);
  text-decoration: none;
  transition: all var(--m-transition-fast);
}
.m-topbar__btn--ghost {
  color: var(--m-grey-700);
}
.m-topbar__btn--ghost:hover {
  background: var(--m-bg-subtle);
}
.m-topbar__btn--primary {
  background: rgb(140, 87, 255);
  color: white;
}
.m-topbar__btn--primary:hover {
  background: rgb(126, 78, 230);
}

/* ── User Menu ── */
.m-topbar__user-menu { position: relative; }
.m-topbar__user-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0.5rem;
  border: none;
  background: transparent;
  border-radius: var(--m-radius-sm);
  cursor: pointer;
  transition: background var(--m-transition-fast);
}
.m-topbar__user-btn:hover { background: var(--m-bg-subtle); }
.m-topbar__avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.875rem;
  font-weight: 600;
  color: white;
}
.m-topbar__user-name {
  font-size: 0.875rem;
  font-weight: var(--m-font-weight-medium);
  color: var(--m-on-surface);
}
.m-topbar__user-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 180px;
  background: var(--m-surface);
  border: 1px solid var(--m-border);
  border-radius: var(--m-radius-lg);
  box-shadow: var(--m-shadow-md);
  padding: 0.5rem;
  z-index: var(--m-z-dropdown);
}
.m-topbar__dropdown-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  color: var(--m-on-surface);
  border: none;
  background: transparent;
  width: 100%;
  text-align: left;
  cursor: pointer;
  border-radius: var(--m-radius-sm);
  transition: background var(--m-transition-fast);
  text-decoration: none;
}
.m-topbar__dropdown-item:hover { background: var(--m-bg-subtle); }
.m-topbar__dropdown-item--danger { color: var(--m-error); }
.m-topbar__dropdown-item--danger:hover { background: rgba(255, 76, 81, 0.08); }

/* ── Mobile Sidebar ── */
.m-mobile-sidebar {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: 280px;
  background: var(--m-surface);
  z-index: var(--m-z-modal);
  transform: translateX(-100%);
  transition: transform var(--m-transition);
  display: flex;
  flex-direction: column;
  box-shadow: var(--m-shadow-xl);
}
.m-mobile-sidebar--open { transform: translateX(0); }
.m-mobile-sidebar__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--m-space-4);
  border-bottom: 1px solid var(--m-border);
}
.m-mobile-sidebar__brand {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.125rem;
  font-weight: var(--m-font-weight-bold);
  color: var(--m-on-surface);
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
  color: var(--m-grey-600);
  border-radius: var(--m-radius-sm);
  cursor: pointer;
}
.m-mobile-sidebar__close:hover { background: var(--m-bg-subtle); }
.m-mobile-sidebar__nav {
  flex: 1;
  padding: var(--m-space-2);
  overflow-y: auto;
}
.m-mobile-sidebar__link {
  display: block;
  padding: 0.75rem 1rem;
  font-size: 0.9375rem;
  font-weight: var(--m-font-weight-medium);
  color: var(--m-grey-700);
  border-radius: var(--m-radius-sm);
  text-decoration: none;
  transition: all var(--m-transition-fast);
}
.m-mobile-sidebar__link:hover { background: var(--m-bg-subtle); color: var(--m-primary); }
.m-mobile-sidebar__link--active { background: rgba(140, 87, 255, 0.12); color: var(--m-primary); }
.m-mobile-sidebar__footer {
  padding: var(--m-space-4);
  border-top: 1px solid var(--m-border);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

/* ── Overlay ── */
.m-topnav-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: calc(var(--m-z-modal) - 1);
}

/* ── Main ── */
.m-topnav-main {
  flex: 1;
  min-height: calc(100dvh - var(--m-topbar-height));
}

/* ── Footer ── */
.m-topnav-footer {
  padding: var(--m-space-4);
  text-align: center;
  font-size: var(--m-font-size-sm);
  color: var(--m-grey-500);
  border-top: 1px solid var(--m-border);
}

/* ── Search Modal ── */
.m-search-modal {
  position: fixed;
  inset: 0;
  z-index: var(--m-z-modal);
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
  background: var(--m-surface);
  border-radius: var(--m-radius-lg);
  box-shadow: var(--m-shadow-xl);
  padding: 1rem 1.25rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.m-search-modal__icon { color: var(--m-grey-400); flex-shrink: 0; }
.m-search-modal__input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 1rem;
  font-family: var(--m-font-family);
  color: var(--m-on-surface);
  background: transparent;
}
.m-search-modal__hint {
  font-size: 0.75rem;
  color: var(--m-grey-400);
  margin-top: 0.5rem;
}
.m-search-modal__hint kbd {
  padding: 0.125rem 0.375rem;
  background: var(--m-bg-subtle);
  border: 1px solid var(--m-border);
  border-radius: 4px;
  font-family: monospace;
}

/* ── Responsive ── */
@media (max-width: 1023px) {
  .m-topbar__nav { display: none; }
}
@media (min-width: 1024px) {
  .m-topbar__hamburger { display: none; }
}
</style>
