// src/components/EChartsBar3D.vue
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import VChart from 'vue-echarts'
import * as echarts from 'echarts'
// Register echarts-gl for 3D capabilities
import 'echarts-gl'
const chartRef = ref(null)

// Sample data - in real app this would come from API
const chartData = [
  { name: '作品A', value: 85 },
  { name: '作品B', value: 62 },
  { name: '作品C', value: 95 },
  { name: '作品D', value: 48 },
  { name: '作品E', value: 73 },
]

let chartInstance: echarts.ECharts | null = null

// Initialize 3D bar chart option
const getChartOption = () => ({
  visualMap: {
    show: false,
    min: 0,
    max: 100,
    inRange: {
      color: ['#0ea5e9', '#3b82f6']
    }
  },
  xAxis3D: {
    type: 'category',
    data: chartData.map(d => d.name),
    axisLabel: {
      color: '#9ca3af',
      fontSize: 12
    }
  },
  yAxis3D: {
    type: 'value',
    name: '数量',
    axisLabel: {
      color: '#9ca3af',
      fontSize: 12
    }
  },
  zAxis3D: {
    type: 'value',
    name: '深度',
    axisLabel: {
      color: '#9ca3af',
      fontSize: 12
    }
  },
  series: [{
    type: 'bar3D',
    data: chartData.map(d => ({
      value: [d.value, 0, d.value], // x, y, z coordinates for 3D bar
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#0ea5e9' },
          { offset: 1, color: '#3b82f6' }
        ])
      }
    })),
    shading: 'color',
    label: {
      show: true,
      position: 'inside',
      formatter: '{c}',
      color: '#fff',
      fontSize: 11,
      fontWeight: 'bold'
    },
    emphasis: {
      focus: 'series',
      itemStyle: {
        color: '#60a5fa'
      }
    },
    barsWidth: 0.5
  }],
  grid: {
    containLabel: true
  },
  tooltip: {
    trigger: 'item',
    formatter: (params: any) => `${params.value[0]}: ${params.value[2]}`
  }
})

const updateChart = () => {
  if (!chartInstance) return
  const options = getChartOption()
  chartInstance.setOption(options, true)
}

onMounted(() => {
  chartInstance = echarts.init(chartRef.value as unknown as HTMLElement)
  updateChart()

  // Responsive resize handler
  const handleResize = () => {
    if (chartInstance) chartInstance.resize()
  }
  window.addEventListener('resize', handleResize)
  onBeforeUnmount(() => {
    window.removeEventListener('resize', handleResize)
    if (chartInstance) {
      chartInstance.dispose()
      chartInstance = null
    }
  })
})

watch(() => false, () => {
  // Animation controls removed
})

defineExpose({
  refresh: () => {
    if (chartInstance) {
      chartInstance.setOption(getChartOption(), true)
    }
  }
})
</script>

<template>
  <div class="echarts-3d-container">
    <VChart
      ref="chartRef"
      :option="getChartOption()"
      autoresize
      style="height: 400px; border-radius: 12px; background: white;"
    />
  </div>
</template>

<style scoped>
.echarts-3d-container {
  padding: 1rem;
}

@media (prefers-reduced-motion: reduce) {
  .echarts-3d-container {
    animation: none !important;
  }
}
</style>
