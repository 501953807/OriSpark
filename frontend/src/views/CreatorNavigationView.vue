<template>
  <div class="navigation-view">
    <LoadingSpinner v-if="store.loading" text="加载中..." />
    <template v-else-if="status">
      <h2>创作者导航</h2>
      <p class="subtitle">引导你逐步完成经营配置，提升创作收益</p>

      <!-- Tab 切换 -->
      <div class="tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          :class="['tab', { active: activeTab === tab.key }]"
          @click="switchTab(tab.key)"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- 进度条 -->
      <div class="progress-section">
        <div class="progress-header">
          <span>总进度</span>
          <span class="progress-value">{{ status.progress_percent }}%</span>
        </div>
        <div class="progress-bar-track">
          <div
            class="progress-bar-fill"
            :style="{ width: `${status.progress_percent}%` }"
            :class="'progress-' + progressColor"
          ></div>
        </div>
      </div>

      <!-- 当前任务高亮 -->
      <div v-if="status.current_task" class="current-task-card">
        <div class="current-label">当前任务</div>
        <h3>{{ status.current_task.title }}</h3>
        <p>{{ status.current_task.description }}</p>
        <button class="btn-primary" @click="doComplete(status.current_task.task_key)">
          标记完成
        </button>
      </div>

      <!-- 已完成任务列表 -->
      <div v-if="status.completed_tasks.length > 0" class="completed-section">
        <h3>已完成</h3>
        <div v-for="task in status.completed_tasks" :key="task.task_key" class="task-item done">
          <span class="task-check">✓</span>
          <span class="task-title">{{ task.title }}</span>
        </div>
      </div>

      <!-- 待完成任务列表 -->
      <div class="remaining-section">
        <h3>待完成</h3>
        <div v-for="task in status.remaining_tasks" :key="task.task_key" class="task-item">
          <span class="task-dot"></span>
          <span class="task-title">{{ task.title }}</span>
          <button class="btn-small" @click="doComplete(task.task_key)">完成</button>
        </div>
      </div>

      <!-- 全部完成 -->
      <div v-if="status.remaining_tasks.length === 0 && !status.current_task" class="all-done">
        🎉 恭喜！所有任务已完成
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useNavigationStore } from '@/stores/useNavigationStore'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const store = useNavigationStore()
const activeTab = ref('onboarding')

const tabs = [
  { key: 'onboarding', label: '新手引导' },
  { key: 'compliance', label: '合规检查' },
  { key: 'growth', label: '成长建议' },
]

const status = computed(() => store.status)

const progressColor = computed(() => {
  const p = status.value?.progress_percent ?? 0
  if (p >= 80) return 'green'
  if (p >= 40) return 'yellow'
  return 'red'
})

async function switchTab(key: string) {
  activeTab.value = key
  await store.fetchStatus('current_user', key)
}

async function doComplete(taskKey: string) {
  const result = await store.markComplete(taskKey)
  if (result.new_progress !== undefined) {
    await store.fetchStatus('current_user', activeTab.value)
  }
}
</script>

<style scoped>
.navigation-view {
  max-width: 720px;
  margin: 0 auto;
}
h2 { font-size: 1.4rem; margin-bottom: 4px; }
.subtitle { color: var(--muted); font-size: 0.85rem; margin-bottom: 24px; }

.tabs { display: flex; gap: 8px; margin-bottom: 20px; }
.tab {
  padding: 8px 16px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: transparent;
  cursor: pointer;
  font-size: 0.9rem;
}
.tab.active {
  background: var(--accent);
  color: white;
  border-color: var(--accent);
}

.progress-section {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px 20px;
  margin-bottom: 20px;
}
.progress-header {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  margin-bottom: 8px;
}
.progress-value { font-weight: 700; }
.progress-bar-track {
  height: 8px;
  background: var(--bg-secondary);
  border-radius: 4px;
  overflow: hidden;
}
.progress-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}
.progress-green { background: #22c55e; }
.progress-yellow { background: #f59e0b; }
.progress-red { background: #ef4444; }

.current-task-card {
  background: #fffbeb;
  border: 2px solid #f59e0b;
  border-radius: var(--radius);
  padding: 20px;
  margin-bottom: 20px;
}
.current-label {
  font-size: 0.75rem;
  color: #92400e;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 4px;
}
.current-task-card h3 { margin: 0 0 4px; font-size: 1.1rem; }
.current-task-card p { color: var(--muted); font-size: 0.85rem; margin: 0 0 12px; }

.completed-section, .remaining-section {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px 20px;
  margin-bottom: 16px;
}
.completed-section h3, .remaining-section h3 {
  margin-top: 0;
  font-size: 0.9rem;
  color: var(--muted);
}

.task-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
}
.task-item:last-child { border-bottom: none; }
.task-check {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #22c55e;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  flex-shrink: 0;
}
.task-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--border);
  flex-shrink: 0;
}
.task-title { flex: 1; font-size: 0.9rem; }
.done .task-title { color: var(--muted); text-decoration: line-through; }

.btn-primary {
  background: var(--accent);
  color: white;
  border: none;
  padding: 8px 20px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 0.9rem;
}
.btn-small {
  background: transparent;
  color: var(--accent);
  border: 1px solid var(--accent);
  padding: 4px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 0.8rem;
}
.btn-small:hover { background: var(--accent); color: white; }

.all-done {
  text-align: center;
  padding: 48px;
  font-size: 1.2rem;
  color: #22c55e;
}
</style>
