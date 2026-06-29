<template>
  <div class="wizard-container">
    <div class="wizard-steps">
      <div v-for="(s, i) in steps" :key="i" class="wiz-step" :class="{ active: modelValue === i, done: modelValue > i }" @click="modelValue > i ? $emit('update:modelValue', i) : undefined">
        <span class="wiz-num">{{ modelValue > i ? '✓' : i + 1 }}</span>
        <span class="wiz-label">{{ s }}</span>
      </div>
    </div>
    <slot />
  </div>
</template>

<script setup lang="ts">
defineProps<{ steps: string[]; modelValue: number }>()
defineEmits<{ 'update:modelValue': [value: number] }>()
</script>

<style scoped>
.wizard-steps { display: flex; gap: 0; align-items: center; margin-bottom: 16px; }
.wiz-step { display: flex; align-items: center; gap: 8px; padding: 8px 16px 8px 8px; font-size: .82rem; color: var(--muted); cursor: default; }
.wiz-step.active { color: var(--accent); font-weight: 700; }
.wiz-step.done { color: var(--accent); cursor: pointer; }
.wiz-num { width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; border-radius: 50%; border: 2px solid var(--border); font-size: .78rem; font-weight: 700; }
.wiz-step.active .wiz-num { background: var(--accent); color: #fff; border-color: var(--accent); }
.wiz-step.done .wiz-num { background: oklch(56% 0.12 170 / 0.2); color: var(--accent); border-color: var(--accent); }
</style>
