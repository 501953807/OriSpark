<template>
  <div
    ref="cardRef"
    class="motion-card"
    :class="{
      'card-level-1': effectiveLevel >= 1,
      'card-level-2': effectiveLevel >= 2,
      'card-level-3': effectiveLevel >= 3,
      'reduced-motion': prefersReducedMotion,
    }"
    @mouseenter="onEnter"
    @mouseleave="onLeave"
  >
    <canvas
      v-if="effectiveLevel >= 3 && particlesEnabled"
      ref="canvasRef"
      class="particle-canvas"
    />
    <slot />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useMotionStore, type ImmersionLevel } from '@/stores/useMotionStore'

interface Props {
  /** 粒子数量，仅 Level 3 生效，默认 16 */
  particleCount?: number
}

const props = withDefaults(defineProps<Props>(), {
  particleCount: 16,
})

const store = useMotionStore()
const cardRef = ref<HTMLElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
const isHovered = ref(false)

const effectiveLevel = computed<ImmersionLevel>(() => store.effectiveLevel)
const prefersReducedMotion = computed(() => store.prefersReducedMotion)
const particlesEnabled = computed(() => store.particlesEnabled)

// Particle system (canvas overlay)
type Particle = {
  x: number
  y: number
  vx: number
  vy: number
  life: number
  maxLife: number
  size: number
}

const particles = ref<Particle[]>([])
let animFrameId: number | null = null
let canvasCtx: CanvasRenderingContext2D | null = null

function spawnParticles(count: number) {
  const el = cardRef.value
  if (!el) return
  const rect = el.getBoundingClientRect()
  const newP: Particle[] = []
  for (let i = 0; i < count; i++) {
    newP.push({
      x: rect.width / 2 + (Math.random() - 0.5) * rect.width * 0.6,
      y: rect.height / 2 + (Math.random() - 0.5) * rect.height * 0.6,
      vx: (Math.random() - 0.5) * 2,
      vy: -Math.random() * 2 - 0.5,
      life: 1,
      maxLife: 0.6 + Math.random() * 0.4,
      size: 2 + Math.random() * 3,
    })
  }
  particles.value = [...particles.value, ...newP]
}

function tickParticles() {
  if (!canvasCtx || !canvasRef.value) return
  const { width, height } = canvasRef.value
  canvasCtx.clearRect(0, 0, width, height)

  particles.value = particles.value.filter(p => p.life > 0)
  for (const p of particles.value) {
    p.x += p.vx
    p.y += p.vy
    p.vy -= 0.02 // slight upward drift
    p.life -= 0.012
    canvasCtx!.beginPath()
    canvasCtx!.arc(p.x, p.y, p.size * p.life, 0, Math.PI * 2)
    canvasCtx!.fillStyle = `rgba(14, 165, 233, ${p.life * 0.5})`
    canvasCtx!.fill()
  }

  if (particles.value.length > 0 && isHovered.value) {
    animFrameId = requestAnimationFrame(tickParticles)
  }
}

function startParticles() {
  if (!canvasRef.value) return
  const canvas = canvasRef.value
  canvas.width = canvas.parentElement?.offsetWidth ?? 300
  canvas.height = canvas.parentElement?.offsetHeight ?? 200
  canvasCtx = canvas.getContext('2d')
  spawnParticles(props.particleCount)
  animFrameId = requestAnimationFrame(tickParticles)
}

function stopParticles() {
  if (animFrameId !== null) {
    cancelAnimationFrame(animFrameId)
    animFrameId = null
  }
  particles.value = []
  if (canvasCtx) {
    canvasCtx.clearRect(0, 0, canvasRef.value?.width ?? 0, canvasRef.value?.height ?? 0)
  }
}

function onEnter() {
  if (prefersReducedMotion.value) return
  isHovered.value = true
  if (effectiveLevel.value >= 3 && particlesEnabled.value) {
    startParticles()
  }
}

function onLeave() {
  isHovered.value = false
  stopParticles()
}

onMounted(() => {
  // Resize observer for canvas
  const ro = new ResizeObserver(() => {
    if (canvasRef.value && cardRef.value) {
      canvasRef.value.width = cardRef.value.offsetWidth
      canvasRef.value.height = cardRef.value.offsetHeight
    }
  })
  if (cardRef.value) ro.observe(cardRef.value)
  // eslint-disable-next-line @typescript-eslint/no-floating-promises
  onUnmounted(() => ro.disconnect())
})

onUnmounted(() => {
  stopParticles()
})
</script>

<style scoped>
.motion-card {
  position: relative;
  overflow: hidden;
  border-radius: var(--radius, 12px);
  transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
}

/* Level 1+: hover shadow + slight scale */
.card-level-1:not(.reduced-motion):hover {
  transform: translateY(-2px) scale(1.01);
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
}

/* Level 2+: brand border glow */
.card-level-2:not(.reduced-motion):hover {
  border: 1px solid rgba(14, 165, 233, 0.45);
  box-shadow: 0 0 16px rgba(14, 165, 233, 0.2), 0 8px 24px oklch(0 0 0 / 0.1);
}

/* Reduced motion: no transforms */
.reduced-motion {
  transition: none !important;
}

.particle-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 2;
}
</style>
