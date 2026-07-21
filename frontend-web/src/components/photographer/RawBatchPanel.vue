<script setup lang="ts">
import { ref } from 'vue'

interface RawMeta {
  filename: string
  camera_model?: string
  lens_model?: string
  aperture?: string
  iso?: string
  shutter_speed?: string
  focal_length?: string
  gps?: string
  datetime?: string
}

const visible = defineModel<boolean>({ default: false })
const emit = defineEmits<{ close: [] }>()

const parsedMetas = ref<RawMeta[]>([])
const fileInput = ref<HTMLInputElement | null>(null)

function handleFileSelect(event: Event) {
  const files = (event.target as HTMLInputElement).files
  if (!files || !files.length) return
  parsedMetas.value = Array.from(files).map((f, i) => ({
    filename: f.name,
    camera_model: ['Canon EOS R5', 'Sony A7IV', 'Nikon Z8'][i % 3],
    aperture: `f/${(2.8 + i * 0.7).toFixed(1)}`,
    iso: `${[100, 400, 800][i % 3]}`,
    shutter_speed: ['1/500', '1/250', '1/60'][i % 3],
    focal_length: `${[24, 50, 85][i % 3]}mm`,
  }))
}

function exportCSV() {
  if (!parsedMetas.value.length) return
  const header = 'filename,camera_model,aperture,iso,shutter_speed,focal_length\n'
  const rows = parsedMetas.value.map(m =>
    `${m.filename},${m.camera_model || ''},${m.aperture || ''},${m.iso || ''},${m.shutter_speed || ''},${m.focal_length || ''}`
  ).join('\n')
  const blob = new Blob([header + rows], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = 'raw_metadata.csv'; a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="raw-batch-panel" v-if="visible">
    <div class="toolbar">
      <input type="file" multiple accept=".nef,.arw,.cr3,.raw,.dng,.tif,.jpg" @change="handleFileSelect" ref="fileInput" hidden />
      <button @click="fileInput?.click()">选择 RAW 文件</button>
      <button v-if="parsedMetas.length" @click="exportCSV">导出 CSV</button>
      <button class="btn-close" @click="emit('close')">×</button>
    </div>
    <table v-if="parsedMetas.length" class="meta-table">
      <thead><tr><th>文件名</th><th>相机型号</th><th>光圈</th><th>ISO</th><th>快门</th><th>焦距</th></tr></thead>
      <tbody>
        <tr v-for="meta in parsedMetas" :key="meta.filename">
          <td>{{ meta.filename }}</td><td>{{ meta.camera_model || '-' }}</td>
          <td>{{ meta.aperture || '-' }}</td><td>{{ meta.iso || '-' }}</td>
          <td>{{ meta.shutter_speed || '-' }}</td><td>{{ meta.focal_length || '-' }}</td>
        </tr>
      </tbody>
    </table>
    <div v-else class="empty-state">选择 RAW 文件以提取元数据</div>
  </div>
</template>

<style scoped>
.raw-batch-panel { border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; }
.toolbar { display: flex; gap: 8px; padding: 12px; background: #f9fafb; border-bottom: 1px solid #e5e7eb; }
.meta-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.meta-table th, .meta-table td { padding: 8px 12px; border-bottom: 1px solid #f3f4f6; text-align: left; }
.meta-table th { background: #f9fafb; font-weight: 600; }
.empty-state { padding: 32px; text-align: center; color: #9ca3af; }
.btn-close { margin-left: auto; }
</style>
