<template>
  <div class="notarization-status">
    <!-- Layer 1: Visual badge -->
    <div
      class="status-badge"
      :class="{ expanded }"
      @click="toggleExpand"
    >
      <span v-if="work.is_verified" class="status-verified">
        已存证 <IconCheck />
        <span class="status-date">{{ work.verified_date?.slice(0, 10) || '' }}</span>
      </span>
      <span v-else class="status-unverified">
        未存证 <IconWarning />
      </span>
    </div>

    <!-- Layer 2: Hover tooltip -->
    <div v-if="work.is_verified" class="tooltip">
      数字指纹已锚定到区块链
    </div>

    <!-- Layer 3: Click to expand -->
    <div v-if="expanded" class="expand-panel animate-scale-in">
      <div class="expand-row">
        <span class="expand-label">SHA-256</span>
        <code class="expand-value mono">{{ work.sha256 || '—' }}</code>
      </div>
      <div class="expand-row">
        <span class="expand-label">平台</span>
        <span class="expand-value">版权家</span>
      </div>
      <div class="expand-row">
        <span class="expand-label">交易哈希</span>
        <code class="expand-value mono">{{ work.custom_metadata?.tx_hash || '—' }}</code>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  work: {
    is_verified: boolean
    verified_date?: string | null
    sha256?: string | null
    custom_metadata?: Record<string, any> | null
  }
}>()

const expanded = ref(false)

function toggleExpand() {
  expanded.value = !expanded.value
}
</script>

<style scoped>
.notarization-status {
  position: relative;
  display: inline-block;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 100px;
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
  user-select: none;
}

.status-verified {
  background: oklch(56% 0.12 170 / 0.12);
  color: oklch(50% 0.14 150);
}

.status-unverified {
  background: oklch(85% 0.04 80 / 0.15);
  color: #d97706;
}

.expand-panel {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 12px 16px;
  box-shadow: 0 8px 24px oklch(0 0 0 / 0.1);
  z-index: 100;
  min-width: 280px;
}

.expand-row {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-bottom: 8px;
}

.expand-row:last-child { margin-bottom: 0; }

.expand-label {
  font-size: 0.7rem;
  color: var(--muted);
  font-weight: 600;
}

.expand-value {
  font-size: 0.78rem;
  word-break: break-all;
}

.mono {
  font-family: monospace;
  font-size: 0.7rem;
}

.tooltip {
  position: absolute;
  bottom: calc(100% + 6px);
  left: 50%;
  transform: translateX(-50%);
  padding: 4px 8px;
  background: oklch(20% 0.01 240);
  color: #fff;
  border-radius: 4px;
  font-size: 0.7rem;
  white-space: nowrap;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.15s;
}

.status-badge:hover .tooltip {
  opacity: 1;
}

.animate-scale-in {
  animation: scaleIn 0.15s ease;
}

@keyframes scaleIn {
  from { transform: scale(0.95); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
</style>
