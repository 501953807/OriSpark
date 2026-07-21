<template>
  <div class="content-pipeline-view">
    <LoadingSpinner v-if="loading" text="加载中..." />
    <template v-else>
      <h2>多平台内容分发</h2>
      <p class="subtitle">绑定账号 · 定时发布 · 模拟适配</p>

      <!-- 统计卡片 -->
      <div class="stats-row">
        <div class="stat-card">
          <div class="stat-value">{{ stats.scheduled }}</div>
          <div class="stat-label">待发布</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ stats.published }}</div>
          <div class="stat-label">已发布</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ stats.failed }}</div>
          <div class="stat-label">失败</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ stats.recent_7d_success }}</div>
          <div class="stat-label">近7天成功</div>
        </div>
      </div>

      <!-- 平台账号管理 -->
      <div class="section">
        <h3>平台账号</h3>
        <button class="btn-add" @click="showAddAccount = !showAddAccount">
          {{ showAddAccount ? '取消' : '+ 绑定平台' }}
        </button>
        <div v-if="showAddAccount" class="add-form">
          <select v-model="newAccount.platform" class="form-select">
            <option value="">选择平台</option>
            <option v-for="p in availablePlatforms" :key="p" :value="p">{{ PLATFORMS[p].name_zh }}</option>
          </select>
          <input v-model="newAccount.account_name" placeholder="账号名称" class="form-input" />
          <input v-model.number="newAccount.follower_count" placeholder="粉丝数 (可选)" type="number" class="form-input" />
          <button class="btn-confirm" @click="handleAddAccount">确认绑定</button>
        </div>
        <div class="account-list">
          <div v-for="acc in accounts" :key="acc.id" class="account-item">
            <div class="account-info">
              <strong>{{ PLATFORMS[acc.platform]?.name_zh || acc.platform }}</strong>
              <span>{{ acc.account_name }}</span>
              <span v-if="acc.follower_count > 0">{{ formatNumber(acc.follower_count) }}粉丝</span>
            </div>
            <button class="btn-remove" @click="handleRemoveAccount(acc.platform)">解绑</button>
          </div>
          <div v-if="accounts.length === 0" class="empty-state">
            暂无绑定平台，点击上方按钮开始。
          </div>
        </div>
      </div>

      <!-- 创建发布计划 -->
      <div class="section">
        <h3>发布计划</h3>
        <button class="btn-add" @click="showCreateSchedule = !showCreateSchedule">
          {{ showCreateSchedule ? '取消' : '+ 新建计划' }}
        </button>
        <div v-if="showCreateSchedule" class="schedule-form">
          <input v-model="newSchedule.title" placeholder="标题" class="form-input" />
          <textarea v-model="newSchedule.description" placeholder="描述 (可选)" class="form-input form-textarea" />
          <div class="platform-checks">
            <label v-for="p in Object.keys(PLATFORMS)" :key="p" class="platform-checkbox">
              <input type="checkbox" :value="p" v-model="selectedPlatforms" />
              {{ PLATFORMS[p].name_zh }}
            </label>
          </div>
          <input type="datetime-local" v-model="newSchedule.scheduled_at" class="form-input" />
          <label class="checkbox-label">
            <input type="checkbox" v-model="newSchedule.is_recurring" />
            循环发布
          </label>
          <select v-if="newSchedule.is_recurring" v-model="newSchedule.recurring_pattern" class="form-select">
            <option value="daily">每日</option>
            <option value="weekly">每周</option>
            <option value="biweekly">每两周</option>
          </select>
          <button class="btn-confirm" @click="handleCreateSchedule">创建计划</button>
        </div>
      </div>

      <!-- 模拟适配 -->
      <div class="section">
        <h3>多平台适配模拟</h3>
        <div class="simulate-form">
          <input v-model="simulateTitle" placeholder="输入标题" class="form-input" />
          <div class="platform-checks">
            <label v-for="p in Object.keys(PLATFORMS)" :key="p" class="platform-checkbox">
              <input type="checkbox" :value="p" v-model="simulatePlatforms" />
              {{ PLATFORMS[p].name_zh }}
            </label>
          </div>
          <button class="btn-confirm" @click="handleSimulate">模拟适配</button>
        </div>
        <div v-if="simulateResults.length > 0" class="simulate-results">
          <div v-for="r in simulateResults" :key="r.platform" class="simulate-card">
            <div class="simulate-header">
              <strong>{{ r.platform_name }}</strong>
              <span :class="['tags-badge', { ok: r.tags_ok, fail: !r.tags_ok }]">
                {{ r.tags_ok ? '标签数量合适' : `标签过多 (${r.tags_count}/${r.max_tags})` }}
              </span>
            </div>
            <p class="title-hint">{{ r.title_adapted }}</p>
            <p class="cover-hint">推荐封面: {{ COVER_TYPES[r.recommended_cover] }}</p>
          </div>
        </div>
      </div>

      <!-- 发布计划列表 -->
      <div class="section">
        <h3>发布计划列表</h3>
        <div class="schedule-list">
          <div v-for="s in schedules" :key="s.id" class="schedule-item">
            <div class="schedule-info">
              <strong>{{ s.title }}</strong>
              <span class="schedule-time">{{ s.scheduled_at }}</span>
              <span class="schedule-status" :class="s.status">{{ statusLabel(s.status) }}</span>
            </div>
            <button v-if="s.status === 'scheduled'" class="btn-cancel" @click="handleCancelSchedule(s.id)">取消</button>
          </div>
          <div v-if="schedules.length === 0" class="empty-state">
            暂无发布计划。
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import type { PlatformAccount, PublishSchedule, SimulateResult, PublishStats } from '@/types/contentPipeline'

