<template>
  <div class="mockup-container">
    <div class="mockup-toolbar">
      <div class="color-switcher">
        <button v-for="c in colors" :key="c.value" :class="['color-btn', { active: currentColor === c.value }]" :style="{ background: c.hex }" @click="switchColor(c.value)" :title="c.label"></button>
      </div>
      <div class="zoom-controls">
        <button class="btn btn-sm" @click="zoomOut" :disabled="zoom <= 0.5" title="缩小">−</button>
        <span class="zoom-label">{{ Math.round(zoom * 100) }}%</span>
        <button class="btn btn-sm" @click="zoomIn" :disabled="zoom >= 3" title="放大">+</button>
        <button class="btn btn-sm" @click="resetPosition" title="重置">↺</button>
      </div>
    </div>
    <div class="canvas-area" ref="canvasAreaRef" @wheel.prevent="onWheel">
      <canvas ref="canvasRef" :width="canvasWidth" :height="canvasHeight" @mousedown="onMouseDown" @mousemove="onMouseMove" @mouseup="onMouseUp" @mouseleave="onMouseUp"></canvas>
    </div>
    <div class="mockup-footer">
      <span class="mockup-note">⚠️ 平面效果预览，非真实产品照片。以POD平台实际效果为准。</span>
      <div class="mockup-actions">
        <button class="btn btn-secondary btn-sm" @click="resetPosition">重置位置</button>
        <button class="btn btn-primary btn-sm" @click="exportMockup">导出效果图</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'

const props = withDefaults(defineProps<{
  templateUrl?: string; designUrl?: string; overlayUrl?: string
  colors?: Array<{ value: string; hex: string; label: string }>
  printArea?: { x: number; y: number; w: number; h: number }
}>(), {
  colors: () => [{ value: 'white', hex: '#ffffff', label: '白色' }, { value: 'black', hex: '#2d2d2d', label: '黑色' }, { value: 'gray', hex: '#b0b0b0', label: '灰色' }],
  printArea: () => ({ x: 150, y: 80, w: 200, h: 240 }),
})

const emit = defineEmits<{ export: [blob: Blob]; update: [data: { x: number; y: number; scale: number; color: string }] }>()

const canvasRef = ref<HTMLCanvasElement>(); const canvasAreaRef = ref<HTMLElement>()
const canvasWidth = ref(500); const canvasHeight = ref(550)
const currentColor = ref(props.colors[0]?.value || 'white')
const zoom = ref(1); const offsetX = ref(props.printArea.x); const offsetY = ref(props.printArea.y)
const dragging = ref(false); const dragStartX = ref(0); const dragStartY = ref(0)
let templateImg: HTMLImageElement | null = null; let designImg: HTMLImageElement | null = null; let overlayImg: HTMLImageElement | null = null

onMounted(async () => { await loadImages(); render() })
watch(currentColor, () => render())

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => { const img = new Image(); img.crossOrigin = 'anonymous'; img.onload = () => resolve(img); img.onerror = reject; img.src = src })
}
async function loadImages() {
  try { if (props.templateUrl) templateImg = await loadImage(props.templateUrl); if (props.designUrl) designImg = await loadImage(props.designUrl); if (props.overlayUrl) overlayImg = await loadImage(props.overlayUrl); render() } catch { /* ignore */ }
}
function render() {
  const canvas = canvasRef.value; if (!canvas) return; const ctx = canvas.getContext('2d'); if (!ctx) return
  const pa = props.printArea; ctx.clearRect(0, 0, canvas.width, canvas.height)
  const colorObj = props.colors.find(c => c.value === currentColor.value); ctx.fillStyle = colorObj?.hex || '#ffffff'; ctx.fillRect(0, 0, canvas.width, canvas.height)
  if (templateImg) ctx.drawImage(templateImg, 0, 0, canvas.width, canvas.height)
  ctx.save(); ctx.beginPath(); ctx.strokeStyle = '#5b5fe3'; ctx.lineWidth = 1; ctx.setLineDash([4, 4]); ctx.rect(pa.x, pa.y, pa.w, pa.h); ctx.stroke(); ctx.restore()
  if (designImg) { const scaledW = pa.w * zoom.value; const scaledH = designImg.height * (scaledW / designImg.width); ctx.drawImage(designImg, offsetX.value, offsetY.value, scaledW, scaledH) }
  if (overlayImg) { ctx.globalAlpha = 0.35; ctx.drawImage(overlayImg, pa.x, pa.y, pa.w, pa.h); ctx.globalAlpha = 1 }
}
function switchColor(val: string) { currentColor.value = val }
function zoomIn() { zoom.value = Math.min(3, zoom.value + 0.25); render() }
function zoomOut() { zoom.value = Math.max(0.5, zoom.value - 0.25); render() }
function resetPosition() { zoom.value = 1; offsetX.value = props.printArea.x; offsetY.value = props.printArea.y; render() }
function onWheel(e: WheelEvent) { const delta = e.deltaY > 0 ? -0.1 : 0.1; zoom.value = Math.max(0.5, Math.min(3, zoom.value + delta)); render() }
function onMouseDown(e: MouseEvent) { dragging.value = true; dragStartX.value = e.clientX - offsetX.value; dragStartY.value = e.clientY - offsetY.value }
function onMouseMove(e: MouseEvent) { if (!dragging.value) return; offsetX.value = e.clientX - dragStartX.value; offsetY.value = e.clientY - dragStartY.value; render() }
function onMouseUp() { if (dragging.value) { dragging.value = false; emit('update', { x: offsetX.value, y: offsetY.value, scale: zoom.value, color: currentColor.value }) } }
function exportMockup() { const canvas = canvasRef.value; if (!canvas) return; canvas.toBlob(blob => { if (blob) emit('export', blob) }, 'image/png') }
</script>

<style scoped>
.mockup-container { display: flex; flex-direction: column; gap: 12px; }
.mockup-toolbar { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
.color-switcher { display: flex; gap: 6px; }
.color-btn { width: 28px; height: 28px; border-radius: 50%; border: 2px solid var(--border); cursor: pointer; transition: all .15s; }
.color-btn.active { border-color: var(--accent); box-shadow: 0 0 0 2px oklch(56% 0.12 170 / .25); }
.zoom-controls { display: flex; align-items: center; gap: 6px; }
.zoom-label { font-size: 0.82rem; color: var(--muted); min-width: 40px; text-align: center; }
.canvas-area { display: flex; justify-content: center; overflow: hidden; border: 1px solid var(--border); border-radius: 8px; background: var(--surface); }
.mockup-footer { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.mockup-note { font-size: 0.74rem; color: var(--orange); }
.mockup-actions { display: flex; gap: 8px; }
.btn { padding: 6px 12px; border-radius: 6px; font-size: 0.82rem; cursor: pointer; border: none; font-family: inherit; }
.btn-sm { padding: 4px 10px; font-size: 0.78rem; }
.btn-primary { background: var(--accent); color: #fff; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-secondary { background: var(--surface); color: var(--text-primary); border: 1px solid var(--border); }
</style>
