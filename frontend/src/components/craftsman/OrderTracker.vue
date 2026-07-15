<template>
  <div class="order-tracker">
    <div
      v-for="order in orderedOrders"
      :key="order.id"
      class="order-row"
    >
      <!-- Order header -->
      <div class="order-summary">
        <span class="order-id">#{{ order.id.slice(0, 8) }}</span>
        <span class="order-detail">
          <template v-if="order.delivery_date">
            交期: {{ order.delivery_date }}
          </template>
        </span>
        <span class="countdown" :class="countdownClass(order.delivery_date)">
          {{ countdownText(order.delivery_date) }}
        </span>
      </div>

      <!-- 4-phase stepper -->
      <div class="stepper">
        <div
          v-for="(phase, idx) in PHASES"
          :key="phase.id"
          class="step"
          :class="stepClass(order, phase)"
        >
          <div class="step-circle">
            <span v-if="phaseStatus(order, phase) === 'approved'" class="step-icon">&#10003;</span>
            <span v-else-if="phaseStatus(order, phase) === 'rejected'" class="step-icon">&#10007;</span>
            <span v-else class="step-num">{{ idx + 1 }}</span>
          </div>
          <span class="step-label">{{ phase.label }}</span>
          <span class="step-badge" :class="'badge-' + phaseStatus(order, phase)">
            {{ BADGE_LABELS[phaseStatus(order, phase)] ?? phaseStatus(order, phase) }}
          </span>
        </div>
      </div>

      <!-- Connectors between steps -->
      <div class="connector">
        <svg viewBox="0 0 0 2" width="100%" height="2">
          <line
            x1="0" y1="1" x2="100%" y2="1"
            stroke="var(--border)"
            stroke-width="2"
            stroke-dasharray="4 3"
          />
        </svg>
      </div>

      <!-- Etsy sync status -->
      <div class="sync-status">
        <span class="sync-indicator" :class="'sync-' + order.etasync_status">
          <span class="sync-dot"></span>
          <span class="sync-text">{{ SYNC_LABELS[order.etasync_status] }}</span>
        </span>
      </div>
    </div>

    <div v-if="orderedOrders.length === 0" class="empty-state">
      <p>暂无订单</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Order, SampleStatus, QualityStatus, ETSyncStatus } from '@/types/craftsman'

interface Props {
  orders: Order[]
}

const props = defineProps<Props>()

// ── Phases ──────────────────────────────────────────────────────
interface Phase {
  id: string
  label: string
  statusField: keyof Pick<Order, 'sample_status' | 'quality_inspection'>
}

const PHASES: Phase[] = [
  { id: 'processing',     label: '来料加工',   statusField: 'sample_status' },
  { id: 'sampling',       label: '打样确认',   statusField: 'sample_status' },
  { id: 'production',     label: '量产排期',   statusField: 'quality_inspection' },
  { id: 'inspection',     label: '质检发货',   statusField: 'quality_inspection' },
]

const BADGE_LABELS: Record<string, string> = {
  pending:   '待处理',
  approved:  '已通过',
  rejected:  '已驳回',
}

const SYNC_LABELS: Record<ETSyncStatus, string> = {
  idle:   '未同步',
  syncing: '同步中',
  synced: '已同步',
  error:  '同步失败',
}

// ── Derive per-order phase statuses ──────────────────────────────
function phaseStatus(order: Order, phase: Phase): SampleStatus | QualityStatus {
  if (phase.id === 'processing' || phase.id === 'sampling') {
    return order.sample_status
  }
  return order.quality_inspection
}

function stepClass(order: Order, phase: Phase): string {
  const s = phaseStatus(order, phase)
  return `step-${s}`
}

// ── Ordering: open first, then by creation date desc ─────────────
const orderedOrders = computed(() => {
  const items = [...props.orders]
  items.sort((a, b) => {
    const priority = (o: Order): number => {
      if (o.etasync_status === 'syncing') return 0
      if (o.etasync_status === 'error') return 1
      if (o.sample_status === 'pending') return 2
      return 3
    }
    return priority(a) - priority(b)
  })
  return items
})

