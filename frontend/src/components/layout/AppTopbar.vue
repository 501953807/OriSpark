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

      <!-- 设置 -->
      <router-link to="/app/settings" class="btn btn-ghost" aria-label="偏好设置">⚙️</router-link>

      <!-- 集成 -->
      <router-link to="/app/integrations" class="btn btn-ghost" aria-label="第三方对接">🔌</router-link>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/useAppStore'
import NotificationPanel from '@/components/common/NotificationPanel.vue'

defineEmits(['toggleMobile'])

const route = useRoute()
const appStore = useAppStore()
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
</script>

<style scoped>
.topbar {
  position: sticky;
  top: 0;
  z-index: 50;
  background: oklch(98% 0.004 240 / 0.85);
  backdrop-filter: blur(16px);
  padding: 0 24px;
  height: var(--topbar-h);
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border);
}
.dark .topbar {
  background: oklch(18% 0.01 240 / 0.85);
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
</style>