const PLATFORMS: Record<string, { name_zh: string; max_tags: number }> = {
  xiaohongshu: { name_zh: '小红书', max_tags: 10 },
  bilibili: { name_zh: 'B站', max_tags: 5 },
  douyin: { name_zh: '抖音', max_tags: 10 },
  weibo: { name_zh: '微博', max_tags: 0 },
  zhihu: { name_zh: '知乎', max_tags: 3 },
  kuaishou: { name_zh: '快手', max_tags: 10 },
}
const COVER_TYPES: Record<string, string> = {
  vertical: '竖版 (9:16)',
  horizontal: '横版 (16:9)',
  square: '方版 (1:1)',
  auto: '自动',
}

const loading = ref(false)
const accounts = ref<PlatformAccount[]>([])
const schedules = ref<PublishSchedule[]>([])
const stats = ref<PublishStats>({ total_schedules: 0, scheduled: 0, published: 0, failed: 0, recent_7d_success: 0 })
const simulateResults = ref<SimulateResult[]>([])

const showAddAccount = ref(false)
const showCreateSchedule = ref(false)
const newAccount = ref({ platform: '', account_name: '', follower_count: 0 })
const newSchedule = ref({
  title: '', description: '', platforms: [] as string[],
  scheduled_at: '', is_recurring: false, recurring_pattern: 'weekly',
})
const selectedPlatforms = ref<string[]>([])
const simulatePlatforms = ref<string[]>([])
const simulateTitle = ref('')

const availablePlatforms = Object.keys(PLATFORMS)

async function loadAll() {
  loading.value = true
  try {
    const res = await fetch('/api/content-pipeline/accounts')
    if (res.ok) accounts.value = await res.json()
  } catch { /* silent */ }
  try {
    const res = await fetch('/api/content-pipeline/schedules')
    if (res.ok) schedules.value = await res.json()
  } catch { /* silent */ }
  try {
    const res = await fetch('/api/content-pipeline/stats')
    if (res.ok) stats.value = await res.json()
  } catch { /* silent */ }
  loading.value = false
}

async function handleAddAccount() {
  if (!newAccount.value.platform || !newAccount.value.account_name) return
  await fetch('/api/content-pipeline/accounts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(newAccount.value),
  })
  newAccount.value = { platform: '', account_name: '', follower_count: 0 }
  showAddAccount.value = false
  loadAll()
}

async function handleRemoveAccount(platform: string) {
  await fetch(`/api/content-pipeline/accounts/${platform}`, { method: 'DELETE' })
  loadAll()
}

async function handleCreateSchedule() {
  if (!newSchedule.value.title || selectedPlatforms.value.length === 0) return
  const platforms = selectedPlatforms.value.map(p => ({ platform: p, status: 'pending' }))
  await fetch('/api/content-pipeline/schedules', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ...newSchedule.value,
      platforms,
      scheduled_at: newSchedule.value.scheduled_at + ':00',
    }),
  })
  newSchedule.value = { title: '', description: '', platforms: [], scheduled_at: '', is_recurring: false, recurring_pattern: 'weekly' }
  selectedPlatforms.value = []
  showCreateSchedule.value = false
  loadAll()
}

async function handleCancelSchedule(id: string) {
  await fetch(`/api/content-pipeline/schedules/${id}`, { method: 'DELETE' })
  loadAll()
}

