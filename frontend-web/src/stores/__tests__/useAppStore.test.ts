import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useAppStore } from '@/stores/useAppStore'

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: vi.fn((key: string) => store[key] ?? null),
    setItem: vi.fn((key: string, value: string) => { store[key] = value }),
    removeItem: vi.fn((key: string) => { delete store[key] }),
    clear: vi.fn(() => { store = {} }),
  }
})()
vi.stubGlobal('localStorage', localStorageMock)

describe('useAppStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorageMock.clear()
  })

  it('initializes with default values', () => {
    const store = useAppStore()
    expect(store.sidebarCollapsed).toBe(false)
    expect(store.workCount).toBe(0)
    expect(store.notaryCount).toBe(0)
    expect(store.alertCount).toBe(0)
    expect(store.currentTheme).toBe('cold-white')
    expect(store.themePresets).toEqual(['cold-white', 'warm-gray', 'deep-blue'])
  })

  it('sets theme and updates DOM attribute', () => {
    const store = useAppStore()
    expect(store.currentTheme).toBe('cold-white')

    store.setTheme('deep-blue')
    expect(store.currentTheme).toBe('deep-blue')
    expect(document.documentElement.getAttribute('data-theme')).toBe('deep-blue')
  })

  it('cycles through theme presets', () => {
    const store = useAppStore()
    store.setTheme('cold-white')
    store.cycleTheme()
    expect(store.currentTheme).toBe('warm-gray')
    store.cycleTheme()
    expect(store.currentTheme).toBe('deep-blue')
    store.cycleTheme()
    expect(store.currentTheme).toBe('cold-white')
  })

  it('persists theme to localStorage', () => {
    const store = useAppStore()
    store.setTheme('warm-gray')
    expect(localStorage.setItem).toHaveBeenCalledWith('oristudio-theme', 'warm-gray')
  })

  it('toggles sidebar collapse state', () => {
    const store = useAppStore()
    expect(store.sidebarCollapsed).toBe(false)
    store.toggleSidebar()
    expect(store.sidebarCollapsed).toBe(true)
    store.toggleSidebar()
    expect(store.sidebarCollapsed).toBe(false)
  })

  it('persists sidebar state to localStorage', () => {
    const store = useAppStore()
    store.toggleSidebar()
    expect(localStorage.setItem).toHaveBeenCalledWith('oristudio-sidebar-collapsed', 'true')
  })

  it('sets stats correctly', () => {
    const store = useAppStore()
    store.setStats({ total_works: 10, total_notarized: 5, infringement_alerts: 3 })
    expect(store.workCount).toBe(10)
    expect(store.notaryCount).toBe(5)
    expect(store.alertCount).toBe(3)
  })

  it('initializes theme from localStorage', () => {
    localStorageMock.setItem('oristudio-theme', 'deep-blue')
    const store = useAppStore()
    store.initTheme()
    expect(store.currentTheme).toBe('deep-blue')
    expect(document.documentElement.getAttribute('data-theme')).toBe('deep-blue')
  })

  it('initializes sidebar from localStorage', () => {
    localStorageMock.setItem('oristudio-sidebar-collapsed', 'true')
    const store = useAppStore()
    store.initSidebar()
    expect(store.sidebarCollapsed).toBe(true)
  })
})
