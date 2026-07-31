// app/stores/motion.ts
import { defineStore } from 'pinia'
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'

export const useMotionStore = defineStore('motion', {
  state() {
    return {
      // 用户主动设置：0=无动效, 1=基础动效, 2=品牌沉浸, 3=极致沉浸
      immersionLevel: 2 as number,

      // 系统自动检测的性能降级标志
      isDegraded: false as boolean,
      frameRate: 0 as number,

      // 手动控制开关
      immersiveEnabled: true as boolean,

      // 粒子数量（根据 immersionLevel 动态计算）
      particleCount: 1000 as number,

      // reduced-motion preference（客户端初始化）
      reducedMotion: false as boolean
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
      // 仅在客户端保存 localStorage
      if (typeof window !== 'undefined') {
        localStorage.setItem('immersionLevel', this.immersionLevel.toString())
      }
    },

    toggleImmersive(): void {
      this.immersiveEnabled = !this.immersiveEnabled
      if (typeof window !== 'undefined') {
        localStorage.setItem('immersiveEnabled', this.immersiveEnabled.toString())
      }
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

// 在组件挂载时初始化 reduced-motion 偏好
export function initMotionPreferences(store: ReturnType<typeof useMotionStore>) {
  if (typeof window !== 'undefined') {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    store.reducedMotion = mediaQuery.matches

    // 监听变化
    const handler = (e: MatchMediaEvent) => {
      store.reducedMotion = e.matches
    }
    mediaQuery.addEventListener('change', handler)

    return () => {
      mediaQuery.removeEventListener('change', handler)
    }
  }
  return () => {}
}

// Nuxt 专用初始化函数（用于插件）
export function initMotionStore() {
  const store = useMotionStore()

  // 从 localStorage 恢复设置（仅在客户端）
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
  }

  // 初始化 reduced-motion 偏好
  const cleanup = initMotionPreferences(store)
  onBeforeUnmount(cleanup)

  // 启动帧率监控（如果启用了动效）
  if (store.shouldAnimate) {
    store.monitorFrameRate()
  }
}
