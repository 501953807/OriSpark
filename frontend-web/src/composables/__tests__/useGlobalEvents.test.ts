import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useGlobalEvents } from '../useGlobalEvents'

describe('useGlobalEvents', () => {
  it('emits and receives an event', () => {
    const { emit, on } = useGlobalEvents()
    const fn = vi.fn()
    const cleanup = on('work:created', fn)

    emit('work:created', { workId: 'w-1' })
    expect(fn).toHaveBeenCalledTimes(1)
    expect(fn).toHaveBeenCalledWith({ workId: 'w-1' })

    cleanup()
  })

  it('does not call listener after cleanup', () => {
    const { emit, on } = useGlobalEvents()
    const fn = vi.fn()
    const cleanup = on('work:deleted', fn)

    cleanup()
    emit('work:deleted', { workId: 'w-1' })
    expect(fn).not.toHaveBeenCalled()
  })

  it('supports multiple listeners for same event', () => {
    const { emit, on } = useGlobalEvents()
    const fn1 = vi.fn()
    const fn2 = vi.fn()
    on('work:updated', fn1)
    on('work:updated', fn2)

    emit('work:updated', { workId: 'w-2' })
    expect(fn1).toHaveBeenCalledTimes(1)
    expect(fn2).toHaveBeenCalledTimes(1)
    expect(fn1).toHaveBeenCalledWith({ workId: 'w-2' })
  })

  it('ignores unknown events silently', () => {
    const { emit } = useGlobalEvents()
    expect(() => emit('work:created', { workId: 'w-3' })).not.toThrow()
  })

  it('works with all defined event types', () => {
    const { emit, on } = useGlobalEvents()
    const handlers = {
      'work:created': vi.fn(),
      'work:deleted': vi.fn(),
      'work:updated': vi.fn(),
      'work:notarized': vi.fn(),
      'contract:signed': vi.fn(),
      'alert:new': vi.fn(),
    }

    for (const [event, fn] of Object.entries(handlers)) {
      on(event as keyof typeof handlers, fn)
    }

    emit('work:created', { workId: 'w-1' })
    emit('work:deleted', { workId: 'w-2' })
    emit('work:updated', { workId: 'w-3' })
    emit('work:notarized', { workId: 'w-4' })
    emit('contract:signed', { contractId: 'c-1' })
    emit('alert:new', { alertId: 'a-1' })

    expect(handlers['work:created']).toHaveBeenCalledWith({ workId: 'w-1' })
    expect(handlers['work:deleted']).toHaveBeenCalledWith({ workId: 'w-2' })
    expect(handlers['work:updated']).toHaveBeenCalledWith({ workId: 'w-3' })
    expect(handlers['work:notarized']).toHaveBeenCalledWith({ workId: 'w-4' })
    expect(handlers['contract:signed']).toHaveBeenCalledWith({ contractId: 'c-1' })
    expect(handlers['alert:new']).toHaveBeenCalledWith({ alertId: 'a-1' })
  })

  it('does not crash when a listener throws', () => {
    const { emit, on } = useGlobalEvents()
    const goodFn = vi.fn()
    const badFn = vi.fn(() => { throw new Error('boom') })

    on('work:created', badFn)
    on('work:created', goodFn)

    expect(() => emit('work:created', { workId: 'w-1' })).not.toThrow()
    expect(badFn).toHaveBeenCalledTimes(1)
    expect(goodFn).toHaveBeenCalledTimes(1)
  })
})
