<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { creditApi } from '@/api/credit'
import type { CreditImprovementResponse } from '@/api/credit'

const userId = ref('local')
const loading = ref(false)
const data = ref<CreditImprovementResponse | null>(null)

const tierLabel = computed(() => {
  if (!data.value?.tier) return '未评级'
  const map: Record<string, string> = {
    newbie: '新手',
    good: '良好',
    excellent: '优秀',
    diamond: '钻石',
  }
  return map[data.value.tier] || data.value.tier
})

const tierColor = computed(() => {
  if (!data.value?.tier) return '#6b7280'
  const map: Record<string, string> = {
    newbie: '#6b7280',
    good: '#10b981',
    excellent: '#3b82f6',
    diamond: '#8b5cf6',
  }
  return map[data.value.tier] || '#6b7280'
})

async function loadSuggestions() {
  loading.value = true
  try {
    const res = await creditApi.getImprovementSuggestions(userId.value)
    data.value = res.data
  } finally {
    loading.value = false
  }
}

onMounted(loadSuggestions)
</script>

<template>
  <div class="credit-improvement-view">
    <h2>信用提升建议</h2>
    <p class="subtitle">基于您的信用评级和行为历史，提供个性化改进建议</p>

    <LoadingSpinner v-if="loading" text="加载中..." />

    <template v-else-if="data">
      <!-- 信用概览 -->
      <div class="overview-card">
        <div class="score-section">
          <div class="score-circle" :style="{ borderColor: tierColor }">
            <div class="score-value">{{ data.current_score ?? '-' }}</div>
            <div class="score-label">当前评分</div>
          </div>
          <div class="tier-badge" :style="{ background: tierColor }">
            {{ tierLabel }}
          </div>
        </div>

        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-val">{{ data.transaction_count }}</div>
            <div class="stat-lbl">交易总数</div>
          </div>
          <div class="stat-item">
            <div class="stat-val">{{ data.successful_transactions }}</div>
            <div class="stat-lbl">成功交易</div>
          </div>
          <div class="stat-item">
            <div class="stat-val">{{ data.dispute_count }}</div>
            <div class="stat-lbl">纠纷次数</div>
          </div>
          <div class="stat-item">
            <div class="stat-val">{{ data.recent_30_days }}</div>
            <div class="stat-lbl">近30天行为</div>
          </div>
        </div>
      </div>

      <!-- 提升建议列表 -->
      <div class="suggestions-section">
        <h3>💡 提升建议</h3>
        <div v-for="(suggestion, idx) in data.suggestions" :key="idx" class="suggestion-card" :class="`priority-${suggestion.priority}`">
          <div class="priority-badge" :class="suggestion.priority">
            {{ suggestion.priority === 'high' ? '高' : suggestion.priority === 'medium' ? '中' : '低' }}
          </div>
          <div class="suggestion-content">
            <h4>{{ suggestion.title }}</h4>
            <p>{{ suggestion.description }}</p>
            <div class="action-tip">
              <strong>建议行动：</strong>{{ suggestion.action }}
            </div>
          </div>
        </div>
      </div>
    </template>

    <div v-else class="empty-state">
      <p>暂无信用评级数据</p>
      <button class="btn-primary" @click="loadSuggestions">重新加载</button>
    </div>
  </div>
</template>

<style scoped>
.credit-improvement-view {
  max-width: 960px;
  margin: 0 auto;
}
.subtitle {
  color: var(--muted);
  font-size: 0.85rem;
  margin-bottom: 24px;
}
.overview-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px;
  margin-bottom: 24px;
}
.score-section {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 24px;
}
.score-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  border: 4px solid var(--border);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.score-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--accent);
}
.score-label {
  font-size: 0.75rem;
  color: var(--muted);
}
.tier-badge {
  padding: 8px 20px;
  border-radius: 20px;
  color: white;
  font-weight: 600;
  font-size: 0.9rem;
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.stat-item {
  text-align: center;
  padding: 16px;
  background: oklch(98% 0.002 240);
  border-radius: var(--radius-sm);
}
.stat-val {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--fg);
}
.stat-lbl {
  font-size: 0.75rem;
  color: var(--muted);
  margin-top: 4px;
}
.suggestions-section {
  margin-top: 24px;
}
.suggestions-section h3 {
  font-size: 1.1rem;
  margin-bottom: 16px;
}
.suggestion-card {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  margin-bottom: 12px;
  border-left: 4px solid var(--border);
}
.suggestion-card.priority-high {
  border-left-color: #dc2626;
}
.suggestion-card.priority-medium {
  border-left-color: #f59e0b;
}
.suggestion-card.priority-low {
  border-left-color: #22c55e;
}
.priority-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}
.priority-badge.high {
  background: #fef2f2;
  color: #dc2626;
}
.priority-badge.medium {
  background: #fffbeb;
  color: #d97706;
}
.priority-badge.low {
  background: #f0fdf4;
  color: #16a34a;
}
.suggestion-content h4 {
  margin: 0 0 8px 0;
  font-size: 0.95rem;
}
.suggestion-content p {
  margin: 0 0 8px 0;
  font-size: 0.85rem;
  color: var(--muted);
}
.action-tip {
  font-size: 0.85rem;
  color: var(--fg);
  padding: 8px 12px;
  background: oklch(98% 0.002 240);
  border-radius: var(--radius-sm);
}
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--muted);
}
.btn-primary {
  background: var(--accent);
  color: white;
  border: none;
  padding: 10px 24px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 0.9rem;
  margin-top: 16px;
}
</style>
