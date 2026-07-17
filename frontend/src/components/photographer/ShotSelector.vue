<template>
  <div class="shot-selector">
    <!-- Batch toolbar -->
    <div v-if="visibleCount > 0" class="batch-toolbar">
      <button class="btn btn-sm" @click="$emit('batch-update', buildSelectionMap('all'))">全选</button>
      <button class="btn btn-sm btn-green" @click="doBatch('pass')">通过选中</button>
      <button class="btn btn-sm btn-red" @click="doBatch('reject')">拒绝选中</button>
      <button class="btn btn-sm btn-blue" @click="doBatch('shortlist')">短名单</button>
      <button class="btn btn-sm btn-ghost" @click="clearSelection">清除选择</button>
      <span class="batch-count">{{ selectedIds.size }} / {{ visibleCount }}</span>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="shot-loading">加载中...</div>

    <!-- Empty -->
    <div v-else-if="visibleShots.length === 0" class="shot-empty">
      <span class="empty-icon">📷</span>
      <p>暂无作品</p>
    </div>

    <!-- Thumbnail grid -->
    <div v-else class="shot-grid">
      <div
        v-for="shot in visibleShots"
        :key="shot.id"
        :class="[
          'shot-card',
          `status-${shot.shot_status}`,
          { selected: selectedIds.has(shot.id) }
        ]"
        @click="toggleSelect(shot)"
        @mouseenter.stop="hoveredShotId = shot.id"
        @mouseleave.stop="hoveredShotId = null"
      >
        <!-- Thumbnail -->
        <div class="shot-thumb">
          <img
            :src="thumbnailUrl(shot)"
            :alt="shot.name"
            loading="lazy"
          />
          <!-- Selected ring -->
          <div v-if="selectedIds.has(shot.id)" class="select-ring">
            <span class="check">✓</span>
          </div>
          <!-- Status badge -->
          <span :class="['status-badge', `badge-${shot.shot_status}`]">
            {{ STATUS_LABELS[shot.shot_status] ?? shot.shot_status }}
          </span>
        </div>

        <!-- EXIF overlay on hover -->
        <transition name="fade">
          <div v-if="hoveredShotId === shot.id" class="exif-hover">
            <table class="exif-mini">
              <tr v-if="shot.camera_model"><td>相机</td><td>{{ shot.camera_model }}</td></tr>
              <tr v-if="shot.iso !== undefined"><td>ISO</td><td>{{ shot.iso }}</td></tr>
              <tr v-if="shot.aperture"><td>光圈</td><td>{{ shot.aperture }}</td></tr>
              <tr v-if="shot.shutter_speed"><td>快门</td><td>{{ shot.shutter_speed }}</td></tr>
              <tr v-if="shot.focal_length"><td>焦距</td><td>{{ shot.focal_length }}</td></tr>
            </table>
          </div>
        </transition>

        <!-- Info footer -->
        <div class="shot-info">
          <span class="shot-name" :title="shot.name">{{ shot.name }}</span>
          <span class="shot-dims">{{ shot.width }}x{{ shot.height }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { PhotographerShot, ShotStatus } from '@/types/photographer'

type BatchAction = ShotStatus | 'all'

interface Props {
  shots: PhotographerShot[]
  loading: boolean
  filter?: string
}

const props = withDefaults(defineProps<Props>(), {
  filter: '',
})

const emit = defineEmits<{
  'status-change': [shotId: string, status: ShotStatus, notes?: string]
  'batch-update': [selections: Map<string, ShotStatus>]
  select: [shot: PhotographerShot]
}>()

const STATUS_LABELS: Record<string, string> = {
  unreviewed: '☐ 未选',
  pass: '✅ 通过',
  hold: '⏳ 待处',
  reject: '❌ 拒绝',
  shortlist: '📊 短单',
}

// ── Filtering ──────────────────────────────────────────────────
const visibleShots = computed(() => {
  if (!props.filter) return props.shots
  return props.shots.filter((s) => s.shot_status === props.filter)
})

const visibleCount = computed(() => visibleShots.value.length)

// ── Selection state ────────────────────────────────────────────
const selectedIds = ref(new Set<string>())
const hoveredShotId = ref<string | null>(null)

function toggleSelect(shot: PhotographerShot) {
  const next = new Set(selectedIds.value)
  if (next.has(shot.id)) {
    next.delete(shot.id)
  } else {
    next.add(shot.id)
  }
  selectedIds.value = next

  emit('select', shot)
}

function clearSelection() {
  selectedIds.value = new Set()
}

function buildSelectionMap(action: BatchAction): Map<string, ShotStatus> {
  const map = new Map<string, ShotStatus>()
  const ids = [...selectedIds.value]
  if (action !== 'all') {
    for (const id of ids) {
      map.set(id, action as ShotStatus)
    }
  }
  return map
}

// ── Batch operation ────────────────────────────────────────────
async function doBatch(action: BatchAction) {
  if (selectedIds.value.size === 0) return

  try {
    const map = buildSelectionMap(action)
    for (const [id, st] of map.entries()) {
      emit('status-change', id, st)
    }
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '操作失败'
    ;(window as any).$toast?.show(msg, 'error')
  }
}

// ── Thumbnail helper ───────────────────────────────────────────
function thumbnailUrl(shot: PhotographerShot): string {
  if (shot.raw_file_path) return shot.raw_file_path
  return 'data:image/svg+xml,' + encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300">' +
    '<rect fill="#eee" width="400" height="300"/>' +
    '<text x="50%" y="50%" dominant-baseline="central" text-anchor="middle" fill="#999" font-size="14">暂无缩略图</text>' +
    '</svg>'
  )
}
</script>

