import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useGlobalEvents } from '@/composables/useGlobalEvents'

type ThemePreset = 'cold-white' | 'warm-gray' | 'deep-blue'

export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref(false)
  const workCount = ref(0)
  const notaryCount = ref(0)
  const alertCount = ref(0)

  const { on } = useGlobalEvents()
  on('work:created', () => { workCount.value++ })
  on('work:deleted', () => { workCount.value = Math.max(0, workCount.value - 1) })
  on('work:notarized', () => { notaryCount.value++ })
  on('alert:new', () => { alertCount.value++ })

  // ── Theme preset system (3 presets via data-theme attribute) ──
  const themePresets: ThemePreset[] = ['cold-white', 'warm-gray', 'deep-blue']
  const currentTheme = ref<ThemePreset>('cold-white')

  function setTheme(theme: ThemePreset) {
    currentTheme.value = theme
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('oristudio-theme', theme)
  }

  function initTheme() {
    const saved = localStorage.getItem('oristudio-theme') as ThemePreset
    if (saved && themePresets.includes(saved)) {
      currentTheme.value = saved
      document.documentElement.setAttribute('data-theme', saved)
    }
  }

  function cycleTheme() {
    const idx = themePresets.indexOf(currentTheme.value)
    setTheme(themePresets[(idx + 1) % themePresets.length])
  }

  // ── Sidebar ──
  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
    localStorage.setItem('oristudio-sidebar-collapsed', String(sidebarCollapsed.value))
  }

  function initSidebar() {
    const saved = localStorage.getItem('oristudio-sidebar-collapsed')
    if (saved === 'true') sidebarCollapsed.value = true
  }

  function setStats(stats: { total_works: number; total_notarized: number; infringement_alerts: number }) {
    workCount.value = stats.total_works
    notaryCount.value = stats.total_notarized
    alertCount.value = stats.infringement_alerts
  }

  return {
    sidebarCollapsed,
    workCount,
    notaryCount,
    alertCount,
    currentTheme,
    themePresets,
    setTheme,
    initTheme,
    cycleTheme,
    toggleSidebar,
    initSidebar,
    setStats,
  }
})
