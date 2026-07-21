<template>
  <div class="copyright-guide-view">
    <LoadingSpinner v-if="store.loading" text="加载中..." />
    <template v-else>
      <h2>版权登记指南</h2>
      <p class="subtitle">按作品类型查看登记流程 · 跟踪申请进度</p>

      <!-- 概览 -->
      <div class="stats-row">
        <div class="stat-card">
          <div class="stat-value">{{ summary?.total || 0 }}</div>
          <div class="stat-label">总申请</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ summary?.by_status?.submitted || 0 }}</div>
          <div class="stat-label">已提交</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ summary?.by_status?.approved || 0 }}</div>
          <div class="stat-label">已获批</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">¥{{ formatNum(summary?.total_fees_yuan) }}</div>
          <div class="stat-label">总费用</div>
        </div>
      </div>

      <!-- 登记指南 -->
      <div class="section">
        <h3>登记指南</h3>
        <div class="guide-grid">
          <div v-for="g in store.guides" :key="g.work_type" class="guide-card" @click="selectedGuide = selectedGuide === g.work_type ? null : g.work_type">
            <div class="guide-header">
              <strong>{{ g.title_zh }}</strong>
              <span class="guide-time">{{ g.estimated_days }}天</span>
            </div>
            <p class="guide-fee">预计费用: ¥{{ g.estimated_fee_yuan }}</p>
            <div v-if="selectedGuide === g.work_type" class="guide-steps">
              <ol v-for="s in g.steps" :key="s.step">
                <li><strong>{{ s.title }}</strong> — {{ s.description }}</li>
              </ol>
            </div>
          </div>
        </div>
      </div>

      <!-- 我的申请 -->
      <div class="section">
        <h3>我的申请</h3>
        <button class="btn-add" @click="showNewReg = !showNewReg">
          {{ showNewReg ? '取消' : '+ 新建申请' }}
        </button>
        <div v-if="showNewReg" class="new-reg-form">
          <input v-model="newRegTitle" placeholder="作品名称" class="form-input" />
          <select v-model="newRegType" class="form-select">
            <option value="">作品类型</option>
            <option v-for="g in store.guides" :key="g.work_type" :value="g.work_type">{{ g.title_zh }}</option>
          </select>
          <button class="btn-confirm" @click="handleCreateReg">创建</button>
        </div>
        <div class="reg-list">
          <div v-for="r in store.registrations" :key="r.id" class="reg-item" :class="statusClass(r.status)">
            <div class="reg-info">
              <strong>{{ r.title }}</strong>
              <span class="reg-type">{{ TYPE_LABELS[r.work_type] || r.work_type }}</span>
              <span class="reg-status">{{ STATUS_LABELS[r.status] || r.status }}</span>
            </div>
            <div v-if="r.fee_yuan" class="reg-fee">¥{{ r.fee_yuan }}</div>
          </div>
          <div v-if="store.registrations.length === 0" class="empty-state">暂无申请记录。</div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { useCopyrightGuideStore } from '@/stores/useCopyrightGuideStore'

const store = useCopyrightGuideStore()
const selectedGuide = ref<string | null>(null)
const showNewReg = ref(false)
const newRegTitle = ref('')
const newRegType = ref('')

// Expose store refs for template
const summary = store.summary

const TYPE_LABELS: Record<string, string> = {
  illustration: '美术/插画', photo: '摄影', music: '音乐', writing: '文字',
}
const STATUS_LABELS: Record<string, string> = {
  draft: '草稿', submitted: '已提交', approved: '已获批', rejected: '被拒',
}

function statusClass(s: string): string {
  return `status-${s}`
}

function formatNum(n?: number): string {
  if (!n) return '0.00'
  return n.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

async function handleCreateReg() {
  if (!newRegTitle.value || !newRegType.value) return
  await store.createRegistration({ title: newRegTitle.value, work_type: newRegType.value })
  newRegTitle.value = ''
  showNewReg.value = false
}

onMounted(() => {
  store.loadGuides()
  store.loadRegistrations()
  store.loadSummary()
})
</script>

<style scoped>
.copyright-guide-view { max-width: 900px; margin: 0 auto; }
h2 { font-size: 1.4rem; margin-bottom: 4px; }
.subtitle { color: var(--muted); font-size: 0.85rem; margin-bottom: 24px; }

.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
.stat-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; text-align: center; }
.stat-value { font-size: 1.4rem; font-weight: 800; color: var(--accent); }
.stat-label { font-size: 0.8rem; color: var(--muted); }

.section { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; margin-bottom: 16px; }
.section h3 { margin: 0 0 12px; font-size: 1rem; }

.guide-grid { display: grid; gap: 12px; }
.guide-card { border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 14px; cursor: pointer; transition: background 0.2s; }
.guide-card:hover { background: #f9fafb; }
.guide-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.guide-header strong { font-size: 0.95rem; }
.guide-time { font-size: 0.8rem; color: var(--muted); }
.guide-fee { font-size: 0.8rem; color: var(--accent); margin: 0 0 8px; }
.guide-steps { margin-top: 8px; padding-top: 8px; border-top: 1px solid var(--border); }
.guide-steps ol { padding-left: 20px; font-size: 0.85rem; }
.guide-steps li { margin-bottom: 4px; }

.btn-add { background: none; border: 1px dashed var(--border); padding: 6px 16px; border-radius: var(--radius-sm); cursor: pointer; font-size: 0.8rem; color: var(--accent); }

.new-reg-form { display: flex; gap: 8px; margin: 12px 0; flex-wrap: wrap; }
.form-input, .form-select { padding: 8px 12px; border: 1px solid var(--border); border-radius: var(--radius-sm); font-size: 0.85rem; flex: 1; }
.btn-confirm { background: var(--accent); color: white; border: none; padding: 8px 16px; border-radius: var(--radius-sm); cursor: pointer; }

.reg-list { margin-top: 12px; display: grid; gap: 8px; }
.reg-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; border: 1px solid var(--border); border-radius: var(--radius-sm); }
.reg-info { display: flex; gap: 8px; align-items: center; font-size: 0.85rem; }
.reg-type { font-size: 0.75rem; color: var(--muted); }
.reg-status { font-size: 0.75rem; padding: 2px 8px; border-radius: 10px; }
.status-draft .reg-status { background: #f3f4f6; color: #6b7280; }
.status-submitted .reg-status { background: #dbeafe; color: #2563eb; }
.status-approved .reg-status { background: #dcfce7; color: #16a34a; }
.status-rejected .reg-status { background: #fef2f2; color: #dc2626; }
.reg-fee { font-size: 0.85rem; font-weight: 700; color: var(--accent); }

.empty-state { text-align: center; color: var(--muted); padding: 16px; font-size: 0.85rem; }
</style>
