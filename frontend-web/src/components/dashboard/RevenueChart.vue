<template>
  <div class="revenue-chart">
    <div v-if="isEmpty" class="chart-empty">暂无收入数据</div>
    <div v-else class="chart-wrapper">
      <div class="chart-y-axis">
        <span v-for="tick in yTicks" :key="tick" class="tick">{{ formatTick(tick) }}</span>
      </div>
      <div class="chart-area">
        <div
          v-for="(item, idx) in dataPoints"
          :key="idx"
          class="bar"
          :style="{ height: barHeight(item, idx) + '%' }"
          :title="`${item.month}: ¥${item.revenue.toFixed(2)}`"
        />
      </div>
      <div class="chart-x-axis">
        <span
          v-for="(item, idx) in dataPoints"
          :key="idx"
          class="tick"
          :title="item.month"
        >{{ shortenMonth(item.month) }}</span
        >
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { RevenueSummary } from '@/api/dashboard'

const props = defineProps<{
  data: RevenueSummary | null
}>()

const MONTH_LABELS: Record<string, string> = {
  '01': '1月', '02': '2月', '03': '3月', '04': '4月',
  '05': '5月', '06': '6月', '07': '7月', '08': '8月',
  '09': '9月', '10': '10月', '11': '11月', '12': '12月',
}

const isEmpty = computed(() => !props.data?.revenue_by_month?.length)

const dataPoints = computed(() =>
  props.data?.revenue_by_month ?? []
)

const maxRevenue = computed(() => {
  if (!dataPoints.value.length) return 1
  return Math.max(...dataPoints.value.map((d) => d.revenue), 1)
})

const yTicks = computed(() => {
  const ticks: number[] = []
  const step = niceStep(maxRevenue.value, 4)
  for (let v = 0; v <= maxRevenue.value + step; v += step) {
    ticks.push(Math.round(v * 100) / 100)
  }
  return ticks
})

function barHeight(item: { revenue: number }, _idx: number): number {
  if (!maxRevenue.value) return 0
  return (item.revenue / maxRevenue.value) * 100
}

function formatTick(v: number): string {
  if (v >= 1000) return `¥${Math.round(v / 1000)}k`
  if (Number.isInteger(v)) return `¥${v}`
  return `¥${v.toFixed(0)}`
}

function shortenMonth(m: string): string {
  if (m.length === 7) {
    const parts = m.split('-')
    return `${parts[1]}月`
  }
  return m.slice(0, 3)
}

/** Compute a "nice" step given max value and target tick count. */
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
</script>

<style scoped>
.revenue-chart {
  width: 100%;
  overflow-x: auto;
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
  min-width: 40px;
}
.chart-y-axis .tick {
  font-size: 0.65rem;
  color: var(--muted);
  white-space: nowrap;
}
.chart-area {
  flex: 1;
  display: flex;
  align-items: flex-end;
  gap: 4px;
  padding-bottom: 2px;
  min-height: 150px;
}
.bar {
  flex: 1;
  min-width: 20px;
  max-width: 48px;
  border-radius: 4px 4px 0 0;
  background: linear-gradient(to top, var(--grad1), var(--grad2));
  transition: height 0.4s ease;
  position: relative;
  cursor: pointer;
}
.bar:hover {
  opacity: 0.85;
  box-shadow: 0 0 12px oklch(56% 0.12 170 / 0.3);
}
.chart-x-axis {
  display: flex;
  gap: 4px;
  padding-left: 48px;
  margin-top: 4px;
}
.chart-x-axis .tick {
  flex: 1;
  text-align: center;
  font-size: 0.65rem;
  color: var(--muted);
}
.chart-empty {
  text-align: center;
  padding: 48px 0;
  color: var(--muted);
  font-size: 0.88rem;
}
</style>
