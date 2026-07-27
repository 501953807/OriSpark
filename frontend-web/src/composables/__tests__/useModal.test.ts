import { describe, it, expect, vi } from 'vitest'
import { useModal } from '@/composables/useModal'

describe('useModal', () => {
  it('starts closed', () => {
    const { visible } = useModal()
    expect(visible.value).toBe(false)
  })

  it('opens modal', () => {
    const { visible, open } = useModal()
    open()
    expect(visible.value).toBe(true)
  })

  it('closes modal', () => {
    const { visible, open, close } = useModal()
    open()
    close()
    expect(visible.value).toBe(false)
  })

  it('toggles modal', () => {
    const { visible, toggle } = useModal()
    expect(visible.value).toBe(false)
    toggle()
    expect(visible.value).toBe(true)
    toggle()
    expect(visible.value).toBe(false)
  })

  it('open is idempotent', () => {
    const { visible, open } = useModal()
    open()
    open()
    expect(visible.value).toBe(true)
  })

  it('close is idempotent', () => {
    const { visible, close } = useModal()
    close()
    close()
    expect(visible.value).toBe(false)
  })
})
