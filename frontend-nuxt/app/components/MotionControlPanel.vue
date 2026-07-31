<!-- app/components/MotionControlPanel.vue -->
<script setup lang="ts">
import { useMotionStore } from '@/stores/motion'
import { computed } from 'vue'

const motionStore = useMotionStore()

const levels = computed(() => [
  { id: 0, label: '关闭', desc: '无动画，保障性能' },
  { id: 1, label: '基础', desc: '过渡动效、按钮反馈' },
  { id: 2, label: '品牌沉浸', desc: '粒子背景、3D元素、蓝脉流动效应（推荐）' },
  { id: 3, label: '极致沉浸', desc: '全3D场景、高粒子密度、复杂物理效果' },
])

const toggleImmersive = () => {
  motionStore.toggleImmersive()
}

const setLevel = (levelId: number) => {
  motionStore.setImmersionLevel(levelId)
}
</script>

<template>
  <div class="motion-control-panel" v-if="motionStore.immersiveEnabled">
    <div class="panel-header">
      <span class="panel-title">动效强度</span>
    </div>

    <div class="level-options">
      <button
        v-for="level in levels"
        :key="level.id"
        :class="[
          'level-btn',
          { active: motionStore.immersionLevel === level.id }
        ]"
        @click="setLevel(level.id)"
      >
        <div class="level-label">{{ level.label }}</div>
        <div class="level-desc">{{ level.desc }}</div>
      </button>
    </div>

    <div class="status-indicator" style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #e5e7eb;">
      <div style="font-size: 0.875rem; color: #6b7280;">
        当前帧率: {{ motionStore.frameRate }} FPS |
        降级模式: {{ motionStore.isDegraded ? '开启' : '关闭' }}
      </div>
    </div>
  </div>

  <!-- Toggle开关（当关闭时显示） -->
  <div class="motion-toggle" v-else>
    <button
      class="toggle-button"
      @click="toggleImmersive"
      title="启用沉浸式动效"
    >
      🎨 启用动效
    </button>
  </div>
</template>

<style scoped>
.motion-control-panel {
  background: white;
  border-radius: 12px;
  padding: 1rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  max-width: 400px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.panel-title {
  font-family: 'Satoshi', sans-serif;
  font-weight: 600;
  font-size: 0.95rem;
  color: #1f2937;
}

.level-options {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
}

.level-btn {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 0.75rem 0.5rem;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.85rem;
}

.level-btn:hover {
  border-color: var(--brand-primary);
  background: rgba(14, 165, 233, 0.05);
}

.level-btn.active {
  background: linear-gradient(135deg, #0ea5e9, #3b82f6);
  color: white;
  border-color: var(--brand-primary);
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.3);
}

.level-label {
  font-weight: 600;
  font-size: 0.95rem;
  margin-bottom: 0.25rem;
}

.level-desc {
  font-size: 0.75rem;
  opacity: 0.8;
}

.motion-toggle {
  text-align: center;
  margin-top: 1rem;
}

.toggle-button {
  background: linear-gradient(135deg, #0ea5e9, #3b82f6);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.toggle-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.4);
}

/* 减速模式样式 */
@media (prefers-reduced-motion: reduce) {
  .motion-control-panel, .motion-toggle {
    opacity: 0.6;
    pointer-events: none;
  }
}
</style>
