<template>
  <div class="score-gauge">
    <div class="gauge-container">
      <svg viewBox="0 0 200 200" class="gauge-svg">
        <!-- Background arc -->
        <circle cx="100" cy="100" r="80" fill="none" stroke="var(--border)" stroke-width="16"
                stroke-dasharray="377" stroke-dashoffset="94.25" transform="rotate(135 100 100)" />
        <!-- Score arc -->
        <circle cx="100" cy="100" r="80" fill="none" :stroke="gaugeColor" stroke-width="16"
                :stroke-dasharray="arcLength" :stroke-dashoffset="arcOffset"
                transform="rotate(135 100 100)" style="transition: stroke-dashoffset 0.6s ease;" />
        <!-- Center text -->
        <text x="100" y="90" text-anchor="middle" fill="var(--fg)" font-size="36" font-weight="700"
              font-family="var(--font-display)">{{ score }}</text>
        <text x="100" y="115" text-anchor="middle" fill="var(--muted)" font-size="12">SCORE</text>
      </svg>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ score: number }>()

const ARC_LENGTH = 282.74 // 3/4 circle circumference (r=80)

const gaugeColor = computed(() => {
  if (props.score >= 90) return '#f59e0b' // gold
  if (props.score >= 75) return '#94a3b8' // silver
  if (props.score >= 55) return '#d97706' // bronze
  return '#64748b' // starter
})

const arcOffset = computed(() => {
  const ratio = Math.max(0, Math.min(1, props.score / 100))
  return ARC_LENGTH * (1 - ratio)
})
</script>

<style scoped>
.gauge-container { display: flex; justify-content: center; }
.gauge-svg { width: 200px; height: 200px; }
</style>
