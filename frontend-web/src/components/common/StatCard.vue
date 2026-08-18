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
    green: 'rgba(22, 163, 74, 0.12)',
    orange: 'rgba(217, 119, 6, 0.12)',
    purple: 'rgba(79, 70, 229, 0.12)',
    blue: 'rgba(2, 132, 199, 0.12)',
  }
  return map[props.color || 'green']
})

const gradientStyle = computed(() => {
  const colors: Record<string, string> = {
    green: '#16A34A',
    orange: '#D97706',
    purple: '#4F46E5',
    blue: '#0284C7',
    default: '#4F46E5',
  }
  return colors[props.color || 'default']
})
</script>

<style scoped>
.stat-card {
  background: var(--surface);
  border: none;
  border-radius: var(--m-radius-lg);
  padding: 20px;
  display: flex;
  align-items: flex-start;
  gap: 16px;
  box-shadow: var(--m-shadow-xs);
  transition: all 0.3s ease;
}
.stat-card.clickable {
  cursor: pointer;
}
.stat-card.clickable:hover {
  box-shadow: var(--m-shadow-lg);
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
  box-shadow: 0 4px 12px rgba(15,23,42,0.12);
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
