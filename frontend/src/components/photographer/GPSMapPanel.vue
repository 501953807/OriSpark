<template>
  <div class="gps-map-panel">
    <div v-if="loading" class="map-loading">加载地图数据...</div>

    <div v-else-if="visibleShots.length === 0" class="map-empty">
      <span class="empty-icon">&#128205;</span>
      <p>暂无带 GPS 信息的作品</p>
    </div>

    <template v-else>
      <!-- Map summary -->
      <div class="map-summary">
        <span>&#128205; {{ visibleShots.length }} 个带 GPS 坐标的作品</span>
        <span class="summary-sep">&middot;</span>
        <span>{{ uniqueLocations }} 个独立位置</span>
      </div>

      <!-- Map canvas placeholder -->
      <div class="map-canvas" ref="mapElRef">
        <!-- Background grid pattern -->
        <div class="map-bg">
          <div v-for="i in 40" :key="'h' + i" class="grid-line-h"></div>
          <div v-for="i in 30" :key="'v' + i" class="grid-line-v"></div>
        </div>

        <!-- GPS pins rendered proportional to coordinates -->
        <div
          v-for="shot in visibleShots"
          :key="shot.id"
          class="gps-pin"
          :style="pinStyle(shot)"
          @click="activePinId = shot.id"
          @mouseenter="hoveredPinId = shot.id"
          @mouseleave="hoveredPinId = null"
        >
          <span class="pin-icon">&#128205;</span>
          <!-- Pulse ring for hovered pin -->
          <span v-if="hoveredPinId === shot.id" class="pin-pulse"></span>
        </div>

        <!-- Tooltip overlay for active/hovered pin -->
        <transition name="tooltip-fade">
          <div v-if="activePinId || hoveredPinId" class="map-tooltip" :style="tooltipStyle">
            <div class="tooltip-thumb">
              <img :src="thumbnailUrl(getActiveShot())" :alt="getActiveShot()?.name" />
            </div>
            <div class="tooltip-exif">
              <div class="tooltip-name">{{ activeShot?.name }}</div>
              <table class="tooltip-table">
                <tr v-if="activeShot?.camera_model"><td>相机</td><td>{{ activeShot.camera_model }}</td></tr>
                <tr v-if="activeShot?.iso !== undefined"><td>ISO</td><td>{{ activeShot.iso }}</td></tr>
                <tr v-if="activeShot?.aperture"><td>光圈</td><td>{{ activeShot.aperture }}</td></tr>
                <tr v-if="activeShot?.shutter_speed"><td>快门</td><td>{{ activeShot.shutter_speed }}</td></tr>
                <tr v-if="activeShot?.focal_length"><td>焦距</td><td>{{ activeShot.focal_length }}</td></tr>
                <tr><td>坐标</td><td>
                  {{ activeShot?.gps_latitude?.toFixed(4) }}, {{ activeShot?.gps_longitude?.toFixed(4) }}
                </td></tr>
              </table>
            </div>
          </div>
        </transition>
      </div>

      <!-- GPS point cards -->
      <div class="point-cards">
        <div
          v-for="shot in visibleShots"
          :key="shot.id"
          :class="['point-card', { active: activePinId === shot.id }]"
          @click="activePinId = shot.id"
        >
          <div class="card-location">
            <span class="location-icon">&#128205;</span>
            <span class="coord-text">
              {{ shot.gps_latitude?.toFixed(4) }}, {{ shot.gps_longitude?.toFixed(4) }}
            </span>
          </div>
          <span v-if="shot.camera_model" class="card-camera">{{ shot.camera_model }}</span>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { PhotographerShot } from '@/types/photographer'

interface Props {
  shots: PhotographerShot[]
  loading: boolean
}

const props = defineProps<Props>()

// ── GPS-filtered shots ─────────────────────────────────────────
const visibleShots = computed(() => {
  return props.shots.filter(
    (s: PhotographerShot) => s.gps_latitude != null && s.gps_longitude != null,
  )
})

const uniqueLocations = computed(() => {
  const set = new Set<string>()
  for (const s of visibleShots.value) {
    if (s.gps_latitude != null && s.gps_longitude != null) {
      set.add(`${s.gps_latitude.toFixed(2)},${s.gps_longitude.toFixed(2)}`)
    }
  }
  return set.size
})

// ── Pin positioning ────────────────────────────────────────────
// Convert lat/lng to percentage of map canvas (approx. world projection)
const MIN_LAT = -90
const MAX_LAT = 90
const MIN_LNG = -180
const MAX_LNG = 180

