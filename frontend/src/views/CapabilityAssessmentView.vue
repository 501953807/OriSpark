<template>
  <div class="capability-view">
    <LoadingSpinner v-if="store.loading" text="加载中..." />
    <template v-else>
      <h2>创作者能力评估</h2>
      <p class="subtitle">8 维能力雷达图 · 技能溢价 · AI 护城河</p>

      <!-- 评估表单 -->
      <div class="section">
        <h3>能力自评</h3>
        <div class="dimension-sliders">
          <div v-for="dim in store.dimensions" :key="dim.dimension_key" class="dim-row">
            <label class="dim-label">{{ dim.name_zh }}</label>
            <input
              type="range"
              min="0"
              max="100"
              v-model.number="scores[dim.dimension_key]"
            />
            <span class="dim-score">{{ scores[dim.dimension_key] }}</span>
          </div>
        </div>
        <button class="btn-primary" @click="runAssessment">生成评估报告</button>
      </div>

      <!-- 评估结果 -->
      <div v-if="result" class="section result-section">
        <div class="score-header">
          <span class="overall-label">综合评分</span>
          <span class="overall-value">{{ result.overall_score }}</span>
        </div>

        <!-- 技能溢价 -->
        <div class="premium-card">
          <h4>技能组合溢价</h4>
          <div class="premium-value">+{{ result.skill_premium_percent }}%</div>
        </div>

        <!-- AI 风险 -->
        <div class="ai-risk-card" :class="'risk-' + result.ai_risk_level">
          <h4>AI 替代风险</h4>
          <div class="risk-badge">{{ riskLabel(result.ai_risk_level) }}</div>
          <p>{{ result.ai_risk_description }}</p>
        </div>

        <!-- 阶段推荐 -->
        <div v-if="stageRec" class="stage-card">
          <h4>当前阶段</h4>
          <div class="stage-name">{{ stageRec.stage_name_zh }}</div>
        </div>
      </div>

      <!-- 雷达图可视化 -->
      <div v-if="result && result.dimension_scores" class="section">
        <h3>能力雷达图</h3>
        <div class="radar-container">
          <canvas ref="radarCanvas" width="400" height="400"></canvas>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, watch } from 'vue'
import { useCapabilityStore } from '@/stores/useCapabilityStore'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const store = useCapabilityStore()
const scores = ref<Record<string, number>>({})
const result = ref<any>(null)
const stageRec = ref<any>(null)
const radarCanvas = ref<HTMLCanvasElement | null>(null)

async function runAssessment() {
  const r = await store.submitAssessment(scores.value)
  result.value = r

  const stage = await store.checkStage(r.overall_score ?? 0)
  stageRec.value = stage

  // Draw radar after DOM update
  await nextTick()
  drawRadar(r.dimension_scores)
}

function riskLabel(level: string): string {
  return { low: '低', medium: '中', high: '高', unknown: '未知' }[level] || level
}

function drawRadar(dimScores: Record<string, number>) {
  const canvas = radarCanvas.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const dims = store.dimensions.filter(d => d.dimension_key in dimScores)
  const n = dims.length
  if (n === 0) return

  const cx = 200, cy = 200, maxR = 160
  const angleStep = (Math.PI * 2) / n

  ctx.clearRect(0, 0, 400, 400)

  // Grid circles
  for (let ring = 1; ring <= 5; ring++) {
    const r = (maxR / 5) * ring
    ctx.beginPath()
    for (let i = 0; i <= n; i++) {
      const angle = i * angleStep - Math.PI / 2
      const x = cx + r * Math.cos(angle)
      const y = cy + r * Math.sin(angle)
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
    }
    ctx.strokeStyle = '#e5e7eb'
    ctx.stroke()
  }

  // Axes and labels
  dims.forEach((dim, i) => {
    const angle = i * angleStep - Math.PI / 2
    const x = cx + maxR * Math.cos(angle)
    const y = cy + maxR * Math.sin(angle)

    ctx.beginPath()
    ctx.moveTo(cx, cy)
    ctx.lineTo(x, y)
    ctx.strokeStyle = '#d1d5db'
    ctx.stroke()

    // Label
    const lx = cx + (maxR + 20) * Math.cos(angle)
    const ly = cy + (maxR + 20) * Math.sin(angle)
    ctx.fillStyle = '#374151'
    ctx.font = '11px sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(dim.name_zh, lx, ly)
  })

  // Data polygon
  ctx.beginPath()
  dims.forEach((dim, i) => {
    const score = dimScores[dim.dimension_key] / 100
    const angle = i * angleStep - Math.PI / 2
    const r = maxR * score
    const x = cx + r * Math.cos(angle)
    const y = cy + r * Math.sin(angle)
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
  })
  ctx.closePath()
  ctx.fillStyle = 'rgba(99, 102, 241, 0.2)'
  ctx.fill()
  ctx.strokeStyle = '#6366f1'
  ctx.lineWidth = 2
  ctx.stroke()

  // Data points
  dims.forEach((dim, i) => {
    const score = dimScores[dim.dimension_key] / 100
    const angle = i * angleStep - Math.PI / 2
    const x = cx + maxR * score * Math.cos(angle)
    const y = cy + maxR * score * Math.sin(angle)
    ctx.beginPath()
    ctx.arc(x, y, 4, 0, Math.PI * 2)
    ctx.fillStyle = '#6366f1'
    ctx.fill()
  })
}

// Init
store.loadDimensions()
</script>

<style scoped>
.capability-view {
  max-width: 800px;
  margin: 0 auto;
}
h2 { font-size: 1.4rem; margin-bottom: 4px; }
.subtitle { color: var(--muted); font-size: 0.85rem; margin-bottom: 24px; }

.section {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  margin-bottom: 16px;
}
h3 { margin-top: 0; font-size: 1rem; }

.dimension-sliders { display: grid; gap: 12px; margin-bottom: 16px; }
.dim-row {
  display: flex;
  align-items: center;
  gap: 12px;
}
.dim-label {
  width: 100px;
  font-size: 0.85rem;
  flex-shrink: 0;
}
.dim-row input[type="range"] {
  flex: 1;
}
.dim-score {
  width: 32px;
  text-align: right;
  font-weight: 700;
  font-size: 0.9rem;
}

.btn-primary {
  background: var(--accent);
  color: white;
  border: none;
  padding: 10px 24px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 0.95rem;
}

.result-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.score-header {
  grid-column: 1 / -1;
  text-align: center;
  padding: 16px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-radius: var(--radius);
  color: white;
}
.overall-label { display: block; font-size: 0.85rem; opacity: 0.9; }
.overall-value { font-size: 2.5rem; font-weight: 800; }

.premium-card, .ai-risk-card, .stage-card {
  padding: 16px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  text-align: center;
}
.premium-value {
  font-size: 1.5rem;
  font-weight: 800;
  color: #22c55e;
}
.risk-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 700;
  margin: 8px 0;
}
.risk-low { background: #dcfce7; color: #166534; }
.risk-medium { background: #fef3c7; color: #92400e; }
.risk-high { background: #fee2e2; color: #991b1b; }

.radar-container {
  display: flex;
  justify-content: center;
  padding: 16px;
}
</style>
