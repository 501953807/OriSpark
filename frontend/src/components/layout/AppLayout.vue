<template>
  <div class="flex min-h-screen">
    <!-- P3.3.1: Skip to content link -->
    <a href="#main-content" class="skip-link">跳转到主内容</a>

    <!-- P3.4.1: Mobile hamburger -->
    <button
      class="mobile-menu-btn"
      aria-label="打开菜单"
      :aria-expanded="mobileMenuOpen"
      @click="mobileMenuOpen = !mobileMenuOpen"
    >
      <span class="hamburger-line" :class="{ open: mobileMenuOpen }"></span>
    </button>

    <!-- P3.4.1: Mobile overlay -->
    <div v-if="mobileMenuOpen" class="mobile-overlay" @click="mobileMenuOpen = false" aria-hidden="true"></div>

    <AppSidebar :class="{ 'mobile-visible': mobileMenuOpen }" />

    <div
      :id="'main-content'"
      :class="['main-content', 'flex-1', isCollapsed ? 'ml-[60px]' : 'ml-[var(--sidebar-w)]']"
    >
      <AppTopbar @toggle-mobile="mobileMenuOpen = !mobileMenuOpen" @show-import="showImportModal = true" />
      <Breadcrumb />
      <BusinessChainBar />
      <main class="p-6 max-w-[1400px]">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>

    <!-- Import Modal -->
    <div v-if="showImportModal" class="modal-overlay" @click.self="showImportModal = false">
      <div class="modal-card animate-scale-in" style="max-width:640px">
        <div class="modal-header"><h3>📤 导入作品</h3><button class="modal-close-btn" @click="showImportModal = false">×</button></div>

        <!-- Import mode tabs -->
        <div class="import-tabs">
          <button :class="['import-tab', { active: importMode === 'local' }]" @click="importMode = 'local'">💻 本地上传</button>
          <button :class="['import-tab', { active: importMode === 'batch' }]" @click="importMode = 'batch'">📦 批量导入</button>
          <button :class="['import-tab', { active: importMode === 'sync' }]" @click="importMode = 'sync'">🔗 平台同步</button>
        </div>

        <!-- Local upload -->
        <div v-if="importMode === 'local'" class="import-panel">
          <div class="import-zone" :class="{ dragging: isDragging }" @dragover.prevent="isDragging = true" @dragleave="isDragging = false" @drop.prevent="onDrop">
            <div v-if="!isDragging" class="import-zone-inner">
              <span class="import-icon">📁</span>
              <p class="import-hint">拖拽文件到此处</p>
              <p class="import-or">或</p>
              <label class="btn btn-primary">选择文件
                <input type="file" multiple accept="image/*,video/*,audio/*,.pdf,.doc,.docx" class="hidden" @change="onFilesSelected" />
              </label>
            </div>
            <div v-else class="import-zone-inner import-zone-active">
              <span class="import-icon">✨</span>
              <p class="import-hint">松开鼠标导入文件</p>
            </div>
          </div>
          <div class="format-specs">
            <strong>支持的格式：</strong>
            <span class="fmt-chip">JPG/PNG/GIF/WebP (≤20MB)</span>
            <span class="fmt-chip">MP4/WebM/MOV (≤200MB)</span>
            <span class="fmt-chip">MP3/WAV/OGG (≤20MB)</span>
            <span class="fmt-chip">PDF/DOC/DOCX (≤10MB)</span>
          </div>
        </div>

        <!-- Batch import -->
        <div v-if="importMode === 'batch'" class="import-panel">
          <div class="batch-upload-zone" :class="{ dragging: isBatchDragging }" @dragover.prevent="isBatchDragging = true" @dragleave="isBatchDragging = false" @drop.prevent="onBatchDrop">
            <div v-if="!isBatchDragging" class="batch-zone-inner">
              <span class="import-icon">📦</span>
              <p class="import-hint">拖拽 ZIP/RAR 压缩包到此处</p>
              <p class="import-or">或选择压缩包文件</p>
              <label class="btn btn-primary">选择压缩包
                <input type="file" accept=".zip,.rar,.7z,.tar.gz" class="hidden" @change="onBatchFileSelected" />
              </label>
            </div>
            <div v-else class="batch-zone-inner batch-zone-active">
              <span class="import-icon">📦</span>
              <p class="import-hint">松开鼠标导入压缩包</p>
            </div>
          </div>
          <div class="batch-info">
            <p style="font-size:.82rem;color:var(--muted);margin:0">
              💡 支持 ZIP/RAR/TAR.GZ 格式压缩包，最大 500MB。系统将自动解压并批量创建作品条目。
            </p>
          </div>
        </div>

        <!-- Third-party sync -->
        <div v-if="importMode === 'sync'" class="import-panel">
          <div class="sync-options">
            <div class="sync-card" v-if="false">
              <span class="sync-icon">🎨</span>
              <div>
                <strong>ArtStation</strong>
                <p style="font-size:.78rem;color:var(--muted);margin:0">同步作品集和创作记录</p>
              </div>
              <button class="btn btn-sm btn-secondary" disabled>连接中</button>
            </div>
            <div class="sync-card" v-if="false">
              <span class="sync-icon">📸</span>
              <div>
                <strong>Flickr</strong>
                <p style="font-size:.78rem;color:var(--muted);margin:0">同步相册和元数据</p>
              </div>
              <button class="btn btn-sm btn-secondary" disabled>连接中</button>
            </div>
            <div class="sync-card">
              <span class="sync-icon">🔌</span>
              <div>
                <strong>更多平台</strong>
                <p style="font-size:.78rem;color:var(--muted);margin:0">Instagram, Behance, DeviantArt 等</p>
              </div>
              <button class="btn btn-sm btn-secondary" disabled>建设中</button>
            </div>
          </div>
        </div>

        <!-- Upload progress (local mode) -->
        <div v-if="uploadingFiles.length && importMode === 'local'" class="upload-list">
          <div v-for="(f, i) in uploadingFiles" :key="i" class="upload-item card">
            <div class="upload-item-header">
              <span class="upload-filename">{{ f.name }}</span>
              <span class="upload-size">{{ formatSize(f.size) }}</span>
            </div>
            <div class="upload-progress-bar">
              <div class="upload-progress-fill" :style="{ width: f.progress + '%' }"></div>
            </div>
            <div class="upload-status">
              <span :class="['upload-status-text', f.status]">{{ statusText(f) }}</span>
              <button v-if="f.status === 'error'" class="btn btn-ghost btn-xs" @click="retryUpload(i)">重试</button>
            </div>
          </div>
        </div>

        <!-- Batch progress -->
        <div v-if="batchFiles.length && importMode === 'batch'" class="upload-list">
          <div v-for="(f, i) in batchFiles" :key="i" class="upload-item card">
            <div class="upload-item-header">
              <span class="upload-filename">{{ f.name }}</span>
              <span class="upload-size">{{ formatSize(f.size) }}</span>
            </div>
            <div class="upload-progress-bar">
              <div class="upload-progress-fill" :style="{ width: f.progress + '%' }"></div>
            </div>
            <div class="upload-status">
              <span :class="['upload-status-text', f.status]">{{ statusText(f) }}</span>
              <button v-if="f.status === 'error'" class="btn btn-ghost btn-xs" @click="retryBatchUpload(i)">重试</button>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showImportModal = false">关闭</button>
          <template v-if="importMode === 'local'">
            <button class="btn btn-primary" @click="startUpload" :disabled="selectedFiles.length === 0 || uploading">
              {{ uploading ? '上传中...' : '开始上传' }}
            </button>
          </template>
          <template v-if="importMode === 'batch'">
            <button class="btn btn-primary" @click="startBatchUpload" :disabled="batchFiles.length === 0 || batchUploading">
              {{ batchUploading ? '解析中...' : '开始导入' }}
            </button>
          </template>
        </div>
      </div>
    </div>

    <ToastContainer />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import AppSidebar from './AppSidebar.vue'
