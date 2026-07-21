<template>
  <div class="revenue-charts">
    <div class="chart-card card" v-if="showChart">
      <h3>📊 按平台收入</h3>
      <div ref="platformChartRef" style="height:260px"></div>
    </div>
    <div class="chart-card card" v-if="showChart">
      <h3>📈 月度趋势</h3>
      <div ref="monthChartRef" style="height:260px"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps<{
  revenues: Array<{ platform: string; amount: number; date: string; order_count: number }>
}>()

const showChart = ref(false)
const platformChartRef = ref<HTMLElement>()
const monthChartRef = ref<HTMLElement>()
let platformChart: echarts.ECharts | null = null
let monthChart: echarts.ECharts | null = null

function buildPlatformChart() {
  if (!platformChartRef.value) return
  if (platformChart) platformChart.dispose()
  platformChart = echarts.init(platformChartRef.value)

  const byPlatform: Record<string, number> = {}
  props.revenues.forEach(r => {
    byPlatform[r.platform] = (byPlatform[r.platform] || 0) + r.amount
  })

  platformChart.setOption({
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: ['45%', '75%'],
      itemStyle: {
        borderRadius: 8,
        borderColor: 'oklch(100% 0 0)',
        borderWidth: 2,
      },
      data: Object.entries(byPlatform).map(([name, value]) => ({ name, value })),
      label: { show: true, formatter: '{b}\n¥{c}' },
      emphasis: {
        label: { fontSize: 16, fontWeight: 'bold' },
      },
    }],
  })
}

function buildMonthChart() {
  if (!monthChartRef.value) return
  if (monthChart) monthChart.dispose()
  monthChart = echarts.init(monthChartRef.value)

  const byMonth: Record<string, number> = {}
  props.revenues.forEach(r => {
    const month = r.date?.slice(0, 7) || 'unknown'
    byMonth[month] = (byMonth[month] || 0) + r.amount
  })

  const months = Object.keys(byMonth).sort()
  const values = months.map(m => byMonth[m])

  monthChart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: months, axisLabel: { fontSize: 11 } },
    yAxis: { type: 'value', axisLabel: { formatter: '¥{value}' } },
    series: [{
      type: 'bar',
      data: values,
      itemStyle: {
        borderRadius: [6, 6, 0, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'oklch(56% 0.12 170)' },
          { offset: 1, color: 'oklch(62% 0.16 260)' },
        ]),
      },
    }],
    grid: { top: 10, right: 10, bottom: 20, left: 50 },
  })
}

watch(() => props.revenues, async () => {
  await nextTick()
  if (props.revenues.length) {
    showChart.value = true
    await nextTick()
    buildPlatformChart()
    buildMonthChart()
  }
}, { immediate: true, deep: true })

onMounted(() => {
  if (props.revenues.length) {
    showChart.value = true
    setTimeout(() => { buildPlatformChart(); buildMonthChart() }, 100)
  }
})
</script>

<style scoped>
.revenue-charts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-top: 16px;
}
@media (max-width: 768px) { .revenue-charts { grid-template-columns: 1fr; } }
.chart-card { padding: 20px; }
.chart-card h3 { font-size: .9rem; margin: 0 0 12px; }
</style>
