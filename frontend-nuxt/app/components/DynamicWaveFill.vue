<!-- app/components/DynamicWaveFill.vue -->
<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref } from 'vue'

const waveContainer = ref<HTMLDivElement | null>(null)
let animationId: number | null = null

// SVG 波浪路径生成函数（基于正弦波，随时间平移）
const generateWavePath = (offset: number) => {
  const width = 400
  const height = 100
  const amplitude = 20
  const wavelength = 100

  let d = `M 0 ${height / 2 + offset * Math.sin(0)} `

  for (let x = 0; x <= width; x += 5) {
    const y = height / 2 +
              amplitude * Math.sin((x / wavelength) * Math.PI * 2 + offset) +
              (amplitude * 0.5) * Math.sin((x / wavelength * 0.5) * Math.PI * 2 + offset * 0.5)
    d += `L ${x} ${y} `
  }

  d += `L ${width} ${height} L 0 ${height} Z`
  return d
}

const animate = (timestamp: number) => {
  if (!waveContainer.value || !animationId) return

  const time = timestamp * 0.0003 // 缓慢移动速度
  const path = waveContainer.value.querySelector('path')

  if (path) {
    path.setAttribute('d', generateWavePath(time))
  }

  animationId = requestAnimationFrame(animate)
}

onMounted(() => {
  animationId = requestAnimationFrame(animate)
})

onBeforeUnmount(() => {
  if (animationId) cancelAnimationFrame(animationId)
}
</script>

<template>
  <div ref="waveContainer" class="wave-fill">
    <svg viewBox="0 0 400 100" preserveAspectRatio="none" class="wave-svg">
      <defs>
        <linearGradient id="waveGradient" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" style="stop-color:#0ea5e9; stop-opacity:0.3" />
          <stop offset="100%" style="stop-color:#0ea5e9; stop-opacity:0" />
        </linearGradient>
      </defs>
      <path fill="url(#waveGradient)" d="M 0 50 L 400 50 L 400 100 L 0 100 Z" />
    </svg>
  </div>
</template>

<style scoped>
.wave-fill {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 120px;
  z-index: -1;
  overflow: hidden;
}

.wave-svg {
  width: 100%;
  height: 100%;
}

@media (prefers-reduced-motion: reduce) {
  .wave-svg path {
    transition: none !important;
  }
}
</style>
