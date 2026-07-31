<!-- src/components/MotionControlPanel.vue -->
<script setup lang="ts">
import { ref, computed } from 'vue'
import { useMotionStore } from '@/stores/motion'

const motionStore = useMotionStore()
const isExpanded = ref(false)

const levels = [
  { value: 0, label: '关闭', desc: '无动画', icon: '⊘' },
  { value: 1, label: '基础', desc: '过渡动画', icon: '◐' },
  { value: 2, label: '品牌', desc: '沉浸体验', icon: '◉' },
  { value: 3, label: '极致', desc: '全量特效', icon: '✦' }
] as const

const currentLevel = computed(() => motionStore.immersionLevel)

const setLevel = (level: number) => {
  motionStore.setImmersionLevel(level)
}

const toggleImmersive = () => {
  motionStore.toggleImmersive()
}

const isReducedMotion = computed(() => motionStore.reducedMotion)
</script>

<template>
  <div class="motion-panel" :class="{ 'reduced-motion': isReducedMotion }">
    <div class="panel-header" @click="isExpanded = !isExpanded">
      <span class="panel-title">🎨 动效控制</span>
      <button class="panel-toggle" aria-label="切换面板" @click.stop="isExpanded = !isExpanded">
        {{ isExpanded ? '▲' : '▼' }}
      </button>
    </div>

    <div v-if="isExpanded" class="panel-content">
      <!-- Immersion Level Selector -->
      <div class="control-section">
        <label class="section-label">沉浸等级</label>
        <div class="level-buttons">
          <button
            v-for="lvl in levels"
            :key="lvl.value"
            :class="['level-btn', { active: currentLevel === lvl.value }]"
            @click="setLevel(lvl.value)"
            :title="lvl.desc"
          >
            <span class="level-icon">{{ lvl.icon }}</span>
            <span class="level-label">{{ lvl.label }}</span>
          </button>
        </div>
      </div>

      <!-- Toggle Button -->
      <div class="control-section">
        <label class="section-label">沉浸式模式</label>
        <button
          :class="['toggle-btn', { on: motionStore.immersiveEnabled }]"
          @click="toggleImmersive"
        >
          <span class="toggle-track">
            <span class="toggle-thumb"></span>
          </span>
          <span>{{ motionStore.immersiveEnabled ? '已开启' : '已关闭' }}</span>
        </button>
      </div>

      <!-- Status Display -->
      <div class="status-section">
        <span class="status-label">系统状态:</span>
        <span :class="['status-badge', motionStore.isDegraded ? 'degraded' : 'normal']">
          {{ motionStore.isDegraded ? '性能降级' : '正常' }}
        </span>
        <span v-if="isReducedMotion" class="status-badge reduced">
          省动模式
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.motion-panel {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 9999;
  background: var(--surface, #ffffff);
  border: 1px solid var(--border, #e5e7eb);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  min-width: 200px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid var(--border, #e5e7eb);
}

.panel-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--fg, #1f2937);
}

.panel-toggle {
  background: none;
  border: none;
  font-size: 1rem;
  cursor: pointer;
  color: var(--muted, #6b7280);
}

.panel-content {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.control-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--muted, #6b7280);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.level-buttons {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
}

.level-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 4px;
  border: 2px solid var(--border, #e5e7eb);
  border-radius: 8px;
  background: var(--surface, #ffffff);
  cursor: pointer;
  transition: all 0.2s ease;
}

.level-btn:hover {
  border-color: var(--accent, #0ea5e9);
  transform: translateY(-2px);
}

.level-btn.active {
  border-color: var(--accent, #0ea5e9);
  background: oklch(from var(--accent) l c h / 0.1);
}

.level-icon {
  font-size: 1.2rem;
}

.level-label {
  font-size: 0.7rem;
  font-weight: 500;
  color: var(--fg, #1f2937);
}

.toggle-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border: 1px solid var(--border, #e5e7eb);
  border-radius: 8px;
  background: var(--surface, #ffffff);
  cursor: pointer;
  transition: all 0.2s ease;
}

.toggle-btn:hover {
  background: var(--hover-bg, #f9fafb);
}

.toggle-track {
  width: 36px;
  height: 20px;
  background: var(--border, #d1d5db);
  border-radius: 10px;
  position: relative;
  transition: background 0.2s ease;
}

.toggle-thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 16px;
  height: 16px;
  background: white;
  border-radius: 50%;
  transition: transform 0.2s ease;
}

.toggle-btn.on .toggle-track {
  background: var(--accent, #0ea5e9);
}

.toggle-btn.on .toggle-thumb {
  transform: translateX(16px);
}

.status-section {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.status-label {
  font-size: 0.8rem;
  color: var(--muted, #6b7280);
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.status-badge.normal {
  background: #10b98120;
  color: #10b981;
}

.status-badge.degraded {
  background: #f59e0b20;
  color: #f59e0b;
}

.status-badge.reduced {
  background: #6b728020;
  color: #6b7280;
}

/* Dark theme adjustments */
.dark .motion-panel {
  background: var(--surface, #1f2937);
  border-color: var(--border, #374151);
}

.dark .level-btn,
.dark .toggle-btn {
  background: var(--surface, #1f2937);
  border-color: var(--border, #374151);
  color: var(--fg, #f9fafb);
}

.dark .level-btn:hover,
.dark .toggle-btn:hover {
  border-color: var(--accent, #0ea5e9);
}

/* Reduced motion preference */
.reduced-motion .panel-content {
  animation: none !important;
}

.reduced-motion .level-btn {
  transition: none !important;
}
</style>
