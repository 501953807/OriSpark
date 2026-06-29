<template>
  <div class="file-info-card card">
    <h3>📋 文件信息</h3>
    <div class="info-list">
      <div class="info-row">
        <span class="il">存证状态</span>
        <span class="iv">
          <NotarizationStatus :work="work" />
        </span>
      </div>
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
import NotarizationStatus from './NotarizationStatus.vue'

defineProps<{
  work: {
    file_size: number
    width: number | null
    height: number | null
    mime_type: string | null
    imported_at: string
    is_verified: boolean
    verified_date?: string | null
    sha256?: string | null
    custom_metadata?: Record<string, any> | null
  }
}>()

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}
</script>

<style scoped>
.file-info-card { padding: 16px 20px; }
.file-info-card h3 { margin: 0 0 12px; font-size: 0.88rem; }
.info-list { display: flex; flex-direction: column; gap: 6px; }
.info-row { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; font-size: 0.78rem; padding: 4px 0; border-bottom: 1px solid oklch(94% 0.003 240); }
.info-row:last-child { border-bottom: none; }
.il { color: var(--muted); font-weight: 600; flex-shrink: 0; }
.iv { text-align: right; word-break: break-all; }
</style>