// ── Countdown ────────────────────────────────────────────────────
function countDaysUntil(deliveryDate?: string): number | null {
  if (!deliveryDate) return null
  try {
    const d = new Date(deliveryDate)
    const now = new Date()
    d.setHours(0, 0, 0, 0)
    now.setHours(0, 0, 0, 0)
    const diff = Math.ceil((d.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
    return diff
  } catch {
    return null
  }
}

function countdownClass(deliveryDate?: string): string {
  const days = countDaysUntil(deliveryDate)
  if (days === null) return ''
  if (days < 0) return 'overdue'
  if (days <= 3) return 'urgent'
  return ''
}

function countdownText(deliveryDate?: string): string {
  const days = countDaysUntil(deliveryDate)
  if (days === null) return ''
  if (days < 0) return `逾期 ${Math.abs(days)} 天`
  if (days === 0) return '今日交期'
  return `剩余 ${days} 天`
}
</script>

<style scoped>
.order-tracker {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ── Order summary bar ─────────────────────────────────────── */
.order-row {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.order-summary {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 0.84rem;
  flex-wrap: wrap;
}

.order-id {
  font-weight: 700;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  color: var(--fg);
}

.order-detail {
  color: var(--muted);
}

.countdown {
  font-size: 0.76rem;
  font-weight: 600;
  color: var(--muted);
}

.countdown.urgent {
  color: var(--orange);
}

.countdown.overdue {
  color: #ef4444;
}

/* ── Stepper ───────────────────────────────────────────────── */
.stepper {
  display: flex;
  align-items: flex-start;
  gap: 4px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 80px;
  flex: 1;
}

.step-circle {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--border);
  background: var(--bg);
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--muted);
  transition: border-color 0.2s, background 0.2s;
}

.step-approved .step-circle {
  border-color: var(--green);
  background: oklch(56% 0.12 170 / 0.1);
  color: var(--green);
}

.step-rejected .step-circle {
  border-color: #ef4444;
  background: oklch(56% 0.16 0 / 0.1);
  color: #ef4444;
}

.step-pending .step-circle {
  border-color: var(--orange);
  background: oklch(62% 0.18 55 / 0.1);
  color: var(--orange);
}

.step-icon {
  font-size: 0.85rem;
  line-height: 1;
}

.step-num {
  line-height: 1;
}

.step-label {
  font-size: 0.72rem;
  font-weight: 500;
  color: var(--muted);
  white-space: nowrap;
}

.step-pending .step-label {
  color: var(--orange);
}

.step-badge {
  font-size: 0.65rem;
  padding: 1px 6px;
  border-radius: 6px;
  font-weight: 600;
}

.badge-pending {
  background: oklch(62% 0.18 55 / 0.1);
  color: var(--orange);
}

.badge-approved,
.badge-pass {
  background: oklch(56% 0.12 170 / 0.12);
  color: var(--green);
}

.badge-rejected,
.badge-fail {
  background: oklch(56% 0.16 0 / 0.1);
  color: #ef4444;
}

.connector {
  width: 100%;
  opacity: 0.4;
}

.connector svg line {
  stroke-dasharray: 3 4;
}

/* ── Etsy sync ─────────────────────────────────────────────── */
.sync-status {
  display: flex;
  justify-content: flex-end;
}

.sync-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.74rem;
  font-weight: 500;
}

.sync-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--border);
}

.sync-idle .sync-dot { background: var(--border); }
.sync-syncing .sync-dot { background: var(--blue); animation: pulse 1.2s infinite; }
.sync-synced .sync-dot { background: var(--green); }
.sync-error .sync-dot { background: #ef4444; }

.sync-text {
  color: var(--muted);
}

.sync-idle .sync-text { color: var(--muted); }
.sync-syncing .sync-text { color: var(--blue); }
.sync-synced .sync-text { color: var(--green); }
.sync-error .sync-text { color: #ef4444; }

/* ── Empty ─────────────────────────────────────────────────── */
.empty-state {
  text-align: center;
  padding: 32px;
  color: var(--muted);
  font-size: 0.88rem;
  background: var(--surface);
  border-radius: var(--radius-sm);
  border: 1px dashed var(--border);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
</style>
