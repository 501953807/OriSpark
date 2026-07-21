<template>
  <div class="notarization-strip card">
    <div class="strip-row">
      <!-- Notarization badge (left) -->
      <div class="notary-section">
        <NotarizationStatus :work="work" />
      </div>

      <!-- Quick action buttons (right) -->
      <div class="actions-section">
        <button v-if="!work.is_verified" class="strip-btn primary" @click="$emit('notarize')">
          🔒 快速存证
        </button>
        <button class="strip-btn" @click="$emit('scan')">
          🔍 扫描侵权
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import NotarizationStatus from './NotarizationStatus.vue'

defineProps<{
  work: {
    is_verified: boolean
    verified_date?: string | null
    sha256?: string | null
    custom_metadata?: Record<string, any> | null
  }
}>()

defineEmits<{
  notarize: []
  scan: []
}>()
</script>

<style scoped>
.notarization-strip { padding: 12px 16px; }
.strip-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.notary-section { flex: 1; }
.actions-section {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}
.strip-btn {
  padding: 4px 10px;
  font-size: 0.72rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--fg);
  cursor: pointer;
  font-weight: 600;
  transition: all 0.15s;
  white-space: nowrap;
}
.strip-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
}
.strip-btn.primary {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}
.strip-btn.primary:hover {
  opacity: 0.9;
  color: #fff;
}
</style>
