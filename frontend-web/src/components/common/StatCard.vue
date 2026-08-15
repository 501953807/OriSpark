<template>
  <div class="stat-card" :class="{ clickable: !!to }" @click="to && $router.push(to)">
    <div class="stat-icon-circle" :style="{ background: gradientStyle }">
      <span class="stat-icon">{{ icon }}</span>
    </div>
    <div class="stat-info">
      <div class="stat-label">{{ label }}</div>
      <div class="stat-value">{{ value }}</div>
      <div v-if="trend != null" class="stat-trend" :class="trend > 0 ? 'up' : 'down'">
        <span class="trend-arrow">{{ trend > 0 ? '↑' : '↓' }}</span>
        <span>{{ Math.abs(trend) }}%</span>
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

const gradientStyle = computed(() => {
  const colors: Record<string, string[]> = {
    green: ['var(--success)', 'oklch(68% 0.11 170)'],
    orange: ['var(--warning)', 'oklch(72% 0.16 65)'],
    purple: ['var(--accent)', 'oklch(68% 0.14 290)'],
    blue: ['#6366f1', 'oklch(68% 0.12 255)'],
    default: ['#5585FF', '#2A52B0'],
  }
  const c = colors[props.color || 'default']
  return `linear-gradient(135deg, ${c[0]}, ${c[1]})`
})
</script>

<style scoped>
.stat-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--m-radius-lg);
  padding: 20px;
  display: flex;
  align-items: flex-start;
  gap: 16px;
  transition: all 0.3s ease;
}
.stat-card.clickable {
  cursor: pointer;
}
.stat-card.clickable:hover {
  box-shadow: 0 8px 32px var(--shadow-lg);
  transform: translateY(-2px);
}
.stat-icon-circle {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
  flex-shrink: 0;
  box-shadow: 0 4px 12px var(--shadow);
}
.stat-label {
  font-size: 0.78rem;
  color: var(--muted);
  margin-bottom: 4px;
}
.stat-value {
  font-size: 1.6rem;
  font-weight: 700;
  font-family: Inter;
  color: var(--fg);
  line-height: 1.2;
}
.stat-trend {
  font-size: 0.75rem;
  font-weight: 600;
  margin-top: 4px;
  display: flex;
  align-items: center;
  gap: 2px;
}
.stat-trend.up { color: var(--success); }
.stat-trend.down { color: var(--danger); }
.trend-arrow { font-size: 0.85rem; }
</style>