function pinStyle(shot: PhotographerShot) {
  const top = percentage(shot.gps_latitude ?? 0, MAX_LAT, MIN_LAT, 5, 95)
  const left = percentage(shot.gps_longitude ?? 0, MAX_LNG, MIN_LNG, 5, 95)
  return { top: `${top}%`, left: `${left}%` }
}

function percentage(value: number, min: number, max: number, padTop: number, padLeft: number) {
  const norm = ((value - min) / (max - min)) * 100
  return padTop + (100 - padTop - padTop) * (1 - norm / 100)
}

// ── Tooltip positioning ────────────────────────────────────────
const activePinId = ref<string | null>(null)
const hoveredPinId = ref<string | null>(null)

const activeShot = computed(() =>
  visibleShots.value.find((s) => s.id === activePinId.value) ?? null,
)

const tooltipStyle = computed(() => {
  if (!activeShot.value?.gps_latitude && !activeShot.value?.gps_longitude) return {}
  // Position relative to pin (inferred from activeShot)
  const top = pinStyle(activeShot.value)
  return {
    top: parseInt(top.top) + 3 + '%',
    left: parseInt(top.left) + 2 + '%',
  }
})

function getActiveShot(): PhotographerShot | null {
  return activeShot.value
}

// ── Thumbnail helper ───────────────────────────────────────────
function thumbnailUrl(shot: PhotographerShot | null): string {
  if (!shot) return ''
  if (shot.raw_file_path) return shot.raw_file_path
  return 'data:image/svg+xml,' + encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" width="120" height="90">' +
    '<rect fill="#eee" width="120" height="90"/>' +
    '<text x="50%" y="50%" dominant-baseline="central" text-anchor="middle" fill="#999" font-size="10">图片</text>' +
    '</svg>'
  )
}
</script>

<style scoped>
.map-loading,
.map-empty {
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

/* ── Summary bar ───────────────────────────────────────────── */
.map-summary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  font-size: 0.84rem;
  color: var(--fg);
}

.summary-sep {
  opacity: 0.4;
}

/* ── Map canvas ────────────────────────────────────────────── */
.map-canvas {
  position: relative;
  width: 100%;
  height: 420px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}

.map-bg {
  position: absolute;
  inset: 0;
  opacity: 0.3;
}

.grid-line-h {
  position: absolute;
  left: 0;
  right: 0;
  height: 1px;
  background: var(--border);
}

.grid-line-v {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 1px;
  background: var(--border);
}

/* ── GPS pins ──────────────────────────────────────────────── */
.gps-pin {
  position: absolute;
  transform: translate(-50%, -100%);
  cursor: pointer;
  z-index: 2;
  transition: transform 0.15s ease;
}

.gps-pin:hover {
  transform: translate(-50%, -100%) scale(1.2);
  z-index: 5;
}

.pin-icon {
  font-size: 1.5rem;
  filter: drop-shadow(0 2px 4px oklch(0 0 0 / 0.3));
  line-height: 1;
}

.pin-pulse {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--accent);
  opacity: 0.3;
  transform: translate(-50%, -50%);
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.3; }
  50% { transform: translate(-50%, -50%) scale(2); opacity: 0; }
}

/* ── Tooltip ───────────────────────────────────────────────── */
.map-tooltip {
  position: absolute;
  z-index: 10;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: 0 8px 32px oklch(0 0 0 / 0.15);
  display: flex;
  gap: 12px;
  padding: 12px;
  width: 300px;
  pointer-events: none;
}

.tooltip-thumb {
  width: 72px;
  height: 54px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  flex-shrink: 0;
  background: var(--bg);
}

.tooltip-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.tooltip-exif {
  flex: 1;
  min-width: 0;
}

.tooltip-name {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--fg);
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tooltip-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.72rem;
}

.tooltip-table td {
  padding: 1px 4px;
}

.tooltip-table td:first-child {
  color: var(--muted);
  width: 52px;
}

/* ── Fade transition ───────────────────────────────────────── */
.tooltip-fade-enter-active,
.tooltip-fade-leave-active {
  transition: opacity 0.15s ease;
}

.tooltip-fade-enter-from,
.tooltip-fade-leave-to {
  opacity: 0;
}

/* ── Point cards below map ─────────────────────────────────── */
.point-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 8px;
  padding-top: 12px;
}

.point-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}

.point-card:hover {
  border-color: var(--accent);
  background: var(--bg);
}

.point-card.active {
  border-color: var(--accent);
  background: var(--bg);
}

.location-icon {
  font-size: 0.9rem;
  flex-shrink: 0;
}

.coord-text {
  font-size: 0.78rem;
  font-family: monospace;
  color: var(--fg);
}

.card-camera {
  margin-left: auto;
  font-size: 0.72rem;
  color: var(--muted);
  background: var(--bg);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  white-space: nowrap;
}
</style>
