<template>
  <header class="topbar">
    <div class="topbar-left">
      <!-- Mobile hamburger -->
      <button class="topbar-mobile-btn" @click="$emit('toggleMobile')" aria-label="打开菜单">
        <span class="material-icons">menu</span>
      </button>
      <!-- Search box -->
      <div class="topbar-search">
        <span class="material-icons topbar-search-icon">search</span>
        <input type="text" class="topbar-search-input" placeholder="搜索…" :title="shortcutHint" />
        <span v-if="!isMobile" class="topbar-search-shortcut">{{ shortcutHint }}</span>
      </div>
    </div>

    <div class="topbar-right">
      <!-- Direction toggle -->
      <button class="topbar-icon-btn" title="切换方向" aria-label="切换方向">
        <span class="material-icons">swap_horiz</span>
      </button>

      <!-- Theme switcher -->
      <div class="theme-switcher" :class="{ open: themePickerOpen }">
        <button class="topbar-icon-btn" :title="themeLabel(appStore.currentTheme)" @click="themePickerOpen = !themePickerOpen">
          <span class="material-icons">light_mode</span>
        </button>
        <Transition name="theme-dropdown">
          <div v-if="themePickerOpen" class="theme-panel" @click.stop>
            <div
              v-for="t in appStore.themePresets"
              :key="t"
              class="theme-option"
              :class="{ active: appStore.currentTheme === t }"
              @click="appStore.setTheme(t); themePickerOpen = false"
            >
              <span class="theme-swatch" :style="{ background: themeColor(t) }"></span>
              <span class="theme-name">{{ themeLabel(t) }}</span>
            </div>
          </div>
        </Transition>
      </div>

      <!-- Favorite -->
      <button class="topbar-icon-btn" title="收藏" aria-label="收藏">
        <span class="material-icons">star_border</span>
      </button>

      <!-- Notification -->
      <NotificationBell />

      <!-- Message button -->
      <router-link to="/app/messages" class="topbar-icon-btn" title="消息中心" aria-label="消息中心">
        <span class="material-icons">chat_bubble_outline</span>
      </router-link>

      <!-- User menu -->
      <div class="user-menu" ref="userMenuRef">
        <button class="user-menu-btn" @click="userMenuOpen = !userMenuOpen" aria-label="用户菜单">
          <div class="user-avatar" :style="{ background: avatarGradient }">
            <img v-if="authStore.user?.avatar_url" :src="authStore.user.avatar_url" class="user-avatar-img" />
            <span v-else>{{ (authStore.displayName || 'U').charAt(0).toUpperCase() }}</span>
          </div>
          <span v-if="!isCollapsed" class="user-name">{{ authStore.displayName }}</span>
          <span class="material-icons user-chevron">{{ userMenuOpen ? 'expand_less' : 'expand_more' }}</span>
        </button>
        <Teleport to="body">
          <div v-if="userMenuOpen" class="user-menu-overlay" @click="userMenuOpen = false"></div>
          <Transition name="fade">
            <div v-if="userMenuOpen" class="user-dropdown">
              <div class="dropdown-header">
                <div class="dropdown-avatar" :style="{ background: avatarGradient }">
                  <img v-if="authStore.user?.avatar_url" :src="authStore.user.avatar_url" class="user-avatar-img" />
                  <span v-else>{{ (authStore.displayName || 'U').charAt(0).toUpperCase() }}</span>
                </div>
                <div class="dropdown-info">
                  <div class="dropdown-name">{{ authStore.displayName }}</div>
                  <div class="dropdown-role">{{ authStore.user?.role || '创作者' }}</div>
                </div>
              </div>
              <div class="dropdown-divider"></div>
              <router-link to="/app/risk-warning" class="dropdown-item" @click="userMenuOpen = false">
                <span class="dropdown-icon material-icons">warning</span>
                风险预警
                <span v-if="alertCount > 0" class="dropdown-badge">{{ alertCount }}</span>
              </router-link>
              <router-link to="/app/messages" class="dropdown-item" @click="userMenuOpen = false">
                <span class="dropdown-icon material-icons">chat_bubble_outline</span>
                消息中心
              </router-link>
              <div class="dropdown-divider"></div>
              <router-link to="/app/settings/subscriptions" class="dropdown-item" @click="userMenuOpen = false">
                <span class="dropdown-icon material-icons">stars</span>
                订阅管理
              </router-link>
              <div class="dropdown-divider"></div>
              <router-link to="/app/settings" class="dropdown-item" @click="userMenuOpen = false">
                <span class="dropdown-icon material-icons">settings</span>
                偏好设置
              </router-link>
              <div class="dropdown-divider"></div>
              <button class="dropdown-item dropdown-logout" @click="handleLogout">
                <span class="dropdown-icon material-icons">logout</span>
                退出登录
              </button>
            </div>
          </Transition>
        </Teleport>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useLayoutContext } from '@/composables/useLayoutContext'
