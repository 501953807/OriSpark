import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import StatCard from '@/components/common/StatCard.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'

describe('StatCard', () => {
  it('renders icon, label, and value', () => {
    const wrapper = mount(StatCard, {
      props: { icon: '📊', label: '总作品数', value: 42 },
    })
    expect(wrapper.find('.stat-icon').text()).toBe('📊')
    expect(wrapper.find('.stat-label').text()).toBe('总作品数')
    expect(wrapper.find('.stat-value').text()).toBe('42')
  })

  it('renders up trend with positive number', () => {
    const wrapper = mount(StatCard, {
      props: { icon: '📈', label: '增长', value: '128', trend: 12 },
    })
    expect(wrapper.find('.stat-trend.up').exists()).toBe(true)
    expect(wrapper.find('.stat-trend').text()).toContain('12')
  })

  it('renders down trend with negative number', () => {
    const wrapper = mount(StatCard, {
      props: { icon: '📉', label: '下降', value: '5', trend: -8 },
    })
    expect(wrapper.find('.stat-trend.down').exists()).toBe(true)
    expect(wrapper.find('.stat-trend').text()).toContain('8')
  })

  it('applies clickable class when to prop is provided', () => {
    const wrapper = mount(StatCard, {
      props: { icon: '🔗', label: 'Clickable', value: 1, to: '/app/works' },
    })
    expect(wrapper.find('.stat-card.clickable').exists()).toBe(true)
  })

  it('is not clickable when to prop is missing', () => {
    const wrapper = mount(StatCard, {
      props: { icon: '📌', label: 'Static', value: 0 },
    })
    expect(wrapper.find('.stat-card.clickable').exists()).toBe(false)
  })

  it('defaults color to green background', () => {
    const wrapper = mount(StatCard, {
      props: { icon: '🎯', label: 'Default', value: 99 },
    })
    const icon = wrapper.find('.stat-icon')
    // Browser may normalize OKLCH percentages to decimals
    expect(icon.attributes('style')).toMatch(/oklch\(0\.56 0\.12 170/)
  })

  it('applies custom color background', () => {
    const wrapper = mount(StatCard, {
      props: { icon: '🔥', label: 'Orange', value: 7, color: 'orange' },
    })
    const icon = wrapper.find('.stat-icon')
    expect(icon.attributes('style')).toMatch(/oklch\(0\.62 0\.18 55/)
  })
})

describe('StatusBadge', () => {
  it('renders status label directly when no labels map', () => {
    const wrapper = mount(StatusBadge, {
      props: { status: 'active' },
    })
    expect(wrapper.text()).toBe('active')
  })

  it('renders mapped label from labels prop', () => {
    const wrapper = mount(StatusBadge, {
      props: {
        status: 'confirmed',
        labels: { confirmed: '已存证', draft: '待存证' },
      },
    })
    expect(wrapper.text()).toBe('已存证')
  })

  it('applies default variant when no variants map', () => {
    const wrapper = mount(StatusBadge, {
      props: { status: 'unknown_status' },
    })
    expect(wrapper.find('.default').exists()).toBe(true)
  })

  it('applies custom variant from variants map', () => {
    const wrapper = mount(StatusBadge, {
      props: {
        status: 'confirmed',
        variants: { confirmed: 'success' },
      },
    })
    expect(wrapper.find('.success').exists()).toBe(true)
  })

  it('matches success/confirmed/active class for success variant', () => {
    for (const status of ['success', 'confirmed', 'active']) {
      const wrapper = mount(StatusBadge, {
        props: { status, variants: { [status]: 'success' } },
      })
      expect(wrapper.find('.success').exists()).toBe(true)
    }
  })

  it('matches warning/pending class for warning variant', () => {
    const wrapper = mount(StatusBadge, {
      props: { status: 'pending', variants: { pending: 'warning' } },
    })
    expect(wrapper.find('.warning').exists()).toBe(true)
  })

  it('matches error/failed class for error variant', () => {
    const wrapper = mount(StatusBadge, {
      props: { status: 'failed', variants: { failed: 'error' } },
    })
    expect(wrapper.find('.error').exists()).toBe(true)
  })

  it('matches info/draft class for info variant', () => {
    const wrapper = mount(StatusBadge, {
      props: { status: 'draft', variants: { draft: 'info' } },
    })
    expect(wrapper.find('.info').exists()).toBe(true)
  })

  it('falls back to default when label not in map', () => {
    const wrapper = mount(StatusBadge, {
      props: {
        status: 'pending_review',
        labels: { confirmed: '已存证' },
      },
    })
    expect(wrapper.text()).toBe('pending_review')
  })
})
