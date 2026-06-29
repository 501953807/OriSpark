import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useToast } from '@/composables/useToast'
import { useModal } from '@/composables/useModal'
import { useFileUpload } from '@/composables/useFileUpload'

describe('useToast', () => {
  it('shows and removes toasts', () => {
    const { toasts, show, success, error } = useToast()
    expect(toasts.value).toHaveLength(0)

    success('ok')
    expect(toasts.value).toHaveLength(1)
    expect(toasts.value[0].type).toBe('success')

    error('fail')
    expect(toasts.value).toHaveLength(2)
    expect(toasts.value[1].type).toBe('error')

    // remove
    const id = toasts.value[0].id
    toasts.value = toasts.value.filter(t => t.id !== id)
    expect(toasts.value).toHaveLength(1)
  })
})

describe('useModal', () => {
  it('toggles visibility', () => {
    const { visible, open, close, toggle } = useModal()
    expect(visible.value).toBe(false)

    open()
    expect(visible.value).toBe(true)

    close()
    expect(visible.value).toBe(false)

    toggle()
    expect(visible.value).toBe(true)
    toggle()
    expect(visible.value).toBe(false)
  })
})

describe('useFileUpload', () => {
  it('manages file list', () => {
    const { files, addFiles, removeFile, clearFiles } = useFileUpload()
    expect(files.value).toHaveLength(0)

    const f1 = new File(['a'], 'a.txt')
    const f2 = new File(['b'], 'b.txt')
    addFiles([f1, f2])
    expect(files.value).toHaveLength(2)

    removeFile(0)
    expect(files.value).toHaveLength(1)
    expect(files.value[0].name).toBe('b.txt')

    clearFiles()
    expect(files.value).toHaveLength(0)
  })

  it('handles upload progress', async () => {
    const { addFiles, upload, uploading, progress } = useFileUpload()
    addFiles([new File(['x'], 'x.txt'), new File(['y'], 'y.txt')])

    const fn = vi.fn().mockResolvedValue({ ok: true })
    const promise = upload(fn)
    expect(uploading.value).toBe(true)

    const results = await promise
    expect(results).toHaveLength(2)
    expect(uploading.value).toBe(false)
    expect(fn).toHaveBeenCalledTimes(2)
  })
})
