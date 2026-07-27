import { describe, it, expect, vi } from 'vitest'
import { useFileUpload } from '@/composables/useFileUpload'

describe('useFileUpload', () => {
  it('starts with empty files', () => {
    const { files } = useFileUpload()
    expect(files.value).toHaveLength(0)
  })

  it('adds files', () => {
    const { files, addFiles } = useFileUpload()
    const f1 = new File(['a'], 'a.txt')
    const f2 = new File(['b'], 'b.txt')
    addFiles([f1, f2])
    expect(files.value).toHaveLength(2)
    expect(files.value[0].name).toBe('a.txt')
    expect(files.value[1].name).toBe('b.txt')
  })

  it('removes file by index', () => {
    const { files, addFiles, removeFile } = useFileUpload()
    addFiles([new File(['a'], 'a.txt'), new File(['b'], 'b.txt'), new File(['c'], 'c.txt')])
    removeFile(1)
    expect(files.value).toHaveLength(2)
    expect(files.value[0].name).toBe('a.txt')
    expect(files.value[1].name).toBe('c.txt')
  })

  it('clears all files', () => {
    const { files, addFiles, clearFiles } = useFileUpload()
    addFiles([new File(['a'], 'a.txt'), new File(['b'], 'b.txt')])
    clearFiles()
    expect(files.value).toHaveLength(0)
  })

  it('filters files by max size', () => {
    const { files, addFiles } = useFileUpload({ maxSize: 100 })
    const small = new File(['a'], 'small.txt')
    const big = new File(['x'.repeat(200)], 'big.txt')
    addFiles([small, big])
    expect(files.value).toHaveLength(1)
    expect(files.value[0].name).toBe('small.txt')
  })

  it('accepts all files when no maxSize set', () => {
    const { files, addFiles } = useFileUpload()
    const big = new File(['x'.repeat(200)], 'big.txt')
    addFiles([big])
    expect(files.value).toHaveLength(1)
  })

  it('uploads files sequentially', async () => {
    const { files, addFiles, upload } = useFileUpload()
    addFiles([new File(['a'], 'a.txt'), new File(['b'], 'b.txt')])

    const callOrder: string[] = []
    const fn = vi.fn(async (file: File) => {
      callOrder.push(file.name)
      return { url: `https://example.com/${file.name}` }
    })

    const results = await upload(fn)
    expect(results).toHaveLength(2)
    expect(callOrder).toEqual(['a.txt', 'b.txt'])
  })

  it('sets uploading state during upload', async () => {
    const { files, addFiles, upload, uploading } = useFileUpload()
    addFiles([new File(['a'], 'a.txt'), new File(['b'], 'b.txt')])

    const fn = vi.fn(async () => ({ ok: true }))
    const promise = upload(fn)

    expect(uploading.value).toBe(true)
    await promise
    expect(uploading.value).toBe(false)
  })

  it('resets progress after upload', async () => {
    const { files, addFiles, upload, progress } = useFileUpload()
    addFiles([new File(['a'], 'a.txt'), new File(['b'], 'b.txt')])

    const fn = vi.fn(async () => ({ ok: true }))
    await upload(fn)
    expect(progress.value).toBe(0)
  })

  it('handles upload failure gracefully', async () => {
    const { files, addFiles, upload } = useFileUpload()
    addFiles([new File(['a'], 'a.txt')])

    const fn = vi.fn(async () => {
      throw new Error('upload failed')
    })

    await expect(upload(fn)).rejects.toThrow('upload failed')
  })

  it('returns empty array for empty file list', async () => {
    const { upload } = useFileUpload()
    const fn = vi.fn(async () => ({ ok: true }))
    const results = await upload(fn)
    expect(results).toEqual([])
  })
})
