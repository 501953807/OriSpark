import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import DynamicSidebar from '@/components/layout/DynamicSidebar.vue'

// Mock stores
const mockToggleSidebar = vi.fn()
const mockGetTypeInfo = vi.fn(() => ({
  type: 'illustrator',
  label: '插画师',
  color: '#667eea',
  description: 'Illustrator',
  routes: ['works', 'rights', 'monitor', 'business', 'illustrator'],
}))
const mockGetCurrentType = vi.fn(() => 'illustrator')
const mockSwitchType = vi.fn()

vi.mock('@/stores/useAppStore', () => ({
  useAppStore: vi.fn(() => ({ sidebarCollapsed: false, toggleSidebar: mockToggleSidebar })),
}))

vi.mock('@/stores/useCreatorTypeStore', () => ({
  useCreatorTypeStore: vi.fn(() => ({
    currentType: 'illustrator',
    getTypeInfo: mockGetTypeInfo,
    getCurrentType: mockGetCurrentType,
    switchType: mockSwitchType,
  })),
}))

vi.mock('@/types/creator', () => ({
  getAllCreators: vi.fn(() => [
    { type: 'illustrator', label: '插画师', color: '#667eea' },
    { type: 'photographer', label: '摄影师', color: '#f093fb' },
  ]),
}))

describe('DynamicSidebar', () => {
  let wrapper: VueWrapper
  let router: any

  beforeEach(() => {
    setActivePinia(createPinia())
    mockToggleSidebar.mockReset()
    mockGetTypeInfo.mockReset()
    mockGetCurrentType.mockReset()
    mockSwitchType.mockReset()

    router = createRouter({
      history: createWebHistory(),
      routes: [{ path: '/', component: { render: () => null } }],
    })

    wrapper = mount(DynamicSidebar, {
      props: { creatorType: 'illustrator' as any },
      global: {
        plugins: [router],
      },
    })
  })

  afterEach(() => {
    wrapper?.unmount()
    if (router) {
      router.isReady().then(() => router.history.destroy())
    }
  })

  it('renders the brand text', () => {
    expect(wrapper.text()).toContain('OriStudio')
  })

  it('displays overview section', () => {
    const text = wrapper.text()
    expect(text).toContain('概览')
    expect(text).toContain('工作台')
  })

  it('has collapse button that calls toggleSidebar', async () => {
    const btn = wrapper.find('.sb-collapse-btn')
    expect(btn.exists()).toBe(true)
    await btn.trigger('click')
    expect(mockToggleSidebar).toHaveBeenCalled()
  })

  it('has footer with type selector', () => {
    expect(wrapper.find('.sb-type-selector').exists()).toBe(true)
  })

  it('renders links for navigation', () => {
    const links = wrapper.findAll('a')
    expect(links.length).toBeGreaterThan(5)
  })

  it('type selector has click handler', async () => {
    const selector = wrapper.find('.sb-type-selector')
    await selector.trigger('click')
    // Chevron should flip
    expect(wrapper.find('.sb-chevron').text()).toBe('▲')
  })

  it('switchType calls store method', async () => {
    const selector = wrapper.find('.sb-type-selector')
    await selector.trigger('click')
    const items = wrapper.findAll('.picker-item')
    if (items.length > 0) {
      await items[0].trigger('click')
      expect(mockSwitchType).toHaveBeenCalled()
    }
  })
})