import { useAppStore } from '@/stores/useAppStore'
import { useAuthStore } from '@/stores/useAuthStore'
import NotificationBell from '@/components/NotificationBell.vue'

defineProps<{ isCollapsed?: boolean }>()
defineEmits(['toggleMobile'])

const appStore = useAppStore()
const authStore = useAuthStore()
const userMenuOpen = ref(false)
const userMenuRef = ref<HTMLElement | null>(null)
const themePickerOpen = ref(false)
const isMobile = ref(window.innerWidth < 768)

const shortcutHint = computed(() => {
  const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0
  return isMac ? '⌘K' : 'Ctrl+K'
})

const avatarGradient = computed(() => {
  const hue = 270
  return `linear-gradient(135deg, hsl(${hue},70%,60%), hsl(${(hue + 30) % 360},70%,45%))`
})

function themeColor(t: string): string {
  if (t === 'cold-white') return 'oklch(54% 0.16 280)'
  if (t === 'warm-gray') return 'oklch(54% 0.14 40)'
  if (t === 'midnight-gold') return '#D4AF37'
  return 'oklch(65% 0.13 280)'
}
function themeLabel(t: string): string {
  if (t === 'cold-white') return '冷白商务'
  if (t === 'warm-gray') return '暖灰温和'
  if (t === 'midnight-gold') return '午夜金'
  return '深蓝夜间'
}

const alertCount = computed(() => appStore.alertCount)

async function handleLogout() {
  await authStore.logout()
  userMenuOpen.value = false
  window.location.href = '/login'
}

function handleClickOutside(event: MouseEvent) {
  if (userMenuRef.value && !userMenuRef.value.contains(event.target as Node)) {
    userMenuOpen.value = false
  }
}

function handleThemeClickOutside(event: MouseEvent) {
  const themeEl = document.querySelector('.theme-switcher')
  if (themeEl && !themeEl.contains(event.target as Node)) {
    themePickerOpen.value = false
  }
}

