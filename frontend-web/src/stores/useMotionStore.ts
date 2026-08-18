import { defineStore } from 'pinia'
import { ref, computed, onMounted, onUnmounted } from 'vue'

export type ImmersionLevel = 0 | 1 | 2 | 3

export const useMotionStore = defineStore('motion', () => {
  // Core state
  const immersionLevel = ref<ImmersionLevel>(2)
  const fps = ref(60)
  const frameCount = ref(0)
  let lastTime = performance.now()
  let rafId: number | null = null

  // Reduced motion from system preference
  const prefersReducedMotion = ref(false)

  // Auto-adjust flags
  const particlesEnabled = ref(true)
  const backgroundAnimations = ref(true)
  const scrollTriggers = ref(true)

  // Compute effective level (system reduced-motion overrides manual)
  const effectiveLevel = computed<ImmersionLevel>(() => {
    if (prefersReducedMotion.value) return 0
    return immersionLevel.value
  })

  // Brand colors
  const brandRippleColor = 'rgba(79, 70, 229, 0.3)'
  const brandRippleDuration = 600

  // Frame rate monitoring
  function tick() {
    const now = performance.now()
    frameCount.value++
    if (now - lastTime >= 1000) {
      fps.value = frameCount.value
      frameCount.value = 0
      lastTime = now
      autoAdjust()
    }
    rafId = requestAnimationFrame(tick)
  }

  function autoAdjust() {
    if (fps.value < 20) {
      particlesEnabled.value = false
      backgroundAnimations.value = false
      scrollTriggers.value = false
    } else if (fps.value < 30) {
      particlesEnabled.value = false
      backgroundAnimations.value = true
      scrollTriggers.value = false
    } else if (fps.value < 45) {
      particlesEnabled.value = false
      backgroundAnimations.value = true
      scrollTriggers.value = true
    } else {
      particlesEnabled.value = true
      backgroundAnimations.value = true
      scrollTriggers.value = true
    }
  }

  // Lifecycle
  onMounted(() => {
    if (typeof window !== 'undefined') {
      const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
      prefersReducedMotion.value = mq.matches
      mq.addEventListener?.('change', (e) => {
        prefersReducedMotion.value = (e as MediaQueryListEvent).matches
      })
    }
    rafId = requestAnimationFrame(tick)
  })

  onUnmounted(() => {
    if (rafId !== null) cancelAnimationFrame(rafId)
  })

  function setLevel(level: ImmersionLevel) {
    immersionLevel.value = level
    autoAdjust()
  }

  return {
    immersionLevel,
    effectiveLevel,
    fps,
    prefersReducedMotion,
    particlesEnabled,
    backgroundAnimations,
    scrollTriggers,
    brandRippleColor,
    brandRippleDuration,
    setLevel,
    autoAdjust,
  }
})
