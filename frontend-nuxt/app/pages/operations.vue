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
            <span class="status-badge" style="color: var(--m-warning)">待处理</span>
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
definePageMeta({ layout: 'materio-topnav' })
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
  padding: 0;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 24px;
  color: var(--m-on-surface);
  padding: 0 24px;
}

.tabs {
  display: flex;
  gap: 0;
  margin-bottom: 24px;
  padding: 0 24px;
  border-bottom: 1px solid var(--m-border);
}

.tab-btn {
  padding: 12px 20px;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  background: none;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  color: var(--m-grey-500);
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
  font-family: inherit;
}

.tab-btn.active {
  color: var(--m-primary);
  border-bottom-color: var(--m-primary);
  font-weight: 600;
}

.badge {
  background: var(--m-error);
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
  padding: 8px 14px;
  border: 1px solid var(--m-border);
  border-radius: 6px;
  font-size: 14px;
  background: #FFFFFF;
  color: var(--m-on-surface);
  font-family: inherit;
}

.btn-primary {
  padding: 8px 20px;
  background: var(--m-primary);
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  font-family: inherit;
}

.btn-primary:hover {
  background: rgb(110, 57, 220);
}

.coop-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.coop-card {
  background: #FFFFFF;
  border-radius: 6px;
  border: none;
  box-shadow: var(--m-shadow-md);
  padding: 20px;
  transition: box-shadow 0.2s;
}

.coop-card:hover {
  box-shadow: rgba(46, 38, 61, 0.2) 0px 4px 10px 0px;
}

.pending-card {
  border-left: 4px solid var(--m-warning);
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
  color: var(--m-on-surface);
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
  color: var(--m-grey-500);
  flex-wrap: wrap;
}

.coop-notes {
  font-size: 14px;
  color: var(--m-on-surface);
  line-height: 1.5;
  padding: 8px 12px;
  background: var(--m-grey-100);
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
  color: var(--m-grey-500);
  font-weight: 500;
}

.scope-values {
  color: var(--m-on-surface);
}

.days-remaining {
  font-size: 12px;
  font-weight: 600;
}

.days-remaining.urgent {
  color: var(--m-error);
}

.coop-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(46, 38, 61, 0.06);
}

.btn-accept {
  padding: 8px 24px;
  background: var(--m-success);
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.btn-accept:hover {
  background: var(--m-success);
}

.btn-reject {
  padding: 8px 24px;
  background: transparent;
  color: var(--m-error);
  border: 1px solid var(--m-error);
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.btn-reject:hover {
  background: rgba(255, 76, 81, 0.06);
}

.loading-state,
.error-state,
.empty-state {
  text-align: center;
  padding: 48px 0;
  color: var(--m-grey-500);
}

.error-state {
  color: var(--m-error);
}
</style>