function handleResize() {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  document.addEventListener('click', handleThemeClickOutside)
  window.addEventListener('resize', handleResize)
})
onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('click', handleThemeClickOutside)
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.topbar {
  height: var(--m-topbar-height, 64px);
  background: var(--m-topbar-bg, #ffffff);
  border-bottom: 1px solid var(--m-topbar-border, rgba(46, 38, 61, 0.12));
  box-shadow: var(--m-topbar-shadow, 0 1px 0 rgba(46, 38, 61, 0.08));
  display: flex;
  align-items: center;
  padding: 0 16px;
  gap: 8px;
  position: sticky;
  top: 0;
  z-index: 90;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

/* Mobile hamburger */
.topbar-mobile-btn {
  display: none;
  width: 36px;
  height: 36px;
  border: none;
  background: none;
  cursor: pointer;
  border-radius: var(--m-radius-sm);
  color: var(--m-on-surface, #2E263D);
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.topbar-mobile-btn:hover { background: var(--m-sidebar-hover-bg, #F4F5FA); }
.topbar-mobile-btn .material-icons { font-size: 1.25rem; }

/* Search box */
.topbar-search {
  position: relative;
  display: flex;
  align-items: center;
  flex: 1;
  max-width: 360px;
}
.topbar-search-icon {
  position: absolute;
  left: 10px;
  font-size: 1.1rem !important;
  color: var(--m-muted, #8A8D93);
  pointer-events: none;
  z-index: 1;
}
.topbar-search-input {
  width: 100%;
  height: 36px;
  padding: 0 72px 0 36px;
  border: 1px solid var(--m-search-border, rgba(46, 38, 61, 0.12));
  border-radius: var(--m-radius-md, 10px);
  background: var(--m-search-bg, #F4F5FA);
  font-size: 0.875rem;
  color: var(--m-on-surface, #2E263D);
  outline: none;
  transition: border-color 0.15s, background 0.15s;
}
.topbar-search-input::placeholder { color: var(--m-muted, #8A8D93); }
.topbar-search-input:focus {
  border-color: #5585FF;
  background: #fff;
}
.topbar-search-shortcut {
  position: absolute;
  right: 10px;
  font-size: 0.72rem;
  color: var(--m-muted, #8A8D93);
  background: var(--m-surface-2, #EEF0F4);
  padding: 2px 6px;
  border-radius: 4px;
  pointer-events: none;
}

/* Right side */
.topbar-right {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* Icon buttons */
.topbar-icon-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: none;
  cursor: pointer;
  border-radius: var(--m-radius-sm);
  color: var(--m-on-surface, #2E263D);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
}
.topbar-icon-btn:hover { background: var(--m-sidebar-hover-bg, #F4F5FA); }
.topbar-icon-btn .material-icons { font-size: 1.25rem; }

/* Theme switcher */
.theme-switcher { position: relative; }
.theme-panel {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  background: var(--m-surface, #fff);
  border: 1px solid var(--m-border, rgba(46,38,61,0.12));
  border-radius: var(--m-radius-md);
  box-shadow: var(--m-shadow-md, 0 0.5rem 1rem rgba(46,38,61,0.2));
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  z-index: 200;
  min-width: 160px;
}
.theme-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: var(--m-radius-sm);
  cursor: pointer;
  transition: background 0.15s;
}
.theme-option:hover { background: var(--m-sidebar-hover-bg, #F4F5FA); }
.theme-option.active { background: var(--m-accent-dim, rgba(139,92,246,0.08)); }
.theme-swatch {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  flex-shrink: 0;
  border: 2px solid rgba(0,0,0,0.1);
}
.theme-name { font-size: 0.82rem; color: var(--m-on-surface, #2E263D); }

/* NotificationBell: preserve existing positioning */
.notif-wrapper :deep(.notif-btn) {
  width: 36px;
  height: 36px;
  padding: 0;
  border-radius: var(--m-radius-sm);
}
.notif-wrapper :deep(.notif-btn:hover) {
  background: var(--m-sidebar-hover-bg, #F4F5FA);
}

/* User menu */
.user-menu { position: relative; margin-left: 4px; }
.user-menu-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border: none;
  background: none;
  cursor: pointer;
  border-radius: var(--m-radius-sm);
  transition: background 0.15s;
  font-family: inherit;
}
.user-menu-btn:hover { background: var(--m-sidebar-hover-bg, #F4F5FA); }
.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 600;
  font-size: 0.85rem;
  flex-shrink: 0;
  overflow: hidden;
  box-shadow: 0 2px 6px rgba(139,92,246,0.25);
}
.user-avatar-img { width: 100%; height: 100%; object-fit: cover; }
.user-name {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--m-on-surface, #2E263D);
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.user-chevron { font-size: 1.1rem !important; color: var(--m-muted, #8A8D93); }

/* Dropdown */
.user-menu-overlay {
  position: fixed;
  inset: 0;
  z-index: 99;
}
.user-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 240px;
  background: var(--m-surface, #fff);
  border: 1px solid var(--m-border, rgba(46,38,61,0.12));
  border-radius: var(--m-radius-md);
  box-shadow: var(--m-shadow-md, 0 0.5rem 1rem rgba(46,38,61,0.2));
  z-index: 200;
  overflow: hidden;
}
.dropdown-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 14px 12px;
}
.dropdown-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 600;
  font-size: 1rem;
  flex-shrink: 0;
  overflow: hidden;
}
.dropdown-info { flex: 1; min-width: 0; }
.dropdown-name { font-size: 0.9rem; font-weight: 600; color: var(--m-on-surface, #2E263D); }
.dropdown-role { font-size: 0.75rem; color: var(--m-muted, #8A8D93); margin-top: 2px; }
.dropdown-divider { height: 1px; background: var(--m-border, rgba(46,38,61,0.12)); margin: 4px 0; }
.dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 14px;
  font-size: 0.85rem;
  color: var(--m-on-surface, #2E263D);
  text-decoration: none;
  transition: background 0.15s;
  cursor: pointer;
  border: none;
  background: none;
  width: 100%;
  text-align: left;
  font-family: inherit;
}
.dropdown-item:hover { background: var(--m-sidebar-hover-bg, #F4F5FA); }
.dropdown-icon { font-size: 1.15rem !important; color: var(--m-muted, #8A8D93); }
.dropdown-badge {
  margin-left: auto;
  background: rgba(239,68,68,0.12);
  color: #ef4444;
  font-size: 0.65rem;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 100px;
}
.dropdown-logout { color: #ef4444; }
.dropdown-logout .dropdown-icon { color: #ef4444; }

/* Transitions */
.theme-dropdown-enter-active, .theme-dropdown-leave-active { transition: opacity 0.15s, transform 0.15s; }
.theme-dropdown-enter-from, .theme-dropdown-leave-to { opacity: 0; transform: translateY(-4px); }
.fade-enter-active, .fade-leave-active { transition: opacity 0.15s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

/* Mobile */
@media (max-width: 767px) {
  .topbar-mobile-btn { display: flex; }
  .topbar-search { max-width: none; }
  .topbar-search-shortcut { display: none; }
  .user-name { display: none; }
}
</style>
