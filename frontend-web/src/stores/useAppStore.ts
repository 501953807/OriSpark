import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useGlobalEvents } from '@/composables/useGlobalEvents'

export const useAppStore = defineStore('app', () => {
  // State
  const isDark = ref(false)
  const sidebarCollapsed = ref(false)
  const workCount = ref(0)
  const notaryCount = ref(0)
  const alertCount = ref(0)

  // 跨 store 数据同步：监听全局事件自动更新统计
  const { on } = useGlobalEvents()
  on('work:created', () => { workCount.value++ })
  on('work:deleted', () => { workCount.value = Math.max(0, workCount.value - 1) })
  on('work:notarized', () => { notaryCount.value++ })
  on('alert:new', () => { alertCount.value++ })

  // Actions
  function toggleTheme() {
    isDark.value = !isDark.value
    document.documentElement.classList.toggle('dark', isDark.value)
    localStorage.setItem('oristudio-theme', isDark.value ? 'dark' : 'light')
  }

  function initTheme() {
    const saved = localStorage.getItem('oristudio-theme')
    if (saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      isDark.value = true
      document.documentElement.classList.add('dark')
    }
  }

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
    localStorage.setItem('oristudio-sidebar-collapsed', String(sidebarCollapsed.value))
  }

  function initSidebar() {
    const saved = localStorage.getItem('oristudio-sidebar-collapsed')
    if (saved === 'true') {
      sidebarCollapsed.value = true
    }
  }

  function setStats(stats: { total_works: number; total_notarized: number; infringement_alerts: number }) {
    workCount.value = stats.total_works
    notaryCount.value = stats.total_notarized
    alertCount.value = stats.infringement_alerts
  }

  return {
    isDark,
    sidebarCollapsed,
    workCount,
    notaryCount,
    alertCount,
    toggleTheme,
    initTheme,
    toggleSidebar,
    initSidebar,
    setStats,
  }
})
