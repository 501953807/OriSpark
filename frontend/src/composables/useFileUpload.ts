import { ref } from 'vue'

export function useFileUpload(options?: {
  accept?: string
  maxSize?: number
  multiple?: boolean
}) {
  const files = ref<File[]>([])
  const uploading = ref(false)
  const progress = ref(0)

  function addFiles(newFiles: FileList | File[]) {
    const list = Array.from(newFiles)
    if (options?.maxSize) {
      const valid = list.filter(f => f.size <= (options.maxSize || Infinity))
      files.value.push(...valid)
      if (valid.length < list.length) {
        console.warn(`${list.length - valid.length} files exceeded max size`)
      }
    } else {
      files.value.push(...list)
    }
  }

  function removeFile(index: number) {
    files.value.splice(index, 1)
  }

  function clearFiles() {
    files.value = []
  }

  async function upload(uploadFn: (file: File) => Promise<any>): Promise<any[]> {
    uploading.value = true
    progress.value = 0
    const results: any[] = []

    try {
      for (let i = 0; i < files.value.length; i++) {
        results.push(await uploadFn(files.value[i]))
        progress.value = ((i + 1) / files.value.length) * 100
      }
    } finally {
      uploading.value = false
      progress.value = 0
    }

    return results
  }

  return {
    files, uploading, progress,
    addFiles, removeFile, clearFiles, upload,
  }
}
