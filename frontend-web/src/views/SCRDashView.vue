<template>
  <div class="scr-dash">
    <n-card title="SCR 分布式信誉系统">
      <!-- Score gauge -->
      <div class="score-section">
        <ScoreGauge :score="score?.overall_score ?? 50" />
        <div class="rating-info">
          <RatingBadge :level="score?.rating_level || 'starter'" />
          <div class="score-detail">
            <span>用户 {{ score?.user_id?.slice(0, 8) }}</span>
            <span>平均响应 {{ score?.avg_response_hours ?? 24 }}h</span>
          </div>
        </div>
      </div>

      <!-- Stats cards -->
      <div class="stats-grid">
        <div class="stat-card positive">
          <div class="stat-value">{{ score?.fulfillment_count ?? 0 }}</div>
          <div class="stat-label">成功履约</div>
        </div>
        <div class="stat-card negative">
          <div class="stat-value">{{ score?.default_count ?? 0 }}</div>
          <div class="stat-label">违约次数</div>
        </div>
        <div class="stat-card neutral">
          <div class="stat-value">{{ score?.late_review_count ?? 0 }}</div>
          <div class="stat-label">迟评</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-value">{{ score?.complaint_count ?? 0 }}</div>
          <div class="stat-label">投诉</div>
        </div>
        <div class="stat-card info">
          <div class="stat-value">{{ score?.cleared_count ?? 0 }}</div>
          <div class="stat-label">申诉清除</div>
        </div>
      </div>

      <!-- Tabs: history + leaderboard -->
      <n-tabs type="segment">
        <n-tab-pane name="history" tab="历史记录">
          <div v-if="history.length === 0" class="empty-state">暂无记录</div>
          <div v-else class="history-list">
            <div v-for="h in history" :key="h.id" class="history-item">
              <span :class="['delta', h.score_delta > 0 ? 'up' : 'down']">
                {{ h.score_delta > 0 ? '+' : '' }}{{ h.score_delta }}
              </span>
              <span class="reason">{{ reasonLabel(h.reason) }}</span>
              <span class="time">{{ formatDate(h.created_at) }}</span>
            </div>
          </div>
        </n-tab-pane>
        <n-tab-pane name="leaderboard" tab="排行榜">
          <div v-if="leaderboard.length === 0" class="empty-state">加载中...</div>
          <div v-else class="lb-table">
            <div v-for="(entry, idx) in leaderboard" :key="entry.user_id" class="lb-row">
              <span class="lb-rank">#{{ idx + 1 }}</span>
              <span class="lb-user">{{ entry.user_id.slice(0, 8) }}</span>
              <span class="lb-score">{{ entry.overall_score }}</span>
              <n-tag size="small">{{ entry.rating_level }}</n-tag>
            </div>
          </div>
        </n-tab-pane>
      </n-tabs>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NTabs, NTabPane, NTag } from 'naive-ui'
import type { SCRScore, SCRAuditLog, LeaderboardEntry } from '@/types/scr'
import { scrApi } from '@/api/scr'
import ScoreGauge from '@/components/scr/ScoreGauge.vue'
import RatingBadge from '@/components/scr/RatingBadge.vue'

const score = ref<SCRScore | null>(null)
const history = ref<SCRAuditLog[]>([])
const leaderboard = ref<LeaderboardEntry[]>([])

async function load() {
  try {
    const userScore = await scrApi.getScore('test-user-001')
    score.value = userScore.data.data
  } catch { /* silent */ }
  try {
    const resp = await scrApi.getHistory('test-user-001')
    history.value = resp.data.data || []
  } catch { /* silent */ }
  try {
    const resp = await scrApi.getLeaderboard(20)
    leaderboard.value = resp.data.data || []
  } catch { /* silent */ }
}

function reasonLabel(r: string): string {
  const map: Record<string, string> = {
    fulfillment: '履约', default: '违约', late_review: '迟评', complaint: '投诉', cleared: '申诉清除',
  }
  return map[r] || r
}

function formatDate(iso?: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  return `${d.getMonth()+1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
}

onMounted(load)
</script>

<style scoped>
.scr-dash { display: flex; flex-direction: column; gap: 16px; }

.score-section {
  display: flex; align-items: center; gap: 24px;
  padding: 24px; background: var(--bg); border-radius: var(--radius);
}

.rating-info { display: flex; flex-direction: column; gap: 8px; }

.score-detail { display: flex; gap: 16px; font-size: 0.82rem; color: var(--muted); }

.stats-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
}

.stat-card {
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  padding: 16px; background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius);
}

.stat-value { font-size: 1.5rem; font-weight: 700; font-family: var(--font-display); }
.stat-label { font-size: 0.78rem; color: var(--muted); }

.stat-card.positive .stat-value { color: #16a34a; }
.stat-card.negative .stat-value { color: #ef4444; }
.stat-card.warning .stat-value { color: #ea580c; }
.stat-card.info .stat-value { color: #2563eb; }
.stat-card.neutral .stat-value { color: var(--fg); }

.history-list { display: flex; flex-direction: column; gap: 6px; }

.history-item {
  display: flex; align-items: center; gap: 12px;
  padding: 8px 12px; background: var(--bg); border-radius: var(--radius-sm);
  font-size: 0.84rem;
}

.delta { font-weight: 700; font-family: monospace; min-width: 50px; }
.delta.up { color: #16a34a; }
.delta.down { color: #ef4444; }
.reason { flex: 1; }
.time { color: var(--muted); font-size: 0.78rem; }

.lb-table { display: flex; flex-direction: column; gap: 4px; }

.lb-row {
  display: flex; align-items: center; gap: 12px;
  padding: 8px 12px; background: var(--bg); border-radius: var(--radius-sm);
  font-size: 0.84rem;
}

.lb-rank { font-weight: 700; color: var(--muted); min-width: 40px; }
.lb-user { flex: 1; }
.lb-score { font-weight: 700; font-family: monospace; }

.empty-state { padding: 24px; text-align: center; color: var(--muted); }
</style>