import AppTopbar from './AppTopbar.vue'
import BusinessChainBar from './BusinessChainBar.vue'
import Breadcrumb from '@/components/common/Breadcrumb.vue'
import ToastContainer from '@/components/common/ToastContainer.vue'
import { useAppStore } from '@/stores/useAppStore'
import { worksApi } from '@/api/works'

const appStore = useAppStore()
const isCollapsed = computed(() => appStore.sidebarCollapsed)
const mobileMenuOpen = ref(false)
const showImportModal = ref(false)
const importMode = ref<'local' | 'batch' | 'sync'>('local')
const isDragging = ref(false)
const isBatchDragging = ref(false)
const selectedFiles = ref<File[]>([])
const uploadingFiles = ref<any[]>([])
const uploading = ref(false)
const batchFiles = ref<any[]>([])
const batchUploading = ref(false)

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function statusText(f: any): string {
  if (f.status === 'done') return '上传成功'
  if (f.status === 'error') return '上传失败'
  return `上传中 ${f.progress}%`
}

function onDrop(event: DragEvent) {
  isDragging.value = false
  const files = Array.from(event.dataTransfer?.files || [])
  selectedFiles.value = [...selectedFiles.value, ...files]
  uploadingFiles.value = files.map(f => ({
    name: f.name, size: f.size, progress: 0, status: 'pending' as const,
  }))
}

