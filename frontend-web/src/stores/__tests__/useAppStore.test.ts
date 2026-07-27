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

// Mock DOM APIs
vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: false, addListener: () => {}, removeListener: () => {} })))

describe('useAppStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorageMock.clear()
  })

  it('initializes with default values', () => {
    const store = useAppStore()
    expect(store.isDark).toBe(false)
    expect(store.sidebarCollapsed).toBe(false)
    expect(store.workCount).toBe(0)
    expect(store.notaryCount).toBe(0)
    expect(store.alertCount).toBe(0)
  })

  it('toggles theme and updates DOM class', () => {
    const store = useAppStore()
    expect(store.isDark).toBe(false)
    expect(document.documentElement.classList.contains('dark')).toBe(false)

    store.toggleTheme()
    expect(store.isDark).toBe(true)
    expect(document.documentElement.classList.contains('dark')).toBe(true)

    store.toggleTheme()
    expect(store.isDark).toBe(false)
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })

  it('toggles sidebar collapse state', () => {
    const store = useAppStore()
    expect(store.sidebarCollapsed).toBe(false)

    store.toggleSidebar()
    expect(store.sidebarCollapsed).toBe(true)

    store.toggleSidebar()
    expect(store.sidebarCollapsed).toBe(false)
  })

  it('persists theme to localStorage on toggle', () => {
    const store = useAppStore()
    store.toggleTheme()
    expect(localStorage.setItem).toHaveBeenCalledWith('oristudio-theme', 'dark')

    store.toggleTheme()
    expect(localStorage.setItem).toHaveBeenCalledWith('oristudio-theme', 'light')
  })

  it('persists sidebar state to localStorage on toggle', () => {
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
})
