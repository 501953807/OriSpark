import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import StatCard from '@/components/common/StatCard.vue'
import SearchBar from '@/components/common/SearchBar.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import EmptyState from '@/components/common/EmptyState.vue'

describe('StatCard', () => {
  it('renders label and value', () => {
    const wrapper = mount(StatCard, {
      props: { icon: '🎨', label: '总数', value: 42 },
      global: { stubs: { 'router-link': true } },
    })
    expect(wrapper.text()).toContain('总数')
    expect(wrapper.text()).toContain('42')
  })

  it('renders trend correctly', () => {
    const up = mount(StatCard, {
      props: { icon: '📈', label: '增长', value: 100, trend: 15, color: 'green' },
      global: { stubs: { 'router-link': true } },
    })
    expect(up.text()).toContain('15%')

    const down = mount(StatCard, {
      props: { icon: '📉', label: '下降', value: 50, trend: -10, color: 'orange' },
      global: { stubs: { 'router-link': true } },
    })
    expect(down.text()).toContain('10%')
  })
})

describe('SearchBar', () => {
  it('emits search on enter', async () => {
    const wrapper = mount(SearchBar, {
      props: { modelValue: '', placeholder: '搜索...' },
    })
    const input = wrapper.find('input')
    await input.setValue('test')
    await input.trigger('keyup.enter')
    expect(wrapper.emitted('search')).toBeTruthy()
    expect(wrapper.emitted('search')![0]).toEqual(['test'])
  })

  it('clears on button click', async () => {
    const wrapper = mount(SearchBar, {
      props: { modelValue: 'hello' },
    })
    await wrapper.find('.search-clear').trigger('click')
    expect(wrapper.emitted('update:modelValue')![0]).toEqual([''])
  })
})

describe('StatusBadge', () => {
  it('renders status label', () => {
    const wrapper = mount(StatusBadge, {
      props: { status: 'confirmed', labels: { confirmed: '已确认' }, variants: { confirmed: 'success' } },
    })
    expect(wrapper.text()).toContain('已确认')
    expect(wrapper.classes()).toContain('success')
  })

  it('falls back to raw status', () => {
    const wrapper = mount(StatusBadge, {
      props: { status: 'unknown', labels: {} },
    })
    expect(wrapper.text()).toContain('unknown')
  })
})

describe('EmptyState', () => {
  it('renders title and description', () => {
    const wrapper = mount(EmptyState, {
      props: { icon: '📭', title: '空空如也', description: '暂无数据' },
    })
    expect(wrapper.text()).toContain('空空如也')
    expect(wrapper.text()).toContain('暂无数据')
  })

  it('renders slot content', () => {
    const wrapper = mount(EmptyState, {
      props: { title: '空' },
      slots: { default: '<button>添加</button>' },
    })
    expect(wrapper.text()).toContain('添加')
  })
})
