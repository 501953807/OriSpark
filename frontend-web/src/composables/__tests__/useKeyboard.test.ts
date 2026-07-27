import { describe, it, expect, vi } from 'vitest'
import { useKeyboard } from '@/composables/useKeyboard'

describe('useKeyboard', () => {
  it('binds and unbinds keydown listener', () => {
    const handlers = {
      Escape: vi.fn(),
      Enter: vi.fn(),
    }
    const { bind, unbind } = useKeyboard(handlers)

    const addSpy = vi.spyOn(window, 'addEventListener')
    const removeSpy = vi.spyOn(window, 'removeEventListener')

    bind()
    expect(addSpy).toHaveBeenCalledWith('keydown', expect.any(Function))

    unbind()
    expect(removeSpy).toHaveBeenCalledWith('keydown', expect.any(Function))

    addSpy.mockRestore()
    removeSpy.mockRestore()
  })

  it('calls handler when matching key is pressed', () => {
    const handlers = {
      a: vi.fn((e: KeyboardEvent) => { e.preventDefault() }),
    }
    const { bind } = useKeyboard(handlers)
    bind()

    const event = new KeyboardEvent('keydown', { key: 'a' })
    window.dispatchEvent(event)
    expect(handlers.a).toHaveBeenCalled()

    window.removeEventListener('keydown', handlers.a as any)
  })

  it('does not call handler for non-matching key', () => {
    const handlers = {
      a: vi.fn(),
    }
    const { bind } = useKeyboard(handlers)
    bind()

    const event = new KeyboardEvent('keydown', { key: 'b' })
    window.dispatchEvent(event)
    expect(handlers.a).not.toHaveBeenCalled()

    window.removeEventListener('keydown', handlers.a as any)
  })

  it('passes keyboard event to handler', () => {
    let receivedEvent: KeyboardEvent | null = null
    const handlers = {
      x: (e: KeyboardEvent) => { receivedEvent = e },
    }
    const { bind } = useKeyboard(handlers)
    bind()

    const event = new KeyboardEvent('keydown', { key: 'x', ctrlKey: true })
    window.dispatchEvent(event)
    expect(receivedEvent).toBe(event)
    expect(receivedEvent?.ctrlKey).toBe(true)

    window.removeEventListener('keydown', handlers.x as any)
  })

  it('handles multiple handlers', () => {
    const h1 = vi.fn()
    const h2 = vi.fn()
    const handlers = { q: h1, w: h2 }
    const { bind } = useKeyboard(handlers)
    bind()

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'q' }))
    expect(h1).toHaveBeenCalled()
    expect(h2).not.toHaveBeenCalled()

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'w' }))
    expect(h2).toHaveBeenCalled()

    window.removeEventListener('keydown', handlers.q as any)
    window.removeEventListener('keydown', handlers.w as any)
  })
})
