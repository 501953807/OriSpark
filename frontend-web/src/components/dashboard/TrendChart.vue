<template>
  <div class="trend-chart">
    <div v-if="isEmpty" class="chart-empty">暂无数据</div>
    <div v-else class="chart-wrapper">
      <div class="chart-y-axis">
        <span v-for="tick in yTicks" :key="tick" class="tick">{{ tick }}</span>
      </div>
      <svg
        class="chart-svg"
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        :style="{ width: '100%', height: '180px' }"
      >
        <!-- Area gradient -->
        <defs>
          <linearGradient id="trendAreaGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="var(--grad1)" stop-opacity="0.35" />
            <stop offset="100%" stop-color="var(--grad2)" stop-opacity="0.05" />
          </linearGradient>
        </defs>

        <!-- Area fill -->
        <path
          :d="areaPath"
          fill="url(#trendAreaGrad)"
          stroke="none"
        />

        <!-- Line -->
        <polyline
          :points="linePoints"
          fill="none"
          stroke="url(#trendLineGrad)"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
        <!-- Gradient def for polyline (SVG doesn't support CSS vars directly in stroke) -->
        <defs>
          <linearGradient id="trendLineGrad" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stop-color="var(--grad1)" />
            <stop offset="100%" stop-color="var(--grad2)" />
          </linearGradient>
        </defs>

        <!-- Dots at data peaks -->
        <circle
          v-for="(pt, i) in peakPoints"
          :key="'peak-' + i"
          :cx="pt.x"
          :cy="pt.y"
          r="1.5"
          fill="var(--grad1)"
        />
      </svg>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { TrendsSummary } from '@/api/dashboard'

const props = defineProps<{
  data: TrendsSummary | null
}>()

const MAX_POINTS = 30
const INNER_PAD = { x: 6, y: 6 }

const isEmpty = computed(() => !props.data?.daily_trends?.length)

const dataPoints = computed(() => props.data?.daily_trends ?? [])

const maxCount = computed(() => {
  if (!dataPoints.value.length) return 1
  return Math.max(...dataPoints.value.map((d) => d.count), 1)
})

const yTicks = computed(() => {
  const ticks: number[] = []
  const step = niceStep(maxCount.value, 4)
  for (let v = 0; v <= maxCount.value + step; v += step) {
    ticks.push(Math.round(v))
  }
  return ticks
})

const chartPaths = computed(() => {
  const pts = dataPoints.value
  if (!pts.length) return { linePoints: '', areaPath: '', peakPoints: [] as { x: number; y: number }[] }

  const w = 100
  const h = 100

  const xStep = (w - INNER_PAD.x * 2) / Math.max(pts.length - 1, 1)

  const coords = pts.map((d, i) => ({
    x: INNER_PAD.x + i * xStep,
    y: h - INNER_PAD.y - (d.count / maxCount.value) * (h - INNER_PAD.y * 2),
  }))

  const linePoints = coords.map((c) => `${c.x},${c.y}`).join(' ')

  const bottomY = h - INNER_PAD.y
  const areaPath = `M${coords[0].x},${bottomY} ` + coords.map((c) => `L${c.x},${c.y}`).join(' ') + ` L${coords[coords.length - 1].x},${bottomY} Z`

  const peaks: { x: number; y: number }[] = []
  for (let i = 1; i < coords.length - 1; i++) {
    if (coords[i].y < coords[i - 1].y && coords[i].y <= coords[i + 1].y) {
      peaks.push(coords[i])
    }
  }

  return { linePoints, areaPath, peakPoints: peaks }
})

const linePoints = computed(() => chartPaths.value.linePoints)
const areaPath = computed(() => chartPaths.value.areaPath)
const peakPoints = computed(() => chartPaths.value.peakPoints)

function niceStep(maxVal: number, target: number): number {
  const rough = maxVal / target
  const mag = Math.pow(10, Math.floor(Math.log10(rough)))
  const residual = rough / mag
  let nice: number
  if (residual <= 1.5) nice = 1
  else if (residual <= 3) nice = 2
  else if (residual <= 7) nice = 5
  else nice = 10
  return nice * mag
}

defineExpose({ linePoints, areaPath, peakPoints })
</script>

<style scoped>
.trend-chart {
  width: 100%;
  overflow: hidden;
}
.chart-wrapper {
  display: flex;
  gap: 0;
  align-items: stretch;
  min-height: 180px;
}
.chart-y-axis {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding-right: 8px;
  min-width: 32px;
  padding-top: 0;
}
.chart-y-axis .tick {
  font-size: 0.65rem;
  color: var(--muted);
  white-space: nowrap;
}
.chart-svg {
  flex: 1;
}
.chart-empty {
  text-align: center;
  padding: 48px 0;
  color: var(--muted);
  font-size: 0.88rem;
}
</style>