function onFilesSelected(event: Event) {
  const files = Array.from((event.target as HTMLInputElement).files || [])
  selectedFiles.value = [...selectedFiles.value, ...files]
  uploadingFiles.value = files.map(f => ({
    name: f.name, size: f.size, progress: 0, status: 'pending' as const,
  }))
}

function onBatchDrop(event: DragEvent) {
  isBatchDragging.value = false
  const files = Array.from(event.dataTransfer?.files || [])
  batchFiles.value = [...batchFiles.value, ...files.map(f => ({ name: f.name, size: f.size, progress: 0, status: 'pending' as const, file: f }))]
}

function onBatchFileSelected(event: Event) {
  const files = Array.from((event.target as HTMLInputElement).files || [])
  batchFiles.value = [...batchFiles.value, ...files.map(f => ({ name: f.name, size: f.size, progress: 0, status: 'pending' as const, file: f }))]
}

async function startBatchUpload() {
  if (batchFiles.value.length === 0 || batchUploading.value) return
  batchUploading.value = true
  for (let i = 0; i < batchFiles.value.length; i++) {
    const entry = batchFiles.value[i]
    const file = entry.file as File
    entry.status = 'uploading'
    entry.progress = 10
    try {
      const fd = new FormData()
      fd.append('file', file)
      fd.append('batch', 'true')
      await worksApi.create(fd)
      entry.status = 'done'
      entry.progress = 100
      ;(window as any).$toast?.show(`${file.name} 解析完成`, 'success')
    } catch {
      entry.status = 'error'
      entry.progress = 0
    }
  }
  batchUploading.value = false
  batchFiles.value = []
}

function retryBatchUpload(index: number) {
  const entry = batchFiles.value[index]
  entry.status = 'pending'
  entry.progress = 0
}

async function startUpload() {
  if (selectedFiles.value.length === 0 || uploading.value) return
  uploading.value = true
  for (let i = 0; i < selectedFiles.value.length; i++) {
    const file = selectedFiles.value[i]
    const uf = uploadingFiles.value[i]
    uf.status = 'uploading'
    uf.progress = 10
    try {
      const fd = new FormData()
      fd.append('file', file)
      await worksApi.create(fd)
      uf.status = 'done'
      uf.progress = 100
      ;(window as any).$toast?.show(`${file.name} 上传成功`, 'success')
    } catch {
      uf.status = 'error'
      uf.progress = 0
    }
  }
  uploading.value = false
  selectedFiles.value = []
  setTimeout(() => { uploadingFiles.value = [] }, 3000)
}

function retryUpload(index: number) {
  const uf = uploadingFiles.value[index]
  uf.status = 'pending'
  uf.progress = 0
}
</script>

<style scoped>
.main-content {
  transition: margin-left 0.3s ease;
}
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

/* P3.3.1: Skip link */
.skip-link {
  position: fixed;
  top: -100px;
  left: 8px;
  z-index: 9999;
  padding: 8px 16px;
  background: var(--accent);
  color: #fff;
  font-weight: 600;
  font-size: 0.9rem;
  border-radius: var(--radius-sm);
  text-decoration: none;
  transition: top 0.2s;
}
.skip-link:focus {
  top: 8px;
}

