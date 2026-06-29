import type { Ref } from 'vue'

export function useKeyboard(handlers: Record<string, (e: KeyboardEvent) => void>) {
  function handleKeydown(e: KeyboardEvent) {
    const key = e.key
    if (handlers[key]) {
      handlers[key](e)
    }
  }

  function bind() {
    window.addEventListener('keydown', handleKeydown)
  }

  function unbind() {
    window.removeEventListener('keydown', handleKeydown)
  }

  return { bind, unbind }
}
