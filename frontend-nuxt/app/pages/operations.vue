<template>
  <div class="page-operations">
    <h1 class="page-title">运营合作中心</h1>

    <div class="tabs">
      <button :class="['tab-btn', { active: activeTab === 'operator' }]" @click="activeTab = 'operator'">
        运营合作
      </button>
      <button v-if="isCreator" :class="['tab-btn', { active: activeTab === 'creator' }]" @click="activeTab = 'creator'">
        创作者待办
        <span v-if="creatorPendingCount" class="badge">{{ creatorPendingCount }}</span>
      </button>
    </div>

    <!-- 运营者视图 -->
    <div v-if="activeTab === 'operator' && isOperator">
      <div class="filter-bar">
        <select v-model="statusFilter" class="filter-select">
          <option value="">全部状态</option>
          <option value="pending">待处理</option>
          <option value="accepted">已接受</option>
          <option value="rejected">已拒绝</option>
          <option value="expired">已过期</option>
        </select>
        <button class="btn-primary" @click="showProposeDialog = true">
          + 发起合作要约
        </button>
      </div>

      <div v-if="loading" class="loading-state">加载中...</div>
      <div v-else-if="error" class="error-state">{{ error }}</div>
      <div v-else class="coop-list">
        <div v-for="coop in filteredOperations" :key="coop.id" class="coop-card">
          <div class="coop-header">
            <span class="coop-work-title">{{ coop.work_title || coop.work_id }}</span>
            <span class="status-badge" :style="{ color: STATUS_COLOR[coop.status] }">
              {{ STATUS_LABEL[coop.status] }}
            </span>
          </div>
          <div class="coop-body">
            <div class="coop-meta">
              <span>创作者: {{ coop.creator_name || coop.creator_id }}</span>
              <span>创建: {{ formatDate(coop.created_at) }}</span>
              <span v-if="coop.expires_at">截止: {{ formatDate(coop.expires_at) }}
                <span v-if="daysUntil(coop.expires_at) !== null"
                      :class="['days-remaining', daysUntil(coop.expires_at)! <= 3 ? 'urgent' : '']">
                  ({{ daysUntil(coop.expires_at) }}天)
                </span>
              </span>
            </div>
            <div v-if="coop.notes" class="coop-notes">{{ coop.notes }}</div>
            <div class="coop-scope">
              <div v-if="coop.scope?.regions?.length" class="scope-item">
                <span class="scope-label">地区</span>
                <span class="scope-values">{{ coop.scope.regions.join(', ') }}</span>
              </div>
              <div v-if="coop.scope?.channels?.length" class="scope-item">
                <span class="scope-label">渠道</span>
                <span class="scope-values">{{ coop.scope.channels.join(', ') }}</span>
              </div>
              <div v-if="coop.scope?.products?.length" class="scope-item">
                <span class="scope-label">产品</span>
                <span class="scope-values">{{ coop.scope.products.join(', ') }}</span>
              </div>
              <div v-if="coop.scope?.duration_months" class="scope-item">
                <span class="scope-label">期限</span>
                <span class="scope-values">{{ coop.scope.duration_months }}个月</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div v-if="!filteredOperations.length && !loading" class="empty-state">暂无合作要约</div>
    </div>

    <!-- 创作者视图 -->
    <div v-else-if="activeTab === 'creator' && isCreator">
      <div v-if="loading" class="loading-state">加载中...</div>
      <div v-else-if="error" class="error-state">{{ error }}</div>
      <div v-else class="coop-list">
        <div v-for="coop in creatorPendingOperations" :key="coop.id" class="coop-card pending-card">
          <div class="coop-header">
            <span class="coop-work-title">{{ coop.work_title || coop.work_id }}</span>
            <span class="status-badge" style="color: #f59e0b">待处理</span>
          </div>
          <div class="coop-body">
            <div class="coop-meta">
              <span>运营者: {{ coop.operator_name || coop.operator_id }}</span>
              <span>创建: {{ formatDate(coop.created_at) }}</span>
              <span v-if="coop.expires_at">截止: {{ formatDate(coop.expires_at) }}
                <span v-if="daysUntil(coop.expires_at) !== null"
                      :class="['days-remaining', daysUntil(coop.expires_at)! <= 3 ? 'urgent' : '']">
                  ({{ daysUntil(coop.expires_at) }}天)
                </span>
              </span>
            </div>
            <div v-if="coop.notes" class="coop-notes">{{ coop.notes }}</div>
            <div class="coop-scope">
              <div v-if="coop.scope?.regions?.length" class="scope-item">
                <span class="scope-label">地区</span>
                <span class="scope-values">{{ coop.scope.regions.join(', ') }}</span>
              </div>
              <div v-if="coop.scope?.channels?.length" class="scope-item">
                <span class="scope-label">渠道</span>
                <span class="scope-values">{{ coop.scope.channels.join(', ') }}</span>
              </div>
              <div v-if="coop.scope?.products?.length" class="scope-item">
                <span class="scope-label">产品</span>
                <span class="scope-values">{{ coop.scope.products.join(', ') }}</span>
              </div>
              <div v-if="coop.scope?.duration_months" class="scope-item">
                <span class="scope-label">期限</span>
                <span class="scope-values">{{ coop.scope.duration_months }}个月</span>
              </div>
            </div>
          </div>
          <div class="coop-actions">
            <button class="btn-accept" @click="handleAccept(coop.id)">接受</button>
            <button class="btn-reject" @click="handleReject(coop.id)">拒绝</button>
          </div>
        </div>
      </div>
      <div v-if="!creatorPendingOperations.length && !loading" class="empty-state">暂无待处理的合作请求</div>
    </div>

    <!-- 发起合作要约弹窗 -->
    <ProposeDialog
      v-if="showProposeDialog"
      @close="showProposeDialog = false"
      @submitted="onProposeSubmitted"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import {
  fetchOperatorOperations,
  proposeCooperation,
  fetchCreatorPendingOperations,
  acceptCooperation,
  rejectCooperation,
} from '~/composables/useOperationApi'
import {
  STATUS_LABEL, STATUS_COLOR, formatDate, daysUntil,
} from '~/utils/operation'
import ProposeDialog from '~/components/operations/ProposeDialog.vue'

