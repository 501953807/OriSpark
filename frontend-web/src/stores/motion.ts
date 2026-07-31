// src/stores/motion.ts
import { defineStore } from 'pinia'
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'

export const useMotionStore = defineStore('motion', {
  state() {
    return {
      // User preset: 0=No animation, 1=Basic, 2=Brand immersion, 3=Extreme immersion
      immersionLevel: 2 as number,

      // Auto-detected performance degradation flag
      isDegraded: false as boolean,
      frameRate: 0 as number,

      // Manual control toggle
      immersiveEnabled: true as boolean,

      // Reduced-motion preference (set on mount)
      reducedMotion: false as boolean,

      // Particle count (dynamic)
      particleCount: 1000 as number
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
      this.updateParticleCount()
      // Save to localStorage
      try {
        localStorage.setItem('immersionLevel', this.immersionLevel.toString())
      } catch (e) {
        // Ignore storage errors (e.g., in private mode)
      }
    },

    toggleImmersive(): void {
      this.immersiveEnabled = !this.immersiveEnabled
      try {
        localStorage.setItem('immersiveEnabled', this.immersiveEnabled.toString())
      } catch (e) {}
    },

    updateParticleCount(): void {
      this.particleCount = this.particleDensity
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

// Helper to initialize reduced-motion preference on mount
export function initMotionPreferences(store: ReturnType<typeof useMotionStore>) {
  const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  store.reducedMotion = mediaQuery.matches

  const handler = (e: MatchMediaEvent) => {
    store.reducedMotion = e.matches
  }
  mediaQuery.addEventListener('change', handler)

  return () => {
    mediaQuery.removeEventListener('change', handler)
  }
}

// Store initialization with SSR safety
export function initMotionStore() {
  const store = useMotionStore()

  // Restore from localStorage only in browser environment
  if (typeof window !== 'undefined') {
    try {
      const savedLevel = localStorage.getItem('immersionLevel')
      if (savedLevel !== null) {
        store.setImmersionLevel(parseInt(savedLevel, 10))
      }

      const savedImmersive = localStorage.getItem('immersiveEnabled')
      if (savedImmersive !== null) {
        store.immersiveEnabled = savedImmersive === 'true'
      }
    } catch (e) {
      # failed to restore motion settings
    }

    // Setup reduced-motion listener
    const cleanup = initMotionPreferences(store)
    onBeforeUnmount(cleanup)

    // Start monitoring if animations are enabled
    if (store.shouldAnimate) {
      store.monitorFrameRate()
    }
  }
}
