<template>
  <header class="topbar" role="banner">
    <div class="topbar-left">
      <!-- P3.4.1: Mobile hamburger inside topbar -->
      <button class="topbar-mobile-btn" @click="$emit('toggleMobile')" aria-label="打开菜单">
        <span></span>
      </button>
      <h1 class="topbar-title">{{ pageTitle }}</h1>
    </div>
    <div class="topbar-right">
      <!-- 主题切换 -->
      <button class="btn btn-ghost" @click="toggleTheme" :title="isDark ? '切换到浅色模式' : '切换到暗色模式'" :aria-label="isDark ? '切换到浅色模式' : '切换到暗色模式'">
        {{ isDark ? '☀️' : '🌙' }}
      </button>

      <!-- 通知面板 -->
      <NotificationPanel />

      <!-- 集成 -->
      <router-link to="/app/integrations" class="btn btn-ghost" aria-label="第三方对接">🔌</router-link>

      <!-- 用户下拉菜单 -->
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
import { useAppStore } from '@/stores/useAppStore'
import { useAuthStore } from '@/stores/useAuthStore'
import NotificationPanel from '@/components/common/NotificationPanel.vue'

defineProps<{ isCollapsed?: boolean }>()
defineEmits(['toggleMobile'])

const route = useRoute()
const appStore = useAppStore()
const authStore = useAuthStore()
const userMenuOpen = ref(false)
const userMenuRef = ref<HTMLElement | null>(null)

const isDark = computed(() => appStore.isDark)

const pageTitles: Record<string, string> = {
  dashboard: '工作台',
  works: '作品管理',
  'work-detail': '作品详情',
  rights: '权利保护',
  ipr: 'IP 登记',
  supply: '商业转化',
  publish: '内容分发',
  business: '经营管理',
  projects: '项目分组',
  settings: '偏好设置',
  integrations: '第三方对接',
  watermarks: '水印预设管理',
  'metadata-templates': '模板管理',
  'work-variants': '作品变体',
  culling: '审片视图',
  subscriptions: '订阅管理',
  commissions: '委托看板',
}

const pageTitle = computed(() => {
  const name = route.name as string
  return pageTitles[name] || 'OriStudio'
})

function toggleTheme() {
  appStore.toggleTheme()
}

async function handleLogout() {
  await authStore.logout()
  userMenuOpen.value = false
  window.location.href = '/login'
}

// 点击外部关闭下拉菜单
function handleClickOutside(event: MouseEvent) {
  if (userMenuRef.value && !userMenuRef.value.contains(event.target as Node)) {
    userMenuOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.topbar {
  position: sticky;
  top: 0;
  z-index: 50;
  background: rgba(15, 23, 42, 0.92);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  padding: 0 24px;
  height: var(--topbar-h);
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border);
}
.topbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.topbar-mobile-btn {
  display: none;
  width: 32px;
  height: 32px;
  border: none;
  background: none;
  cursor: pointer;
  padding: 4px;
  align-items: center;
  justify-content: center;
}
.topbar-mobile-btn span,
.topbar-mobile-btn span::before,
.topbar-mobile-btn span::after {
  display: block;
  width: 18px;
  height: 2px;
  background: var(--fg);
  border-radius: 2px;
}
.topbar-mobile-btn span { position: relative; }
.topbar-mobile-btn span::before, .topbar-mobile-btn span::after { content: ''; position: absolute; left: 0; }
.topbar-mobile-btn span::before { top: -5px; }
.topbar-mobile-btn span::after { top: 5px; }
@media (max-width: 767px) {
  .topbar-mobile-btn { display: inline-flex; }
  .topbar { padding: 0 12px; }
  .topbar-right .btn.btn-primary span { display: none; }
  .topbar-right .btn.btn-primary { padding: 6px 10px; font-size: 0.78rem; }
}
.topbar-title {
  font-family: var(--font-display);
  font-size: 1.2rem;
  font-weight: 700;
  margin: 0;
}
.topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 用户下拉菜单 */
.user-menu {
  position: relative;
}
.user-menu-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  cursor: pointer;
  font-family: var(--font-body);
  font-size: 0.85rem;
  color: var(--fg);
  transition: background 0.2s;
}
.user-menu-btn:hover {
  background: var(--surface-2, #263348);
}
.user-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--grad1), var(--grad2));
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 600;
  font-size: 0.8rem;
  flex-shrink: 0;
}
.user-name {
  font-weight: 500;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.chevron {
  font-size: 0.65rem;
  color: var(--muted);
}
.user-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 220px;
  background: var(--surface, #1e293b);
  border: 1px solid var(--border, #334155);
  border-radius: var(--radius, 8px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  z-index: 200;
  overflow: hidden;
}
.dropdown-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid var(--border);
}
.dropdown-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--grad1), var(--grad2));
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 600;
  font-size: 1rem;
  flex-shrink: 0;
}
.dropdown-info {
  flex: 1;
  min-width: 0;
}
.dropdown-name {
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--fg);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.dropdown-role {
  font-size: 0.75rem;
  color: var(--muted);
  margin-top: 2px;
}
.dropdown-divider {
  height: 1px;
  background: var(--border);
}
.dropdown-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  font-size: 0.88rem;
  color: var(--fg);
  text-decoration: none;
  transition: background 0.15s;
  width: 100%;
  border: none;
  background: none;
  cursor: pointer;
  font-family: var(--font-body);
  text-align: left;
}
.dropdown-item:hover {
  background: var(--surface-2, #263348);
}
.dropdown-icon {
  font-size: 1.1rem;
  width: 20px;
  text-align: center;
}
.dropdown-logout {
  color: #ef4444;
}
.dropdown-logout:hover {
  background: rgba(239, 68, 68, 0.1) !important;
}
.user-menu-overlay {
  position: fixed;
  inset: 0;
  z-index: 199;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
