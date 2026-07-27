import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useToast } from '@/composables/useToast'

describe('useToast', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('starts with empty toasts', () => {
    const { toasts } = useToast()
    expect(toasts.value).toHaveLength(0)
  })

  it('adds a toast via show()', () => {
    const { toasts, show } = useToast()
    show('Hello', 'info')
    expect(toasts.value).toHaveLength(1)
    expect(toasts.value[0].message).toBe('Hello')
    expect(toasts.value[0].type).toBe('info')
    expect(typeof toasts.value[0].id).toBe('number')
  })

  it('adds success toast', () => {
    const { toasts, success } = useToast()
    success('Saved!')
    expect(toasts.value).toHaveLength(1)
    expect(toasts.value[0].type).toBe('success')
    expect(toasts.value[0].message).toBe('Saved!')
  })

  it('adds error toast', () => {
    const { toasts, error } = useToast()
    error('Failed!')
    expect(toasts.value).toHaveLength(1)
    expect(toasts.value[0].type).toBe('error')
  })

  it('adds warning toast', () => {
    const { toasts, warning } = useToast()
    warning('Watch out!')
    expect(toasts.value).toHaveLength(1)
    expect(toasts.value[0].type).toBe('warning')
  })

  it('adds info toast', () => {
    const { toasts, info } = useToast()
    info('Just letting you know')
    expect(toasts.value).toHaveLength(1)
    expect(toasts.value[0].type).toBe('info')
  })

  it('accumulates multiple toasts', () => {
    const { toasts, success, error, warning } = useToast()
    success('ok')
    error('fail')
    warning('careful')
    expect(toasts.value).toHaveLength(3)
    expect(toasts.value[0].type).toBe('success')
    expect(toasts.value[1].type).toBe('error')
    expect(toasts.value[2].type).toBe('warning')
  })

  it('removes toast by id', () => {
    const { toasts, show, remove } = useToast()
    show('first', 'info')
    show('second', 'success')
    const firstId = toasts.value[0].id
    remove(firstId)
    expect(toasts.value).toHaveLength(1)
    expect(toasts.value[0].message).toBe('second')
  })

  it('remove is idempotent - removing non-existent id does nothing', () => {
    const { toasts, show, remove } = useToast()
    show('hello', 'info')
    remove(99999)
    expect(toasts.value).toHaveLength(1)
  })

  it('auto-removes success toast after default duration (3s)', () => {
    const { toasts, success } = useToast()
    success('will disappear')
    expect(toasts.value).toHaveLength(1)
    vi.advanceTimersByTime(3000)
    expect(toasts.value).toHaveLength(0)
  })

  it('auto-removes error toast after 5s', () => {
    const { toasts, error } = useToast()
    error('error stays longer')
    vi.advanceTimersByTime(4000)
    expect(toasts.value).toHaveLength(1)
    vi.advanceTimersByTime(1000)
    expect(toasts.value).toHaveLength(0)
  })

  it('auto-removes warning toast after 4s', () => {
    const { toasts, warning } = useToast()
    warning('warning timeout')
    vi.advanceTimersByTime(4000)
    expect(toasts.value).toHaveLength(0)
  })

  it('auto-removes info toast after default 3s', () => {
    const { toasts, info } = useToast()
    info('info timeout')
    vi.advanceTimersByTime(3000)
    expect(toasts.value).toHaveLength(0)
  })

  it('does not auto-remove when duration is 0', () => {
    const { toasts, show } = useToast()
    show('persistent', 'info', 0)
    vi.advanceTimersByTime(5000)
    expect(toasts.value).toHaveLength(1)
  })

  it('can manually remove before auto-dismiss', () => {
    const { toasts, show, remove } = useToast()
    show('quick', 'success')
    const id = toasts.value[0].id
    remove(id)
    vi.advanceTimersByTime(3000)
    expect(toasts.value).toHaveLength(0)
  })

  it('generates unique sequential ids', () => {
    const { toasts, show } = useToast()
    show('one', 'info')
    show('two', 'success')
    show('three', 'error')
    const ids = toasts.value.map(t => t.id)
    expect(ids[0]).toBeLessThan(ids[1])
    expect(ids[1]).toBeLessThan(ids[2])
  })

  it('handles custom duration', () => {
    const { toasts, show } = useToast()
    show('custom', 'info', 1000)
    vi.advanceTimersByTime(999)
    expect(toasts.value).toHaveLength(1)
    vi.advanceTimersByTime(1)
    expect(toasts.value).toHaveLength(0)
  })
})