const auth = useAuthStore()
useHead({ title: '运营合作中心 — OriSpark' })

const activeTab = ref('operator')
const statusFilter = ref('')
const loading = ref(false)
const error = ref<string | null>(null)
const operations = ref<any[]>([])
const creatorPendingOperations = ref<any[]>([])
const showProposeDialog = ref(false)

const isOperator = computed(() => auth.isLoggedIn && auth.isOperator)
const isCreator = computed(() => auth.isLoggedIn && !!auth.user?.creator_type)
const creatorPendingCount = computed(() =>
  creatorPendingOperations.value.filter(o => o.status === 'pending').length
)

const filteredOperations = computed(() => {
  if (!statusFilter.value) return operations.value
  return operations.value.filter(o => o.status === statusFilter.value)
})

async function loadOperatorOperations() {
  loading.value = true
  error.value = null
  try {
    operations.value = await fetchOperatorOperations(statusFilter.value || undefined)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

async function loadCreatorPending() {
  try {
    creatorPendingOperations.value = await fetchCreatorPendingOperations()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  }
}

async function handleAccept(id: string) {
  try {
    await acceptCooperation(id)
    creatorPendingOperations.value = creatorPendingOperations.value.filter(o => o.id !== id)
    await loadOperatorOperations()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '操作失败'
  }
}

async function handleReject(id: string) {
  try {
    await rejectCooperation(id)
    creatorPendingOperations.value = creatorPendingOperations.value.filter(o => o.id !== id)
    await loadOperatorOperations()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '操作失败'
  }
}

async function onProposeSubmitted() {
  showProposeDialog.value = false
  await loadOperatorOperations()
}

watch(activeTab, (tab) => {
  if (tab === 'operator') loadOperatorOperations()
  else if (tab === 'creator') loadCreatorPending()
})

watch(statusFilter, loadOperatorOperations)

onMounted(() => {
  if (isOperator.value) loadOperatorOperations()
  if (isCreator.value) loadCreatorPending()
})
</script>

<style scoped>
.page-operations {
  padding: 32px;
  max-width: 960px;
  margin: 0 auto;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 24px;
  color: #1f2937;
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  border-bottom: 2px solid #e5e7eb;
  padding-bottom: 0;
}

.tab-btn {
  padding: 10px 20px;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  background: none;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  color: #6b7280;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.tab-btn.active {
  color: #059669;
  border-bottom-color: #059669;
}

.badge {
  background: #ef4444;
  color: #fff;
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 10px;
  font-weight: 600;
}

.filter-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  align-items: center;
}

.filter-select {
  padding: 10px 16px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  background: #fff;
}

.btn-primary {
  padding: 10px 20px;
  background: #059669;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}

.btn-primary:hover {
  background: #047857;
}

.coop-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.coop-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  transition: box-shadow 0.2s;
}

.coop-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.pending-card {
  border-left: 4px solid #f59e0b;
}

.coop-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.coop-work-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.status-badge {
  font-size: 12px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 100px;
  background: rgba(0, 0, 0, 0.05);
}

.coop-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.coop-meta {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: #6b7280;
  flex-wrap: wrap;
}

.coop-notes {
  font-size: 14px;
  color: #374151;
  line-height: 1.5;
  padding: 8px 12px;
  background: #f9fafb;
  border-radius: 6px;
}

.coop-scope {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.scope-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.scope-label {
  color: #6b7280;
  font-weight: 500;
}

.scope-values {
  color: #1f2937;
}

.days-remaining {
  font-size: 12px;
  font-weight: 600;
}

.days-remaining.urgent {
  color: #ef4444;
}

.coop-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f3f4f6;
}

.btn-accept {
  padding: 8px 24px;
  background: #10b981;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.btn-accept:hover {
  background: #059669;
}

.btn-reject {
  padding: 8px 24px;
  background: #fff;
  color: #ef4444;
  border: 1px solid #ef4444;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.btn-reject:hover {
  background: #fef2f2;
}

.loading-state,
.error-state,
.empty-state {
  text-align: center;
  padding: 48px 0;
  color: #6b7280;
}

.error-state {
  color: #ef4444;
}
</style>
