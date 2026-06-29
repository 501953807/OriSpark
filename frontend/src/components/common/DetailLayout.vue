<template>
  <div class="detail-layout">
    <!-- Top bar: back button + actions -->
    <div class="detail-topbar">
      <button class="btn-back" @click="$emit('back')">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M11 2L5 8l6 6" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>
        返回列表
      </button>
      <slot name="actions" />
    </div>

    <!-- Body: preview (40%) + info panel (60%) -->
    <div class="detail-body">
      <div class="detail-preview">
        <slot name="preview" />
      </div>
      <div class="detail-panel">
        <slot />
      </div>
    </div>

    <!-- Bottom CTA bar -->
    <div v-if="$slots.footer" class="detail-footer">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup lang="ts">
defineEmits<{ back: [] }>()
</script>

<style scoped>
.detail-layout { display: flex; flex-direction: column; gap: 16px; }
.detail-topbar { display: flex; justify-content: space-between; align-items: center; }
.detail-body { display: flex; gap: 24px; flex-wrap: wrap; }
.detail-preview { flex: 0 0 40%; min-width: 280px; }
.detail-panel { flex: 1; min-width: 300px; }
.detail-footer { display: flex; gap: 12px; justify-content: flex-end; padding-top: 16px; border-top: 1px solid var(--border); }

.btn-back { display: flex; align-items: center; gap: 6px; background: none; border: none; color: var(--accent); cursor: pointer; font-size: .88rem; font-family: inherit; padding: 6px 10px; border-radius: 6px; transition: background .15s; }
.btn-back:hover { background: oklch(56% 0.12 170 / 0.06); }
.btn-back svg { width: 16px; height: 16px; }
</style>
