<template>
  <div class="stat-card" :class="{ clickable: !!to }" @click="to && $router.push(to)">
    <div class="stat-icon" :style="{ background: bgColor }">{{ icon }}</div>
    <div class="stat-info">
      <div class="stat-label">{{ label }}</div>
      <div class="stat-value">{{ value }}</div>
      <div v-if="trend" class="stat-trend" :class="trend > 0 ? 'up' : 'down'">
        {{ trend > 0 ? '↑' : '↓' }} {{ Math.abs(trend) }}%
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  icon: string
  label: string
  value: string | number
  trend?: number
  to?: string
  color?: string
}>()

const bgColor = computed(() => {
  const map: Record<string, string> = {
    green: 'oklch(56% 0.12 170 / 0.12)',
    orange: 'oklch(62% 0.18 55 / 0.12)',
    purple: 'oklch(58% 0.16 280 / 0.12)',
    blue: 'oklch(58% 0.14 245 / 0.12)',
  }
  return map[props.color || 'green']
})
</script>

<style scoped>
.stat-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.3s ease;
}
.stat-card.clickable {
  cursor: pointer;
}
.stat-card.clickable:hover {
  box-shadow: 0 8px 32px oklch(0 0 0 / 0.07);
  transform: translateY(-2px);
}
.stat-icon {
  width: 48px; height: 48px;
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
  flex-shrink: 0;
}
.stat-label { font-size: 0.78rem; color: var(--muted); }
.stat-value { font-size: 1.5rem; font-weight: 700; font-family: var(--font-display); }
.stat-trend { font-size: 0.75rem; font-weight: 600; margin-top: 2px; }
.stat-trend.up { color: var(--green); }
.stat-trend.down { color: #e53e3e; }
</style>