async function handleSimulate() {
  if (!simulateTitle.value || simulatePlatforms.value.length === 0) return
  const platforms = simulatePlatforms.value.map(p => ({ platform: p, status: 'pending' }))
  const body = { title: simulateTitle.value, description: '', platforms, scheduled_at: '', is_recurring: false }
  const res = await fetch('/api/content-pipeline/simulate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (res.ok) {
    const data = await res.json()
    simulateResults.value = data.adaptations
  }
}

function formatNumber(n: number): string {
  if (n >= 10000) return `${(n / 10000).toFixed(1)}万`
  return n.toString()
}

function statusLabel(s: string): string {
  return { scheduled: '待发布', published: '已发布', failed: '失败', cancelled: '已取消' }[s] || s
}

onMounted(loadAll)
</script>

<style scoped>
.content-pipeline-view { max-width: 900px; margin: 0 auto; }
h2 { font-size: 1.4rem; margin-bottom: 4px; }
.subtitle { color: var(--muted); font-size: 0.85rem; margin-bottom: 24px; }

.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
.stat-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; text-align: center; }
.stat-value { font-size: 1.8rem; font-weight: 800; color: var(--accent); }
.stat-label { font-size: 0.8rem; color: var(--muted); }

.section { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; margin-bottom: 16px; }
.section h3 { margin: 0 0 12px; font-size: 1rem; display: flex; justify-content: space-between; align-items: center; }

.btn-add { background: none; border: 1px dashed var(--border); padding: 6px 16px; border-radius: var(--radius-sm); cursor: pointer; font-size: 0.8rem; color: var(--accent); }
.btn-add:hover { border-color: var(--accent); }

.add-form, .schedule-form, .simulate-form { display: flex; flex-direction: column; gap: 8px; margin-top: 12px; }
.form-input, .form-select, .form-textarea { padding: 8px 12px; border: 1px solid var(--border); border-radius: var(--radius-sm); font-size: 0.85rem; }
.form-textarea { min-height: 60px; resize: vertical; }

.platform-checks { display: flex; flex-wrap: wrap; gap: 8px; }
.platform-checkbox { display: flex; align-items: center; gap: 4px; font-size: 0.85rem; cursor: pointer; }
.checkbox-label { font-size: 0.85rem; display: flex; align-items: center; gap: 4px; }
.btn-confirm { background: var(--accent); color: white; border: none; padding: 8px 16px; border-radius: var(--radius-sm); cursor: pointer; font-size: 0.85rem; }

.account-list { margin-top: 12px; display: grid; gap: 8px; }
.account-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; border: 1px solid var(--border); border-radius: var(--radius-sm); }
.account-info { display: flex; gap: 12px; align-items: center; font-size: 0.85rem; }
.account-info strong { min-width: 60px; }
.btn-remove { background: none; border: 1px solid #ef4444; color: #ef4444; padding: 4px 12px; border-radius: var(--radius-sm); cursor: pointer; font-size: 0.75rem; }

.schedule-list { margin-top: 12px; display: grid; gap: 8px; }
.schedule-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; border: 1px solid var(--border); border-radius: var(--radius-sm); }
.schedule-info { display: flex; gap: 12px; align-items: center; font-size: 0.85rem; }
.schedule-time { color: var(--muted); font-size: 0.8rem; }
.schedule-status { font-size: 0.75rem; padding: 2px 8px; border-radius: 10px; }
.schedule-status.scheduled { background: #dbeafe; color: #2563eb; }
.schedule-status.published { background: #dcfce7; color: #16a34a; }
.schedule-status.failed { background: #fef2f2; color: #dc2626; }
.btn-cancel { background: none; border: 1px solid #f59e0b; color: #f59e0b; padding: 4px 12px; border-radius: var(--radius-sm); cursor: pointer; font-size: 0.75rem; }

.simulate-results { margin-top: 12px; display: grid; gap: 8px; }
.simulate-card { padding: 12px; border: 1px solid var(--border); border-radius: var(--radius-sm); }
.simulate-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.simulate-header strong { font-size: 0.9rem; }
.tags-badge { font-size: 0.75rem; padding: 2px 8px; border-radius: 10px; }
.tags-badge.ok { background: #dcfce7; color: #16a34a; }
.tags-badge.fail { background: #fef2f2; color: #dc2626; }
.title-hint { font-size: 0.85rem; color: var(--muted); margin: 4px 0; }
.cover-hint { font-size: 0.8rem; color: var(--muted); margin: 0; }

.empty-state { text-align: center; color: var(--muted); padding: 16px; font-size: 0.85rem; }
</style>
