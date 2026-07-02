<template>
  <div class="exif-panel">
    <!-- Camera & Lens -->
    <section class="info-group" v-if="cameraModel || lens">
      <h4 class="info-group-title">器材</h4>
      <div class="info-row" v-if="cameraModel">
        <span class="info-label">相机</span>
        <span class="info-value">{{ cameraModel }}</span>
      </div>
      <div class="info-row" v-if="lens">
        <span class="info-label">镜头</span>
        <span class="info-value">{{ lens }}</span>
      </div>
    </section>

    <!-- Exposure Settings -->
    <section class="info-group" v-if="exifGroup.exposure.length">
      <h4 class="info-group-title">曝光参数</h4>
      <div v-for="item in exifGroup.exposure" :key="item.label" class="info-row">
        <span class="info-label">{{ item.label }}</span>
        <span class="info-value">{{ item.value }}</span>
      </div>
    </section>

    <!-- Composition -->
    <section class="info-group" v-if="exifGroup.composition.length">
      <h4 class="info-group-title">构图信息</h4>
      <div v-for="item in exifGroup.composition" :key="item.label" class="info-row">
        <span class="info-label">{{ item.label }}</span>
        <span class="info-value">{{ item.value }}</span>
      </div>
    </section>

    <!-- Color & Quality -->
    <section class="info-group" v-if="exifGroup.color.length">
      <h4 class="info-group-title">色彩与画质</h4>
      <div v-for="item in exifGroup.color" :key="item.label" class="info-row">
        <span class="info-label">{{ item.label }}</span>
        <span class="info-value">{{ item.value }}</span>
      </div>
    </section>

    <!-- Location -->
    <section class="info-group" v-if="exifGroup.location.length">
      <h4 class="info-group-title">拍摄位置</h4>
      <div v-for="item in exifGroup.location" :key="item.label" class="info-row">
        <span class="info-label">{{ item.label }}</span>
        <span class="info-value">{{ item.value }}</span>
      </div>
    </section>

    <!-- Time -->
    <section class="info-group" v-if="exifGroup.time.length">
      <h4 class="info-group-title">时间信息</h4>
      <div v-for="item in exifGroup.time" :key="item.label" class="info-row">
        <span class="info-label">{{ item.label }}</span>
        <span class="info-value">{{ item.value }}</span>
      </div>
    </section>

    <!-- Empty state -->
    <div v-if="!hasAnyExif" class="empty-hint">
      <span class="hint-icon">&#128247;</span>
      <p>暂无 EXIF 数据</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Work } from '@/types/work'

// ------------------------------------------------------------------
// Prop types
// ------------------------------------------------------------------
interface Props {
  work: Work | null
  exifData: Record<string, any> | null
}

const props = withDefaults(defineProps<Props>(), {
  work: null,
  exifData: null,
})

// ------------------------------------------------------------------
// Derived EXIF values — normalize from work.exif_data first,
// then fall back to work.custom_metadata.exif
// ------------------------------------------------------------------
const raw = computed(() => {
  if (props.exifData && typeof props.exifData === 'object') return props.exifData
  if (props.work?.custom_metadata?.exif && typeof props.work.custom_metadata.exif === 'object')
    return props.work.custom_metadata.exif
  return null
})

const cameraModel = computed(() => raw.value?.camera || raw.value?.camera_model || raw.value?.Camera || null)
const lens = computed(() => raw.value?.lens || raw.value?.Lens || null)
const iso = computed(() => raw.value?.ISO || raw.value?.iso || null)
const aperture = computed(() => raw.value?.Aperture || raw.value?.aperture || raw.value?.FNumber || null)
const shutterSpeed = computed(() => raw.value?.ShutterSpeed || raw.value?.shutter_speed || raw.value?.ExposureTime || null)
const focalLength = computed(() => raw.value?.FocalLength || raw.value?.focal_length || null)
const flash = computed(() => raw.value?.Flash || raw.value?.flash || null)
const exposureProgram = computed(() => raw.value?.ExposureProgram || raw.value?.exposure_program || null)
const meteringMode = computed(() => raw.value?.MeteringMode || raw.value?.metering_mode || null)
const whiteBalance = computed(() => raw.value?.WhiteBalance || raw.value?.white_balance || raw.value?.WB || null)
const histogram = computed(() => raw.value?.histogram || raw.value?.Histogram || null)
const latitude = computed(() => raw.value?.GPSLatitude || raw.value?.gps_latitude || raw.value?.latitude || null)
const longitude = computed(() => raw.value?.GPSLongitude || raw.value?.gps_longitude || raw.value?.longitude || null)
const altitude = computed(() => raw.value?.GPSAltitude || raw.value?.gps_altitude || raw.value?.altitude || null)
const dateTimeOriginal = computed(() => raw.value?.DateTimeOriginal || raw.value?.date_time_original || raw.value?.DateTime || null)
const digitizeDate = computed(() => raw.value?.DigitizeDate || raw.value?.digitize_date || null)
const software = computed(() => raw.value?.Software || raw.value?.software || null)
const maker = computed(() => raw.value?.Maker || raw.value?.maker || raw.value?.Make || null)

