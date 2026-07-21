<template>
  <div class="file-info-strip card">
    <div class="info-list">
      <div class="info-row">
        <span class="il">文件大小</span>
        <span class="iv">{{ formatFileSize(work.file_size) }}</span>
      </div>
      <div class="info-row">
        <span class="il">尺寸</span>
        <span class="iv">{{ work.width || '?' }} × {{ work.height || '?' }}</span>
      </div>
      <div class="info-row">
        <span class="il">MIME</span>
        <span class="iv">{{ work.mime_type || '—' }}</span>
      </div>
      <div class="info-row">
        <span class="il">导入时间</span>
        <span class="iv">{{ work.imported_at?.slice(0, 16) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  work: {
    file_size: number
    width: number | null
    height: number | null
    mime_type: string | null
    imported_at: string
  }
}>()

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}
</script>

<style scoped>
.file-info-strip { padding: 12px 16px; }
.info-list { display: flex; flex-direction: column; gap: 0; }
.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  font-size: 0.75rem;
  padding: 5px 0;
  border-bottom: 1px solid oklch(94% 0.003 240);
}
.info-row:last-child { border-bottom: none; }
.il { color: var(--muted); font-weight: 600; flex-shrink: 0; }
.iv { text-align: right; word-break: break-all; }
</style>
