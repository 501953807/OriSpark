// src/stores/motion.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useMotionStore = defineStore('motion', {
  state() {
    return {
      immersionLevel: 2 as number,
      isDegraded: false as boolean,
      frameRate: 0 as number,
      immersiveEnabled: true as boolean,
      reducedMotion: false as boolean,
      particleCount: 1000 as number,
    }
  },

  getters: {
    shouldAnimate(): boolean {
      if (this.reducedMotion) return false
      if (!this.immersiveEnabled) return this.immersionLevel === 1
      return this.immersionLevel >= 1
    },

    animationSpeedFactor(): number {
      if (this.frameRate < 30 && this.isDegraded) return 0.5
      if (this.frameRate < 45) return 0.75
      return 1
    },

    particleDensity(): number {
      switch (this.immersionLevel) {
        case 0: return 0
        case 1: return 300
        case 2: return 1000
        case 3: return 2000
        default: return 1000
      }
    }
  },

  actions: {
    setImmersionLevel(level: number): void {
      this.immersionLevel = Math.max(0, Math.min(3, level))
      this.particleCount = this.particleDensity
      try {
        localStorage.setItem('immersionLevel', this.immersionLevel.toString())
      } catch { /* ignore */ }
    },

    toggleImmersive(): void {
      this.immersiveEnabled = !this.immersiveEnabled
      try {
        localStorage.setItem('immersiveEnabled', this.immersiveEnabled.toString())
      } catch { /* ignore */ }
    },

    monitorFrameRate(): void {
      if (!this.shouldAnimate || this.immersionLevel === 0) return

      let lastTime = performance.now()
      let frameCount = 0

      const check = () => {
        frameCount++
        const now = performance.now()
        if (now - lastTime >= 1000) {
          this.frameRate = Math.round(frameCount * 1000 / (now - lastTime))
          frameCount = 0
          lastTime = now
          if (this.frameRate < 45 && !this.isDegraded) {
            this.isDegraded = true
            this.setImmersionLevel(Math.max(1, this.immersionLevel - 1))
          } else if (this.frameRate >= 50 && this.isDegraded) {
            this.isDegraded = false
          }
        }
        if (this.shouldAnimate) {
          requestAnimationFrame(check)
        }
      }
      requestAnimationFrame(check)
    }
  }
})

export function initMotionStore() {
  const store = useMotionStore()
  if (typeof window === 'undefined') return

  try {
    const savedLevel = localStorage.getItem('immersionLevel')
    if (savedLevel !== null) {
      store.setImmersionLevel(parseInt(savedLevel, 10))
    }
    const savedImmersive = localStorage.getItem('immersiveEnabled')
    if (savedImmersive !== null) {
      store.immersiveEnabled = savedImmersive === 'true'
    }
  } catch { /* ignore */ }

  const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
  store.reducedMotion = mq.matches
  const onMotionChange = (e: MediaQueryListEvent) => { store.reducedMotion = e.matches }
  mq.addEventListener('change', onMotionChange)

  // Expose cleanup function for the app bootstrap component
  ;(window as any).__motionCleanup = () => {
    mq.removeEventListener('change', onMotionChange)
  }

  if (store.shouldAnimate) {
    store.monitorFrameRate()
  }
}
