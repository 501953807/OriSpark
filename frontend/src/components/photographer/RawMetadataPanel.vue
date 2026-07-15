<template>
  <div class="raw-metadata-panel">
    <div v-if="!props.shot" class="empty-hint">
      <span class="hint-icon">&#128247;</span>
      <p>请选择一张作品查看详情</p>
    </div>

    <template v-else>
      <!-- Shot header -->
      <div class="panel-header">
        <span class="shot-name">{{ props.shot.name }}</span>
        <span class="shot-id">{{ props.shot.id.slice(0, 8) }}</span>
      </div>

      <!-- Dimensions -->
      <div class="dimension-strip">
        <span>{{ props.shot.width }} x {{ props.shot.height }}</span>
        <span class="dim-sep">&middot;</span>
        <span>比例 {{ props.shot.aspect_ratio.toFixed(2) }}</span>
        <span class="dim-sep">&middot;</span>
        <span>{{ props.shot.width * props.shot.height >= 1000000 ? `${(props.shot.width * props.shot.height / 1000000).toFixed(1)} MP` : `${props.shot.width * props.shot.height}px` }}</span>
      </div>

      <!-- EXIF data -->
      <div class="exif-section">
        <h3 class="section-title">EXIF 参数</h3>
        <div class="exif-grid">
          <div v-if="props.shot.camera_model" class="exif-item">
            <span class="exif-label">相机</span>
            <span class="exif-value">{{ props.shot.camera_model }}</span>
          </div>
          <div v-if="props.shot.lens" class="exif-item">
            <span class="exif-label">镜头</span>
            <span class="exif-value">{{ props.shot.lens }}</span>
          </div>
          <div v-if="props.shot.iso !== undefined" class="exif-item">
            <span class="exif-label">ISO</span>
            <span class="exif-value">{{ props.shot.iso }}</span>
          </div>
          <div v-if="props.shot.aperture" class="exif-item">
            <span class="exif-label">光圈</span>
            <span class="exif-value">{{ props.shot.aperture }}</span>
          </div>
          <div v-if="props.shot.shutter_speed" class="exif-item">
            <span class="exif-label">快门</span>
            <span class="exif-value">{{ props.shot.shutter_speed }}</span>
          </div>
          <div v-if="props.shot.focal_length" class="exif-item">
            <span class="exif-label">焦距</span>
            <span class="exif-value">{{ props.shot.focal_length }}</span>
          </div>
          <div v-if="props.shot.gps_latitude != null && props.shot.gps_longitude != null" class="exif-item">
            <span class="exif-label">GPS</span>
            <span class="exif-value">
              {{ props.shot.gps_latitude.toFixed(4) }}, {{ props.shot.gps_longitude.toFixed(4) }}
              <span v-if="props.shot.gps_altitude != null"> | 海拔 {{ props.shot.gps_altitude }}m</span>
            </span>
          </div>
          <div v-if="!hasAnyExif" class="empty-exif">
            <p>暂无 EXIF 数据</p>
          </div>
        </div>
      </div>

      <!-- RAW file info -->
      <div v-if="props.shot.raw_file_path" class="raw-section">
        <h3 class="section-title">RAW 文件</h3>
        <div class="raw-info">
          <span class="raw-icon">&#128196;</span>
          <code class="raw-path">{{ props.shot.raw_file_path }}</code>
          <span class="raw-format">{{ getRawFormat(props.shot.raw_file_path) }}</span>
        </div>
      </div>

      <!-- Notes editor -->
      <div class="notes-section">
        <label class="notes-label">备注</label>
        <textarea
          v-model="localNotes"
          class="notes-textarea"
          rows="3"
          placeholder="添加拍摄备注..."
        ></textarea>
        <div class="notes-actions">
          <button
            class="btn btn-sm btn-primary"
            :disabled="!hasNotesChanges"
            @click="saveNotes"
          >保存备注</button>
          <button
            v-if="hasNotesChanges"
            class="btn btn-sm btn-ghost"
            @click="cancelNotes"
          >取消</button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { PhotographerShot } from '@/types/photographer'

interface Props {
  shot: PhotographerShot | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  update: [shotId: string, field: string, value: string]
}>()

// ── Local notes editing ────────────────────────────────────────
const localNotes = ref(props.shot?.shot_notes ?? '')
const originalNotes = ref(props.shot?.shot_notes ?? '')

watch(
  () => props.shot?.shot_notes,
  (val) => {
    localNotes.value = val ?? ''
    originalNotes.value = val ?? ''
  },
)