// ------------------------------------------------------------------
// Grouped display entries
// ------------------------------------------------------------------
function fmt(val: string | number | null | undefined): string {
  if (val == null || val === '') return '—'
  return String(val)
}

const exposureGroup = computed(() => {
  const items: Array<{ label: string; value: string }> = []
  if (iso.value) items.push({ label: 'ISO', value: fmt(iso.value) })
  if (aperture.value) items.push({ label: '光圈', value: fmt(aperture.value) })
  if (shutterSpeed.value) items.push({ label: '快门', value: fmt(shutterSpeed.value) })
  if (exposureProgram.value) items.push({ label: '曝光模式', value: fmt(exposureProgram.value) })
  if (meteringMode.value) items.push({ label: '测光', value: fmt(meteringMode.value) })
  if (flash.value) items.push({ label: '闪光灯', value: fmt(flash.value) })
  return items
})

const compositionGroup = computed(() => {
  const items: Array<{ label: string; value: string }> = []
  if (focalLength.value) items.push({ label: '焦距', value: fmt(focalLength.value) })
  const w = props.work?.width
  const h = props.work?.height
  if (w && h) items.push({ label: '分辨率', value: `${w} x ${h}` })
  return items
})

const colorGroup = computed(() => {
  const items: Array<{ label: string; value: string }> = []
  if (whiteBalance.value) items.push({ label: '白平衡', value: fmt(whiteBalance.value) })
  if (histogram.value) items.push({ label: '直方图', value: fmt(histogram.value) })
  return items
})

const locationGroup = computed(() => {
  const items: Array<{ label: string; value: string }> = []
  if (latitude.value != null && longitude.value != null) {
    const latVal = typeof latitude.value === 'number'
      ? latitude.value
      : parseFloat(String(latitude.value))
    const lonVal = typeof longitude.value === 'number'
      ? longitude.value
      : parseFloat(String(longitude.value))
    if (!isNaN(latVal) && !isNaN(lonVal)) {
      items.push({ label: '经纬度', value: `${latVal.toFixed(4)}, ${lonVal.toFixed(4)}` })
    }
  }
  if (altitude.value) items.push({ label: '海拔', value: fmt(altitude.value) })
  return items
})

const timeGroup = computed(() => {
  const items: Array<{ label: string; value: string }> = []
  if (dateTimeOriginal.value) items.push({ label: '拍摄时间', value: fmt(dateTimeOriginal.value) })
  if (digitizeDate.value) items.push({ label: '数字化日期', value: fmt(digitizeDate.value) })
  if (software.value) items.push({ label: '软件', value: fmt(software.value) })
  return items
})

const exifGroup = computed(() => ({
  exposure: exposureGroup.value,
  composition: compositionGroup.value,
  color: colorGroup.value,
  location: locationGroup.value,
  time: timeGroup.value,
}))

// ------------------------------------------------------------------
// Computed display helpers
// ------------------------------------------------------------------
const hasAnyExif = computed(() => {
  return !!(
    cameraModel.value ||
    lens.value ||
    iso.value ||
    aperture.value ||
    shutterSpeed.value ||
    focalLength.value ||
    flash.value ||
    exposureProgram.value ||
    meteringMode.value ||
    whiteBalance.value ||
    histogram.value ||
    (latitude.value != null && longitude.value != null) ||
    altitude.value ||
    dateTimeOriginal.value ||
    digitizeDate.value ||
    software.value ||
    maker.value
  )
})
</script>

<style scoped>
.empty-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  color: var(--muted);
  gap: 8px;
}

.hint-icon {
  font-size: 2rem;
  opacity: 0.6;
}

/* Re-export the info-group styles that match WorkDetailView */
.info-group {
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
}

.info-group:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.info-group-title {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--accent);
  margin: 0 0 10px 0;
}

.info-row {
  display: flex;
  align-items: baseline;
  gap: 12px;
  font-size: 0.85rem;
  margin-bottom: 6px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-label {
  color: var(--muted);
  font-weight: 600;
  font-size: 0.8rem;
  min-width: 60px;
  flex-shrink: 0;
}

.info-value {
  color: var(--fg);
  font-size: 0.85rem;
  word-break: break-word;
}
</style>
