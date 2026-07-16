<template>
  <div class="growth-stage-view">
    <LoadingSpinner v-if="store.loading" text="加载中..." />
    <template v-else-if="store.dashboard">
      <h2>创作者成长阶段</h2>
      <p class="subtitle">自动评估 · 任务清单 · 进度追踪</p>

      <!-- 当前阶段卡片 -->
      <div class="stage-card">
        <div class="stage-header">
          <span class="stage-badge">{{ store.dashboard.current_stage.name_zh }}</span>
          <span class="stage-progress-text">{{ store.dashboard.progress_percent }}%</span>
        </div>
        <p class="stage-desc">{{ store.dashboard.current_stage.description_zh }}</p>

        <!-- 进度条 -->
        <div class="progress-bar-container">
          <div class="progress-bar" :style="{ width: store.dashboard.progress_percent + '%' }"></div>
        </div>

        <!-- 解锁功能 -->
        <div class="unlock-features">
          <strong>已解锁：</strong>
          <span v-for="f in store.dashboard.current_stage.unlock_features" :key="f" class="feature-tag">{{ f }}</span>
        </div>

        <!-- 距下一阶段 -->
        <div v-if="store.dashboard.next_stage" class="next-stage">
          <strong>→ 下一阶段：{{ store.dashboard.next_stage.name_zh }}</strong>
          <div class="remaining">
            <span>收入差距 ¥{{ store.dashboard.remaining_to_next.monthly_revenue_gap.toLocaleString() }}/月</span>
            <span>作品还需 {{ store.dashboard.remaining_to_next.works_needed }} 件</span>
            <span>存证还需 {{ store.dashboard.remaining_to_next.certs_needed }} 个</span>
          </div>
        </div>
      </div>

      <!-- 任务清单 -->
      <div class="tasks-section">
        <h3>本阶段任务（{{ store.dashboard.completed_tasks }}/{{ store.dashboard.total_tasks }}）</h3>
        <div v-for="(task, i) in store.dashboard.tasks" :key="i" class="task-item">
          <div class="task-priority" :class="'p' + task.priority">{{ task.priority }}</div>
          <div class="task-content">
            <strong>{{ task.title }}</strong>
            <p v-if="task.description">{{ task.description }}</p>
          </div>
          <div class="task-category">{{ categoryLabel(task.category) }}</div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { useGrowthStageStore } from '@/stores/useGrowthStageStore'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const store = useGrowthStageStore()

function categoryLabel(key: string): string {
  const map: Record<string, string> = {
    revenue: '💰 收入', works: '🎨 作品', certification: '📜 存证',
    distribution: '📤 分发', community: '👥 社群',
  }
  return map[key] || key
}

// Init
store.loadDashboard()
</script>

<style scoped>
.growth-stage-view {
  max-width: 800px;
  margin: 0 auto;
}
h2 { font-size: 1.4rem; margin-bottom: 4px; }
.subtitle { color: var(--muted); font-size: 0.85rem; margin-bottom: 24px; }

.stage-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: var(--radius);
  padding: 24px;
  color: white;
  margin-bottom: 16px;
}
.stage-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.stage-badge {
  font-size: 1.2rem;
  font-weight: 800;
  background: rgba(255,255,255,0.2);
  padding: 4px 16px;
  border-radius: 20px;
}
.stage-progress-text { font-size: 1.5rem; font-weight: 800; }
.stage-desc { opacity: 0.9; font-size: 0.9rem; margin-bottom: 16px; }

.progress-bar-container {
  height: 8px;
  background: rgba(255,255,255,0.3);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 16px;
}
.progress-bar {
  height: 100%;
  background: #22c55e;
  border-radius: 4px;
  transition: width 0.5s;
}

.unlock-features { margin-bottom: 16px; }
.unlock-features strong { margin-right: 8px; }
.feature-tag {
  display: inline-block;
  background: rgba(255,255,255,0.2);
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 0.8rem;
  margin: 2px 4px 2px 0;
}

.next-stage {
  border-top: 1px solid rgba(255,255,255,0.3);
  padding-top: 12px;
}
.next-stage strong { font-size: 0.9rem; }
.remaining { display: flex; gap: 16px; font-size: 0.8rem; margin-top: 8px; opacity: 0.85; flex-wrap: wrap; }

.tasks-section { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; }
.tasks-section h3 { margin: 0 0 12px; font-size: 1rem; }

.task-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
}
.task-item:last-child { border-bottom: none; }
.task-priority {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  flex-shrink: 0;
}
.task-priority.p1 { background: #fee2e2; color: #dc2626; }
.task-priority.p2 { background: #fef3c7; color: #d97706; }
.task-priority.p3 { background: #dbeafe; color: #2563eb; }
.task-content { flex: 1; }
.task-content strong { font-size: 0.9rem; display: block; }
.task-content p { font-size: 0.8rem; color: var(--muted); margin: 2px 0 0; }
.task-category { font-size: 0.75rem; color: var(--muted); flex-shrink: 0; }
</style>