const hasNotesChanges = computed(() => localNotes.value !== originalNotes.value)

// ── Save / cancel ──────────────────────────────────────────────
async function saveNotes() {
  if (!props.shot || !hasNotesChanges.value) return

  try {
    emit('update', props.shot.id, 'shot_notes', localNotes.value)
    originalNotes.value = localNotes.value
    ;(window as any).$toast?.show('备注已保存', 'success')
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '保存失败'
    ;(window as any).$toast?.show(msg, 'error')
  }
}

function cancelNotes() {
  localNotes.value = originalNotes.value
}

// ── Helpers ────────────────────────────────────────────────────
const hasAnyExif = computed(() =>
  !!(
    props.shot?.camera_model ||
    props.shot?.lens ||
    props.shot?.iso !== undefined ||
    props.shot?.aperture ||
    props.shot?.shutter_speed ||
    props.shot?.focal_length ||
    (props.shot?.gps_latitude != null && props.shot?.gps_longitude != null)
  ),
)

function getRawFormat(filePath: string): string {
  const ext = filePath.split('.').pop()?.toUpperCase() ?? ''
  const extMap: Record<string, string> = {
    RAW: 'Canon RAW',
    CR2: 'Canon RAW',
    CR3: 'Canon RAW (3rd gen)',
    NEF: 'Nikon RAW',
    NRW: 'Panasonic RAW',
    ORF: 'Olympus RAW',
    ARW: 'Sony RAW',
    DNG: 'Digital Negative (DNG)',
    PEF: 'Pentax RAW',
    K26: 'Kodak RAW',
  }
  return extMap[ext] ?? ext
}
</script>

<style scoped>
.empty-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  color: var(--muted);
  gap: 12px;
}

.hint-icon {
  font-size: 2.5rem;
}

/* ── Panel header ──────────────────────────────────────────── */
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}

.shot-name {
  font-size: 1rem;
  font-weight: 600;
  color: var(--fg);
}

.shot-id {
  font-size: 0.72rem;
  color: var(--muted);
  font-family: monospace;
  background: var(--bg);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}

/* ── Dimension strip ───────────────────────────────────────── */
.dimension-strip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 0;
  font-size: 0.82rem;
  color: var(--muted);
}

.dim-sep {
  opacity: 0.5;
}

/* ── Sections ──────────────────────────────────────────────── */
.exif-section,
.raw-section,
.notes-section {
  padding: 16px 0;
  border-bottom: 1px solid var(--border);
}

.section-title {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0 0 12px;
}

/* ── EXIF grid ─────────────────────────────────────────────── */
.exif-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px;
}

.exif-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 14px;
  background: var(--bg);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
}

.exif-label {
  font-size: 0.72rem;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-weight: 500;
}

.exif-value {
  font-size: 0.9rem;
  color: var(--fg);
  font-weight: 500;
  word-break: break-all;
}

.empty-exif {
  grid-column: 1 / -1;
  padding: 20px;
  text-align: center;
  color: var(--muted);
  font-size: 0.88rem;
  background: var(--bg);
  border-radius: var(--radius-sm);
}

/* ── RAW info ──────────────────────────────────────────────── */
.raw-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.84rem;
}

.raw-icon {
  font-size: 1.1rem;
  flex-shrink: 0;
}

.raw-path {
  flex: 1;
  font-family: monospace;
  font-size: 0.78rem;
  color: var(--fg);
  word-break: break-all;
}

.raw-format {
  font-size: 0.72rem;
  color: var(--muted);
  background: var(--surface);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  white-space: nowrap;
}

/* ── Notes ─────────────────────────────────────────────────── */
.notes-label {
  display: block;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 8px;
}

.notes-textarea {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.88rem;
  font-family: inherit;
  color: var(--fg);
  background: var(--bg);
  resize: vertical;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.notes-textarea:focus {
  outline: none;
  border-color: var(--accent);
}

.notes-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.btn {
  padding: 6px 16px;
  border-radius: var(--radius-sm);
  font-size: 0.82rem;
  cursor: pointer;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--fg);
  font-family: inherit;
  transition: background 0.2s;
}

.btn:hover { background: var(--bg); }

.btn-sm { padding: 6px 14px; font-size: 0.82rem; }

.btn-primary {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}

.btn-primary:hover {
  background: oklch(minus(var(--grad1-luminance), 0.05) var(--grad1-chroma) var(--grad1-angle));
}

.btn-ghost {
  background: transparent;
  color: var(--muted);
}

.btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
