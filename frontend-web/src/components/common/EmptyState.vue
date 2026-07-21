<template>
  <div class="empty-state">
    <div class="empty-icon">{{ icon }}</div>
    <div class="empty-title">{{ title }}</div>
    <div v-if="description" class="empty-desc">{{ description }}</div>
    <div v-if="showAction && primaryAction" class="empty-actions">
      <button class="btn btn-primary" @click="primaryAction.onClick">{{ primaryAction.label }}</button>
      <button v-if="secondaryAction" class="btn btn-link" @click="secondaryAction.onClick">{{ secondaryAction.label }}</button>
    </div>
    <div v-if="tips && tips.length" class="empty-tips">
      <div v-for="(tip, i) in tips" :key="i" class="empty-tip">💡 {{ tip }}</div>
    </div>
    <slot />
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  icon?: string; title?: string; description?: string
  showAction?: boolean
  primaryAction?: { label: string; onClick: () => void }
  secondaryAction?: { label: string; onClick: () => void }
  tips?: string[]
}>(), {
  icon: '📭', title: '暂无内容', description: '', showAction: false,
})
</script>

<style scoped>
.empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 60px 20px; text-align: center; }
.empty-icon { font-size: 3rem; margin-bottom: 16px; opacity: 0.7; }
.empty-title { font-size: 1.1rem; font-weight: 600; color: var(--text-primary, #333); margin-bottom: 4px; }
.empty-desc { font-size: 0.88rem; color: var(--text-secondary, #666); margin: 4px 0 16px; max-width: 400px; }
.empty-actions { display: flex; gap: 12px; align-items: center; margin-bottom: 16px; }
.empty-tips { text-align: left; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 12px 16px; margin-top: 8px; max-width: 420px; }
.empty-tip { font-size: 0.82rem; color: var(--text-secondary); padding: 4px 0; }
.btn { padding: 8px 20px; border-radius: 8px; font-size: 0.88rem; cursor: pointer; border: none; font-family: inherit; }
.btn-primary { background: var(--accent, #5b5fe3); color: #fff; }
.btn-link { background: none; border: none; color: var(--accent); cursor: pointer; font-size: 0.84rem; text-decoration: underline; }
</style>
