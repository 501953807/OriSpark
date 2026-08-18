<template>
  <div class="rating-badge">
    <span :class="['badge', `badge-${level}`]">
      <span class="badge-icon">{{ icon }}</span>
      <span class="badge-label">{{ label }}</span>
    </span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ level: string }>()

const icon = computed(() => {
  const map: Record<string, string> = { gold: '🥇', silver: '🥈', bronze: '🥉', starter: '⭐' }
  return map[props.level] || '⭐'
})

const label = computed(() => {
  const map: Record<string, string> = { gold: 'Gold', silver: 'Silver', bronze: 'Bronze', starter: 'Starter' }
  return map[props.level] || 'Starter'
})
</script>

<style scoped>
.badge {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 4px 12px; border-radius: var(--m-radius-lg, 16px); font-size: 0.82rem; font-weight: 600;
}

.badge-icon { font-size: 1rem; }

.badge-gold { background: rgba(22,163,74, 0.06); color: #fff; }
.badge-silver { background: rgba(99,102,241, 0.06); color: #fff; }
.badge-bronze { background: rgba(234,88,12, 0.06); color: #fff; }
.badge-starter { background: var(--border); color: var(--fg); }
</style>