<style scoped>
.batch-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  flex-wrap: wrap;
}

.batch-count {
  margin-left: auto;
  font-size: 0.82rem;
  color: var(--muted);
  font-weight: 600;
}

.shot-loading,
.shot-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  color: var(--muted);
  gap: 12px;
}

.empty-icon {
  font-size: 2.5rem;
}

/* ── Shot grid ─────────────────────────────────────────────── */
.shot-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

@media (max-width: 1200px) {
  .shot-grid { grid-template-columns: repeat(3, 1fr); }
}

@media (max-width: 900px) {
  .shot-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 600px) {
  .shot-grid { grid-template-columns: 1fr; }
}

/* ── Shot card ─────────────────────────────────────────────── */
.shot-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  transition: box-shadow 0.2s, border-color 0.2s, transform 0.15s;
  cursor: pointer;
  position: relative;
}

.shot-card:hover {
  box-shadow: 0 4px 16px oklch(0 0 0 / 0.08);
  transform: translateY(-2px);
}

.shot-card.selected {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px oklch(var(--accent) / 0.2);
}

.shot-card.status-pass { border-left: 4px solid #16a34a; }
.shot-card.status-reject { border-left: 4px solid #ef4444; }
.shot-card.status-shortlist { border-left: 4px solid #2563eb; }
.shot-card.status-hold { border-left: 4px solid #ea580c; }

.shot-thumb {
  position: relative;
  width: 100%;
  padding-top: 66.67%;
  overflow: hidden;
  background: var(--bg);
}

.shot-thumb img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.select-ring {
  position: absolute;
  top: 8px;
  left: 8px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--accent);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  z-index: 2;
  box-shadow: 0 2px 8px oklch(0 0 0 / 0.2);
}

.check {
  line-height: 1;
  font-weight: 700;
}

.status-badge {
  position: absolute;
  bottom: 8px;
  right: 8px;
  font-size: 0.68rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 10px;
  z-index: 2;
  text-shadow: 0 1px 2px oklch(0 0 0 / 0.4);
}

.badge-unreviewed { background: oklch(50% 0.02 240); color: #fff; }
.badge-pass { background: #16a34a; color: #fff; }
.badge-hold { background: #ea580c; color: #fff; }
.badge-reject { background: #ef4444; color: #fff; }
.badge-shortlist { background: #2563eb; color: #fff; }

/* ── EXIF hover overlay ────────────────────────────────────── */
.exif-hover {
  position: absolute;
  inset: 0;
  background: oklch(0 0 0 / 0.65);
  backdrop-filter: blur(2px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 3;
  padding: 12px;
}

.exif-mini {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.72rem;
  color: #fff;
}

.exif-mini td {
  padding: 2px 6px;
}

.exif-mini td:first-child {
  color: oklch(75% 0.02 240);
  font-weight: 500;
  white-space: nowrap;
}

/* ── Info footer ───────────────────────────────────────────── */
.shot-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  font-size: 0.82rem;
  border-top: 1px solid var(--border);
  background: var(--surface);
}

.shot-name {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--fg);
}

.shot-dims {
  color: var(--muted);
  font-size: 0.75rem;
  flex-shrink: 0;
}

/* ── Fade transition ───────────────────────────────────────── */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* ── Button colours ────────────────────────────────────────── */
.btn-green {
  background: #16a34a;
  color: #fff;
  border-color: #16a34a;
}

.btn-red {
  background: #ef4444;
  color: #fff;
  border-color: #ef4444;
}

.btn-blue {
  background: #2563eb;
  color: #fff;
  border-color: #2563eb;
}

.btn-ghost {
  background: transparent;
  color: var(--muted);
}

.btn {
  padding: 6px 14px;
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
</style>
