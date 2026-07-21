<template>
  <div class="related-card card">
    <h3>🔗 关联</h3>
    <div class="info-list">
      <div class="info-row">
        <span class="il">存证记录</span>
        <span class="iv">{{ notaryCount }} 条</span>
      </div>
      <div class="info-row">
        <span class="il">产品</span>
        <span class="iv">{{ productCount }} 个</span>
      </div>
      <div class="info-row">
        <span class="il">授权</span>
        <span class="iv">{{ licenseCount }} 条</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  notaryCount?: number
  productCount?: number
  licenseCount?: number
}>()
</script>

<style scoped>
.related-card { padding: 16px 20px; }
.related-card h3 { margin: 0 0 12px; font-size: 0.88rem; }
.info-list { display: flex; flex-direction: column; gap: 6px; }
.info-row { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; font-size: 0.78rem; padding: 4px 0; border-bottom: 1px solid oklch(94% 0.003 240); }
.info-row:last-child { border-bottom: none; }
.il { color: var(--muted); font-weight: 600; flex-shrink: 0; }
.iv { text-align: right; }
</style>
