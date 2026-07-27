import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useCreatorTypeStore } from '@/stores/useCreatorTypeStore'

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

// Mock router
const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mockPush }),
}))

describe('useCreatorTypeStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorageMock.clear()
    mockPush.mockReset()
  })

  it('initializes with default creator type (illustrator)', () => {
    const store = useCreatorTypeStore()
    expect(store.currentType).toBe('illustrator')
    expect(store.history).toEqual([])
  })

  it('loads type from localStorage on init', () => {
    localStorageMock.setItem('oristudio-creator-type', 'photographer')
    const store = useCreatorTypeStore()
    expect(store.currentType).toBe('photographer')
  })

  it('persists type to localStorage on setType', () => {
    const store = useCreatorTypeStore()
    store.setType('photographer')
    expect(localStorage.setItem).toHaveBeenCalledWith('oristudio-creator-type', 'photographer')
  })

  it('setType adds to history', () => {
    const store = useCreatorTypeStore()
    store.setType('photographer')
    store.setType('video')
    expect(store.history.length).toBe(2)
    expect(store.history).toContain('illustrator')
    expect(store.history).toContain('photographer')
  })

  it('switchType calls setType and navigates', () => {
    const store = useCreatorTypeStore()
    store.switchType('photographer')
    expect(mockPush).toHaveBeenCalled()
  })

  it('switchType does nothing when switching to same type', () => {
    const store = useCreatorTypeStore()
    // Current type is illustrator by default
    store.switchType('illustrator')
    expect(mockPush).not.toHaveBeenCalled()
  })

  it('getCurrentType returns current type', () => {
    const store = useCreatorTypeStore()
    expect(store.getCurrentType()).toBe('illustrator')
    store.setType('video')
    expect(store.getCurrentType()).toBe('video')
  })

  it('getTypeInfo returns correct info for a given type', () => {
    const store = useCreatorTypeStore()
    const info = store.getTypeInfo('photographer')
    expect(info).not.toBeNull()
    expect(info?.type).toBe('photographer')
    expect(info?.label).toBeDefined()
    expect(Array.isArray(info?.routes)).toBe(true)
  })

  it('getTypeInfo returns null for unknown type', () => {
    const store = useCreatorTypeStore()
    const info = store.getTypeInfo('unknown' as any)
    expect(info).toBeNull()
  })

  it('getTypeInfo uses current type when no type argument provided', () => {
    const store = useCreatorTypeStore()
    const info = store.getTypeInfo()
    expect(info?.type).toBe('illustrator')
  })
})