/* P3.4.1: Mobile hamburger button */
.mobile-menu-btn {
  display: none;
  position: fixed;
  top: 12px;
  left: 12px;
  z-index: 110;
  width: 40px;
  height: 40px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--surface);
  box-shadow: 0 2px 8px oklch(0 0 0 / 0.08);
  cursor: pointer;
  align-items: center;
  justify-content: center;
}
.hamburger-line,
.hamburger-line::before,
.hamburger-line::after {
  display: block;
  width: 20px;
  height: 2px;
  background: var(--fg);
  border-radius: 2px;
  transition: transform 0.3s, opacity 0.3s;
}
.hamburger-line { position: relative; }
.hamburger-line::before, .hamburger-line::after { content: ''; position: absolute; left: 0; }
.hamburger-line::before { top: -6px; }
.hamburger-line::after { top: 6px; }
.hamburger-line.open { background: transparent; }
.hamburger-line.open::before { transform: translateY(6px) rotate(45deg); }
.hamburger-line.open::after { transform: translateY(-6px) rotate(-45deg); }

.mobile-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: oklch(0 0 0 / 0.4);
  z-index: 95;
}

@media (max-width: 767px) {
  .mobile-menu-btn { display: inline-flex; }
  .mobile-overlay { display: block; }
  .main-content { margin-left: 0 !important; padding-top: 64px; }
  .sidebar { transform: translateX(-100%); }
  .sidebar.mobile-visible { transform: translateX(0); }
  main { padding: 16px !important; }
}

/* Import modal */
.hidden { display: none; }
.import-zone {
  border: 2px dashed var(--border); border-radius: var(--radius); padding: 40px 20px;
  text-align: center; transition: all 0.2s; cursor: pointer;
}
.import-zone.dragging { border-color: var(--accent); background: oklch(56% 0.12 170 / 0.04); }
.import-zone-inner { display: flex; flex-direction: column; align-items: center; gap: 8px; }
.import-icon { font-size: 2.5rem; }
.import-hint { font-size: .9rem; color: var(--muted); margin: 0; }
.import-or { font-size: .78rem; color: var(--muted); margin: 0; }
.import-zone-active .import-icon { font-size: 3rem; }

/* Import mode tabs */
.import-tabs { display: flex; gap: 4px; margin-bottom: 16px; border-bottom: 1px solid var(--border); padding-bottom: 0; }
.import-tab { padding: 8px 16px; font-size: .82rem; font-weight: 600; cursor: pointer; border: none; background: none; color: var(--muted); font-family: var(--font-body); border-bottom: 2px solid transparent; transition: all .2s; }
.import-tab.active { color: var(--accent); border-bottom-color: var(--accent); }

/* Import panels */
.import-panel { margin-bottom: 12px; }
.format-specs { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 12px; }
.fmt-chip { font-size: .72rem; padding: 2px 8px; background: oklch(96% .003 240); border-radius: 4px; color: var(--muted); }

/* Batch upload zone */
.batch-upload-zone { border: 2px dashed var(--border); border-radius: var(--radius); padding: 32px; text-align: center; transition: all .2s; }
.batch-upload-zone.dragging { border-color: var(--accent); background: oklch(56% .12 170 / .03); }
.batch-zone-inner { display: flex; flex-direction: column; align-items: center; gap: 8px; }
.batch-zone-active { background: oklch(56% .12 170 / .05) !important; }
.batch-info { margin-top: 12px; padding: 12px; background: oklch(56% .12 170 / .05); border-radius: var(--radius-sm); }

/* Sync options */
.sync-options { display: flex; flex-direction: column; gap: 10px; }
.sync-card { display: flex; align-items: center; gap: 12px; padding: 14px; border: 1px solid var(--border); border-radius: var(--radius-sm); }
.sync-icon { font-size: 1.5rem; }
.sync-card strong { font-size: .9rem; }
.sync-card p { font-size: .78rem; color: var(--muted); margin: 0; }

.upload-list { display: flex; flex-direction: column; gap: 8px; max-height: 300px; overflow-y: auto; }
.upload-item { padding: 12px; }
.upload-item-header { display: flex; justify-content: space-between; font-size: .82rem; margin-bottom: 6px; }
.upload-filename { font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }
.upload-size { font-size: .75rem; color: var(--muted); }
.upload-progress-bar { height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; margin-bottom: 4px; }
.upload-progress-fill { height: 100%; background: var(--accent); border-radius: 3px; transition: width .3s; }
.upload-status { display: flex; justify-content: space-between; align-items: center; font-size: .75rem; }
.upload-status-text.done { color: var(--accent); }
.upload-status-text.error { color: var(--red); }
</style>
