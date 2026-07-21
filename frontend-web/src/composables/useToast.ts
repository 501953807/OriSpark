import { ref } from 'vue'

type ToastType = 'success' | 'error' | 'warning' | 'info'

export function useToast() {
  const toasts = ref<Array<{ id: number; message: string; type: ToastType }>>([])
  let idCounter = 0

  function show(message: string, type: ToastType = 'info', duration: number = 3000) {
    const id = ++idCounter
    toasts.value.push({ id, message, type })
    if (duration > 0) {
      setTimeout(() => remove(id), duration)
    }
  }

  function remove(id: number) {
    const idx = toasts.value.findIndex(t => t.id === id)
    if (idx > -1) toasts.value.splice(idx, 1)
  }

  function success(msg: string) { show(msg, 'success') }
  function error(msg: string) { show(msg, 'error', 5000) }
  function warning(msg: string) { show(msg, 'warning', 4000) }
  function info(msg: string) { show(msg, 'info') }

  return { toasts, show, remove, success, error, warning, info }
}
