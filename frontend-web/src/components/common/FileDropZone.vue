<template>
  <div class="drop-zone-wrapper">
    <!-- Mode toggle -->
    <div class="mode-toggle">
      <button
        :class="['mode-btn', { active: isFolderMode }]"
        @click="isFolderMode = false"
      >文件导入</button>
      <button
        :class="['mode-btn', { active: isFolderMode }]"
        @click="isFolderMode = true"
      >文件夹导入</button>
    </div>

    <div
      class="drop-zone"
      :class="{ 'drag-over': isDragOver, 'folder-mode': isFolderMode }"
      @dragover.prevent="isDragOver = true"
      @dragleave="isDragOver = false"
      @drop.prevent="handleDrop"
    >
      <div class="dz-content">
        <div class="dz-icon">📤</div>
        <div class="dz-title">{{ isFolderMode ? '拖拽文件夹到此处上传' : '拖拽文件到此处上传' }}</div>
        <div class="dz-subtitle">{{ isFolderMode ? '点击选择文件夹（支持多层嵌套）' : '或点击选择文件' }}</div>
        <div class="dz-hint">
          支持 JPG, PNG, WebP, GIF, SVG, MP3, WAV, MP4, PDF, DOCX 等格式
        </div>
      </div>
      <input
        ref="inputRef"
        type="file"
        :class="['dz-input', { 'dz-input-folder': isFolderMode }]"
        :accept="acceptTypes"
        :webkitdirectory="isFolderMode"
        :directory="isFolderMode"
        @change="handleInput"
      />
    </div>
    <!-- File list preview -->
    <div v-if="files.length" class="file-list">
      <div v-for="(f, i) in files" :key="i" class="file-item">
        <span class="file-icon">{{ getFileIcon(f) }}</span>
        <span class="file-name">{{ f.name }}</span>
        <span class="file-size">{{ formatSize(f.size) }}</span>
        <button class="file-remove" @click="removeFile(i)">×</button>
      </div>
      <div class="file-actions">
        <button class="btn btn-secondary" @click="clearFiles">取消</button>
        <button class="btn btn-primary" @click="uploadFiles" :disabled="!files.length">
          导入 {{ files.length }} 个文件
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = withDefaults(defineProps<{
  acceptTypes?: string
}>(), {
  acceptTypes: 'image/*,audio/*,video/*,.pdf,.docx,.txt,.md,.psd,.ai',
})

const emit = defineEmits<{
  upload: [files: File[]]
}>()

const inputRef = ref<HTMLInputElement>()
const isDragOver = ref(false)
const files = ref<File[]>([])
const isFolderMode = ref(false)

function handleDrop(e: DragEvent) {
  isDragOver.value = false
  if (e.dataTransfer?.files) {
    addFiles(e.dataTransfer.files)
  }
}

function handleInput(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files) {
    addFiles(target.files)
  }
}

function addFiles(list: FileList) {
  for (let i = 0; i < list.length; i++) {
    files.value.push(list[i])
  }
}

function removeFile(index: number) {
  files.value.splice(index, 1)
}

function clearFiles() {
  files.value = []
}

function uploadFiles() {
  emit('upload', [...files.value])
  files.value = []
}

function getFileIcon(f: File): string {
  const ext = f.name.split('.').pop()?.toLowerCase()
  if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(ext || '')) return '🖼️'
  if (['mp3', 'wav', 'flac', 'ogg'].includes(ext || '')) return '🎵'
  if (['mp4', 'mov', 'webm'].includes(ext || '')) return '🎬'
  if (['pdf', 'docx', 'txt', 'md'].includes(ext || '')) return '📄'
  return '📁'
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}
</script>

<style scoped>
.drop-zone-wrapper { display: flex; flex-direction: column; gap: 12px; }

/* Mode toggle */
.mode-toggle {
  display: flex;
  gap: 4px;
  background: oklch(90% 0.005 240);
  border-radius: var(--radius-sm);
  padding: 3px;
}
.dark .mode-toggle {
  background: oklch(28% 0.01 240);
}
.mode-btn {
  flex: 1;
  padding: 6px 14px;
  border: none;
  border-radius: 4px;
  background: transparent;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  color: var(--muted);
  transition: all 0.15s;
  font-family: var(--font-body);
}
.mode-btn.active {
  background: var(--surface);
  color: var(--fg);
  box-shadow: 0 1px 3px oklch(0 0 0 / 0.08);
  font-weight: 600;
}
.mode-btn:hover:not(.active) {
  color: var(--fg);
}

.drop-zone {
  border: 2px dashed var(--border);
  border-radius: var(--radius-lg);
  padding: 48px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  background: oklch(96% 0.004 240);
}
.dark .drop-zone {
  background: oklch(22% 0.01 240);
}
.drop-zone:hover, .drop-zone.drag-over {
  border-color: var(--accent);
  background: oklch(56% 0.12 170 / 0.05);
}
.dz-input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}
.dz-icon { font-size: 3rem; margin-bottom: 12px; }
.dz-title { font-size: 1.1rem; font-weight: 700; margin-bottom: 4px; }
.dz-subtitle { font-size: 0.88rem; color: var(--muted); }
.dz-hint { font-size: 0.75rem; color: var(--muted); margin-top: 12px; }
.file-list { margin-top: 16px; }
.file-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  margin-bottom: 6px;
  font-size: 0.88rem;
}
.file-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.file-size { color: var(--muted); flex-shrink: 0; }
.file-remove {
  background: none; border: none; cursor: pointer;
  font-size: 1.2rem; color: var(--muted); padding: 0 4px;
}
.file-remove:hover { color: #e53e3e; }
.file-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 12px;
}
</style>
