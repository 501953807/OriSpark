import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore } from '@/stores/useAuthStore'

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

describe('useAuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorageMock.clear()
  })

  it('initializes with no token and user when localStorage is empty', () => {
    const store = useAuthStore()
    expect(store.token).toBeNull()
    expect(store.user).toBeNull()
    expect(store.isLoggedIn).toBe(false)
    expect(store.loading).toBe(false)
    expect(store.error).toBe('')
  })

  it('returns correct displayName when user is null', () => {
    const store = useAuthStore()
    expect(store.displayName).toBe('创作者')
  })

  it('clearError resets error message', () => {
    const store = useAuthStore()
    store.error = 'Something went wrong'
    store.clearError()
    expect(store.error).toBe('')
  })
})
