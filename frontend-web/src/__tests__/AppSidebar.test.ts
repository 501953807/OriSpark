import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import AppSidebar from '@/components/layout/AppSidebar.vue'

// Mock stores
const mockToggleSidebar = vi.fn()
const mockUser = { username: '创作者', email: 'local@oristudio', role: 'creator' }

vi.mock('@/stores/useAppStore', () => ({
  useAppStore: vi.fn(() => ({
    workCount: 12,
    notaryCount: 5,
    alertCount: 3,
  })),
}))

vi.mock('@/stores/useAuthStore', () => ({
  useAuthStore: vi.fn(() => ({
    user: mockUser,
    displayName: '创作者',
    isLoggedIn: true,
    logout: vi.fn(),
  })),
}))

vi.mock('@/composables/useLayoutContext', () => ({
  useLayoutContext: vi.fn(() => ({
    sidebarCollapsed: false,
    toggleSidebar: mockToggleSidebar,
    displayName: '创作者',
    user: mockUser,
  })),
}))

describe('AppSidebar', () => {
  let wrapper: VueWrapper
  let router: any

  beforeEach(() => {
    Object.defineProperty(global, 'localStorage', {
      value: {
        getItem: vi.fn(() => null),
        setItem: vi.fn(),
        removeItem: vi.fn(),
        clear: vi.fn(),
      },
      writable: true,
    })

    setActivePinia(createPinia())
    mockToggleSidebar.mockReset()

    router = createRouter({
      history: createWebHistory(),
      routes: [
        { path: '/app', name: 'dashboard', component: { render: () => null } },
        { path: '/app/works', name: 'works', component: { render: () => null } },
        { path: '/app/ipr', name: 'ipr', component: { render: () => null } },
        { path: '/app/rights', name: 'rights', component: { render: () => null } },
        { path: '/app/risk-warning', name: 'risk-warning', component: { render: () => null } },
      ],
    })

    wrapper = mount(AppSidebar, {
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

  it('renders OriStudio brand', () => {
    expect(wrapper.text()).toContain('OriStudio')
  })

  it('renders all 17 menu items', () => {
    const expectedItems = [
      '工作台', '创意资产', 'IP登记', '权利保护', '内容分发', '商业转化',
      '经营管理', '回收站', '项目分组', '审片视图', '委托看板',
      '风险预警',
      '偏好设置', '第三方对接', '水印预设', '模板管理', '订阅管理',
    ]
    const text = wrapper.text()
    expectedItems.forEach((item) => {
      expect(text).toContain(item)
    })
  })

  it('has collapse button', async () => {
    const btn = wrapper.find('.sb-collapse-btn')
    expect(btn.exists()).toBe(true)
    await btn.trigger('click')
    expect(mockToggleSidebar).toHaveBeenCalled()
  })

  it('has footer with user info', () => {
    expect(wrapper.find('.sb-footer').exists()).toBe(true)
    expect(wrapper.text()).toContain('创作者')
  })

  it('shows workCount badge on 创意资产', () => {
    const text = wrapper.text()
    expect(text).toContain('创意资产')
    expect(text).toContain('12')
  })

  it('shows alertCount badge on 权利保护 and 风险预警', () => {
    const text = wrapper.text()
    expect(text).toContain('权利保护')
    expect(text).toContain('风险预警')
    // alertCount shows as 3 on rights and risk-warning
    expect(text).toContain('3')
  })
})
