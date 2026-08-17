<!-- app/components/StatCounter.vue -->
<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'

const props = defineProps<{
  value: number
  label?: string
  duration?: number
  suffix?: string
}>()

const valueEl = ref<HTMLSpanElement | null>(null)
let animationId: number | null = null

const animateValue = (start: number, end: number, duration: number) => {
  const startTime = performance.now()

  const update = (currentTime: number) => {
    const elapsed = currentTime - startTime
    const progress = Math.min(elapsed / duration, 1)
    const current = start + (end - start) * easeOutExpo(progress)

    if (valueEl.value) {
      valueEl.value.textContent = Math.round(current).toLocaleString()
    }

    if (progress < 1) {
      animationId = requestAnimationFrame(update)
    } else if (valueEl.value) {
      valueEl.value.textContent = end.toLocaleString()
    }
  }

  animationId = requestAnimationFrame(update)
}

const easeOutExpo = (t: number) => t === 1 ? 1 : 1 - Math.pow(2, -10 * t)

onMounted(() => {
  animateValue(0, props.value, props.duration || 2000)
})

onBeforeUnmount(() => {
  if (animationId) cancelAnimationFrame(animationId)
})

// 响应式更新值
watch(() => props.value, (newVal) => {
  if (animationId) cancelAnimationFrame(animationId)
  animateValue(0, newVal, props.duration || 2000)
})
</script>

<template>
  <div class="stat-card">
    <div class="stat-label">{{ label || '' }}</div>
    <div class="stat-value">
      <span ref="valueEl">0</span>{{ suffix }}
    </div>
  </div>
</template>

<style scoped>
.stat-card {
  background: white;
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  text-align: center;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(140, 87, 255, 0.15);
}

.stat-label {
  font-size: 0.875rem;
  color: var(--m-grey-500);
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.stat-value {
  font-size: 2.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, var(--m-primary), var(--m-primary-dark));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* 淡入动画 */
.fade-in {
  animation: fadeInUp 0.8s ease-out forwards;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 减速模式时简化动画 */
@media (prefers-reduced-motion: reduce) {
  .stat-card {
    transition: none !important;
  }
}
</style>
