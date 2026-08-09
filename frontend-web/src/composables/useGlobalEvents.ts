/** Global event bus for cross-store communication. */

export interface GlobalEventMap {
  'work:created': { workId: string }
  'work:deleted': { workId: string }
  'work:updated': { workId: string }
  'work:notarized': { workId: string }
  'contract:signed': { contractId: string }
  'alert:new': { alertId: string }
}

type Listener<T> = (payload: T) => void

const listeners = new Map<string, Set<Listener<unknown>>>()

// Helper to avoid TS parsing >> as right-shift in generic casts
type CastFn<T> = Listener<T>

export function useGlobalEvents() {
  function emit<K extends keyof GlobalEventMap>(
    event: K,
    payload: GlobalEventMap[K],
  ): void {
    const set = listeners.get(event)
    if (!set) return
    for (const fn of [...set]) {
      try {
        ;((fn as CastFn<GlobalEventMap[K]>)(payload))
      } catch {
        // Ignore listener errors to avoid breaking the emitter
      }
    }
  }

  function on<K extends keyof GlobalEventMap>(
    event: K,
    fn: Listener<GlobalEventMap[K]>,
  ): () => void {
    if (!listeners.has(event)) {
      listeners.set(event, new Set())
    }
    listeners.get(event)!.add(fn as Listener<unknown>)
    return () => {
      listeners.get(event)?.delete(fn as Listener<unknown>)
    }
  }

  return { emit, on }
}
