<template>
  <div
    v-if="visible"
    class="fps-monitor"
    :class="{ collapsed: isCollapsed }"
  >
    <button class="fps-toggle" @click="isCollapsed = !isCollapsed" aria-label="切换监控面板">
      {{ isCollapsed ? '📊' : '✕' }}
    </button>

    <template v-if="!isCollapsed">
      <div class="fps-row">
        <span class="fps-label">FPS</span>
        <span class="fps-value" :class="fpsClass">{{ fps }}</span>
      </div>
      <div class="fps-row">
        <span class="fps-label">Level</span>
        <span class="fps-value level">{{ immersionLevel }}</span>
      </div>
      <div v-if="prefersReducedMotion" class="fps-row reduced">
        <span class="fps-label">系统</span>
        <span class="fps-value reduced-label"> reduced-motion</span>
      </div>
      <div class="level-buttons">
        <button
          v-for="l in [0, 1, 2, 3]"
          :key="l"
          :class="['level-btn', { active: immersionLevel === l }]"
          @click="setLevel(l as ImmersionLevel)"
        >
          {{ l }}
        </button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useMotionStore, type ImmersionLevel } from '@/stores/useMotionStore'

const store = useMotionStore()
const isCollapsed = ref(false)

const visible = computed(() => {
  if (store.prefersReducedMotion) return false
  return store.effectiveLevel >= 1
})

const fps = computed(() => store.fps)
const immersionLevel = computed(() => store.immersionLevel)
const prefersReducedMotion = computed(() => store.prefersReducedMotion)

const fpsClass = computed(() => {
  if (fps.value >= 50) return 'fps-good'
  if (fps.value >= 30) return 'fps-warn'
  return 'fps-bad'
})

function setLevel(level: ImmersionLevel) {
  store.setLevel(level)
}
</script>

<style scoped>
.fps-monitor {
  position: fixed;
  bottom: 16px;
  right: 16px;
  z-index: 999;
  background: rgba(15,23,42,0.85);
  color: #e2e8f0;
  border: 1px solid #334155;
  border-radius: var(--m-radius-md, 12px);
  padding: 10px 12px;
  font-size: 0.78rem;
  font-family: 'SF Mono', 'Fira Code', monospace;
  min-width: 130px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.3);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.fps-monitor.collapsed {
  padding: 6px 8px;
  min-width: 36px;
}

.fps-toggle {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 1px solid #334155;
  background: #1e293b;
  color: #f1f5f9;
  cursor: pointer;
  font-size: 0.7rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.fps-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.fps-label {
  color: #cbd5e1;
  font-size: 0.72rem;
}

.fps-value {
  font-weight: 700;
  font-size: 0.95rem;
}

.fps-value.level {
  color: rgba(59,130,246,0.8);
}

.fps-value.fps-good { color: #22c55e; }
.fps-value.fps-warn { color: #f59e0b; }
.fps-value.fps-bad { color: #ef4444; }

.fps-row.reduced {
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
}

.reduced-label {
  color: #f59e0b;
  font-size: 0.7rem;
}

.level-buttons {
  display: flex;
  gap: 4px;
}

.level-btn {
  flex: 1;
  padding: 4px 0;
  border: 1px solid #334155;
  border-radius: var(--m-radius-xs, 6px);
  background: transparent;
  color: rgba(99,102,241, 0.06);
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 600;
  transition: all 0.15s;
}

.level-btn:hover {
  border-color: rgba(var(--m-primary-rgb, 79, 70, 229), 0.5);
  color: var(--m-primary, #4F46E5);
}

.level-btn.active {
  background: rgba(var(--m-primary-rgb, 79, 70, 229), 0.2);
  border-color: rgba(var(--m-primary-rgb, 79, 70, 229), 0.6);
  color: var(--m-primary, #4F46E5);
}
</style>
