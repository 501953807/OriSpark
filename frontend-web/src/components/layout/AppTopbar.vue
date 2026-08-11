<template>
  <header class="topbar drag-region" role="banner">
    <div class="topbar-left">
      <button class="topbar-mobile-btn" @click="$emit('toggleMobile')" aria-label="打开菜单">
        <span></span>
      </button>
      <h1 class="topbar-title">{{ pageTitle }}</h1>
    </div>
    <div class="topbar-right">
      <!-- Theme switcher — color swatch panel -->
      <div class="theme-switcher" :class="{ open: themePickerOpen }">
        <button
          class="theme-picker-btn"
          :title="themeLabel(appStore.currentTheme)"
          @click="themePickerOpen = !themePickerOpen"
        >
          <span class="theme-dot active-dot" :style="{ background: themeColor(appStore.currentTheme) }"></span>
          <span class="theme-dot" :style="{ background: themeColor('warm-gray') }"></span>
          <span class="theme-dot" :style="{ background: themeColor('deep-blue') }"></span>
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

      <!-- Notification -->
      <NotificationPanel />

      <!-- Integrations -->
      <router-link to="/app/integrations" class="topbar-action" aria-label="第三方对接">🔌</router-link>

      <!-- User menu -->
      <div class="user-menu" ref="userMenuRef">
        <button class="user-menu-btn" @click="userMenuOpen = !userMenuOpen" aria-label="用户菜单">
          <div class="user-avatar">{{ (authStore.displayName || 'U').charAt(0).toUpperCase() }}</div>
          <span v-if="!isCollapsed" class="user-name">{{ authStore.displayName }}</span>
          <span class="chevron">{{ userMenuOpen ? '▲' : '▼' }}</span>
        </button>
        <Teleport to="body">
          <div v-if="userMenuOpen" class="user-menu-overlay" @click="userMenuOpen = false"></div>
          <Transition name="fade">
            <div v-if="userMenuOpen" class="user-dropdown">
              <div class="dropdown-header">
                <div class="dropdown-avatar">{{ (authStore.displayName || 'U').charAt(0).toUpperCase() }}</div>
                <div class="dropdown-info">
                  <div class="dropdown-name">{{ authStore.displayName }}</div>
                  <div class="dropdown-role">{{ authStore.user?.role || '用户' }}</div>
                </div>
              </div>
              <div class="dropdown-divider"></div>
              <router-link to="/app/settings/subscriptions" class="dropdown-item" @click="userMenuOpen = false">
                <span class="dropdown-icon">💎</span> 订阅管理
              </router-link>
              <router-link to="/app/settings" class="dropdown-item" @click="userMenuOpen = false">
                <span class="dropdown-icon">⚙️</span> 偏好设置
              </router-link>
              <div class="dropdown-divider"></div>
              <button class="dropdown-item dropdown-logout" @click="handleLogout">
                <span class="dropdown-icon">🚪</span> 退出登录
              </button>
            </div>
          </Transition>
        </Teleport>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { useLayoutContext } from '@/composables/useLayoutContext'
import { useAppStore } from '@/stores/useAppStore'
import { useAuthStore } from '@/stores/useAuthStore'
import NotificationPanel from '@/components/common/NotificationPanel.vue'

defineProps<{ isCollapsed?: boolean }>()
defineEmits(['toggleMobile'])

const route = useRoute()
const {
  sidebarCollapsed: isCollapsedProp,
  toggleSidebar,
  user,
  displayName,
  isLoggedIn,
  logout,
  currentTheme,
  setTheme,
  themePresets,
  workCount,
  notaryCount,
  alertCount,
} = useLayoutContext()
const appStore = useAppStore()
const authStore = useAuthStore()
const userMenuOpen = ref(false)
const userMenuRef = ref<HTMLElement | null>(null)
const themePickerOpen = ref(false)

function themeColor(t: string): string {
  if (t === 'cold-white') return 'oklch(54% 0.16 280)'
  if (t === 'warm-gray') return 'oklch(54% 0.14 40)'
  return 'oklch(65% 0.13 280)'
}
function themeLabel(t: string): string {
  return t === 'cold-white' ? '冷白商务' : t === 'warm-gray' ? '暖灰温和' : '深蓝夜间'
}

const pageTitles: Record<string, string> = {
  dashboard: '工作台', works: '作品管理', 'work-detail': '作品详情',
  rights: '权利保护', ipr: 'IP 登记', supply: '商业转化',
  publish: '内容分发', business: '经营管理', projects: '项目分组',
  settings: '偏好设置', integrations: '第三方对接',
  watermarks: '水印预设管理', 'metadata-templates': '模板管理',
  'work-variants': '作品变体', culling: '审片视图',
  subscriptions: '订阅管理', commissions: '委托看板',
}

const pageTitle = computed(() => pageTitles[(route.name as string)] || 'OriStudio')

async function handleLogout() {
  await logout()
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

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  document.addEventListener('click', handleThemeClickOutside)
})
onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('click', handleThemeClickOutside)
})
</script>

<style scoped>
.topbar-mobile-btn {
  display: none; width: 32px; height: 32px; border: none; background: none;
  cursor: pointer; padding: 4px; align-items: center; justify-content: center;
}
.topbar-mobile-btn span {
  display: block; width: 18px; height: 2px; background: var(--fg);
  border-radius: 2px; position: relative;
}
.topbar-mobile-btn span::before,
.topbar-mobile-btn span::after {
  content: ''; position: absolute; left: 0; width: 100%; height: 100%;
  background: var(--fg); border-radius: 2px;
}
.topbar-mobile-btn span::before { top: -5px; }
.topbar-mobile-btn span::after { top: 5px; }

@media (max-width: 767px) {
  .topbar-mobile-btn { display: inline-flex; }
  .topbar { padding: 0 12px; }
}

.topbar-title {
  font-family: var(--font-display); font-size: var(--text-lg);
  font-weight: 700; margin: 0; color: var(--fg);
}
</style>
