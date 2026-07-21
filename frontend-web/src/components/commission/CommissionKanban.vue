<template>
  <div class="kanban-board">
    <div
      v-for="col in columns"
      :key="col.key"
      class="kanban-column"
      :class="{ 'drag-over': colDragOver === col.key }"
      @dragover="onDragOver($event, col.key)"
      @dragleave="onDragLeave"
      @drop="onDrop($event, col)"
    >
      <div class="column-header">
        <span class="column-title">{{ col.label }}</span>
        <span class="column-count">{{ getColumnItems(col.key).length }}</span>
      </div>

      <div class="column-items">
        <div
          v-if="getColumnItems(col.key).length === 0"
          class="column-empty"
        >
          暂无委托
        </div>

        <div
          v-for="item in getColumnItems(col.key)"
          :key="item.id"
          class="kanban-card"
          :class="{ 'card-dragging': draggedId === item.id }"
          draggable="true"
          @dragstart="onDragStart($event, item)"
          @dragend="onDragEnd"
          @click="$emit('select', item)"
        >
          <div class="card-header">
            <div class="card-client">
              {{ item.client_name || '未知客户' }}
            </div>
            <div class="card-status-badge" :class="'status-' + col.key">
              {{ col.label }}
            </div>
          </div>

          <div v-if="item.title" class="card-title">
            {{ item.title }}
          </div>

          <div class="card-meta">
            <span v-if="item.amount" class="card-amount">
              {{ item.currency === 'CNY' ? '¥' : '$' }}{{ item.amount }}
            </span>
            <span v-if="item.due_date" class="card-due">
              截止: {{ item.due_date }}
              <span v-if="getDaysUntil(item.due_date) != null && getDaysUntil(item.due_date) <= 0" :class="dueDateClassFor(item.due_date)">
                (已逾期)
              </span>
              <span v-else-if="getDaysUntil(item.due_date) != null" :class="dueDateClassFor(item.due_date)">
                (还有 {{ getDaysUntil(item.due_date) }} 天)
              </span>
            </span>
          </div>

          <div v-if="item.milestones && item.milestones.length" class="card-progress">
            <div class="progress-bar-track">
              <div
                class="progress-bar-fill"
                :style="{ width: milestoneProgress(item) + '%' }"
              ></div>
            </div>
            <span class="progress-label">
              {{ milestonesCompleted(item) }} / {{ item.milestones.length }}
            </span>
          </div>

          <div class="card-blockers" v-if="col.nextTransition">
            <div class="blocker-label">下一步需要:</div>
            <div
              v-for="req in col.nextTransition"
              :key="req.condition"
              class="blocker-item"
              :class="{ blockerMet: req.met }"
            >
              <span class="blocker-icon">{{ req.met ? '✅' : '❌' }}</span>
              <span>{{ req.label }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, type PropType } from 'vue'
import type { CommissionProject } from '@/types/commission'

interface KanbanColumn {
  key: string
  label: string
  nextTransition?: TransitionRequirement[]
}

interface TransitionRequirement {
  label: string
  condition: string
  met: boolean
}

function computeDaysUntilDue(dueDateStr: string): number | null {
  try {
    const due = new Date(dueDateStr)
    const now = new Date()
    due.setHours(0, 0, 0, 0)
    now.setHours(0, 0, 0, 0)
    const diff = due.getTime() - now.getTime()
    return Math.ceil(diff / (1000 * 60 * 60 * 24))
  } catch {
    return null
  }
}

function computeMilestoneProgress(milestones: Array<{ status: string }>): number {
  if (!milestones || !milestones.length) return 0
  const completed = milestones.filter((m) => m.status === 'completed').length
  return Math.round((completed / milestones.length) * 100)
}

const STATUS_LABEL_MAP: Record<string, string> = {
  brief: '需求',
  proposal: '提案',
  production: '制作中',
  delivery: '交付',
  settlement: '已结款',
}

const STATUS_KEY_MAP: Record<string, string> = {
  '需求': 'brief',
  '提案': 'proposal',
  '制作中': 'production',
  '交付': 'delivery',
  '已结款': 'settlement',
}

const TRANSITIONS: KanbanColumn[] = [
  {
    key: 'brief',
    label: '需求',
    nextTransition: [
      { label: '收到定金', condition: 'deposit_received', met: false },
    ],
  },
  {
    key: 'proposal',
    label: '提案',
    nextTransition: [
      { label: '创建里程碑', condition: 'milestone_created', met: false },
    ],
  },
  {
    key: 'production',
    label: '制作中',
    nextTransition: [
      { label: '完成最终交付', condition: 'final_delivery', met: false },
    ],
  },
  {
    key: 'delivery',
    label: '交付',
    nextTransition: [
      { label: '收到全部款项', condition: 'all_payments_received', met: false },
    ],
  },
  {
    key: 'settlement',
    label: '已结款',
    nextTransition: [],
  },
]

export default defineComponent({
  name: 'CommissionKanban',
  props: {
    commissions: {
      type: Array as PropType<CommissionProject[]>,
      required: true,
    },
    loading: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['select', 'status-update'],
  setup(props, { emit }) {
    const colDragOver = ref<string | null>(null)
    const draggedId = ref<string | null>(null)
    const draggedData = ref<CommissionProject | null>(null)

    const columns = computed<KanbanColumn[]>(() => {
      const items = Array.isArray(props.commissions) ? props.commissions : []
      return TRANSITIONS.map((col) => ({
        ...col,
        nextTransition: col.nextTransition?.map((req) => {
          let met = false
          // Calculate blockers per-card based on the first item in this column
          const columnItems = items.filter((c) => c.status === col.key)
          const sampleItem = columnItems[0]
          if (sampleItem) {
            const m = sampleItem.milestones
            if (req.condition === 'milestone_created' && m && m.some((mi) => mi)) met = true
            if (req.condition === 'final_delivery' && m && m.length > 0) met = true
            if (req.condition === 'all_payments_received') met = true
            if (req.condition === 'deposit_received') met = true
          }
          return { ...req, met }
        }),
      }))
    })

    function getColumnItems(key: string): CommissionProject[] {
      const items = Array.isArray(props.commissions) ? props.commissions : []
      return items.filter((c) => c.status === key)
    }

    function onDragStart(e: DragEvent, item: CommissionProject) {
      draggedId.value = item.id
      draggedData.value = item
      e.dataTransfer!.effectAllowed = 'move'
      e.dataTransfer!.setData('text/plain', item.id)
    }

    function onDragOver(e: DragEvent, _colKey: string) {
      e.preventDefault()
      e.dataTransfer!.dropEffect = 'move'
      colDragOver.value = _colKey
    }

    function onDragLeave() {
      colDragOver.value = null
    }

    function onDragEnd() {
      draggedId.value = null
      draggedData.value = null
      colDragOver.value = null
    }

    function onDrop(e: DragEvent, targetCol: KanbanColumn) {
      e.preventDefault()
      colDragOver.value = null

      if (!draggedData.value) return

      const sourceCommission = draggedData.value
      const sourceStatus = sourceCommission.status
      const targetStatus = targetCol.key

      if (sourceStatus === targetStatus) return

      const targetIdx = TRANSITIONS.findIndex((c) => c.key === targetStatus)
      const sourceIdx = TRANSITIONS.findIndex((c) => c.key === sourceStatus)

      if (targetIdx === -1 || sourceIdx === -1) return

      if (targetIdx > sourceIdx + 1) {
        const src = (window as any).$toast
        src?.show('不能跳过状态，请逐步更新', 'error')
        return
      }

      const updatedCommission = {
        ...sourceCommission,
        status: targetStatus,
        updated_at: new Date().toISOString(),
      }

      emit('status-update', {
        commissionId: sourceCommission.id,
        fromStatus: sourceStatus,
        toStatus: targetStatus,
        commission: updatedCommission,
      })
    }

    function daysUntilDue(dateStr: string): number | null {
      return computeDaysUntilDue(dateStr)
    }

    function getDaysUntil(dateStr: string): number {
      return computeDaysUntilDue(dateStr) ?? 0
    }

    function dueDateClassFor(dateStr: string): string {
      const d = computeDaysUntilDue(dateStr)
      if (d === null) return ''
      if (d <= 0) return 'due-overdue'
      if (d <= 3) return 'due-soon'
      return 'due-ok'
    }

    function milestoneProgress(item: CommissionProject): number {
      if (!item.milestones || !item.milestones.length) return 0
      return computeMilestoneProgress(item.milestones)
    }

    function milestonesCompleted(item: CommissionProject): number {
      if (!item.milestones || !item.milestones.length) return 0
      return item.milestones.filter((m) => m.status === 'completed').length
    }

    return {
      columns,
      colDragOver,
      draggedId,
      draggedData,
      getColumnItems,
      onDragStart,
      onDragOver,
      onDragLeave,
      onDragEnd,
      onDrop,
      daysUntilDue,
      getDaysUntil,
      dueDateClassFor,
      milestoneProgress,
      milestonesCompleted,
    }
  },
})
</script>

<style scoped>
/* Kanban Board */
.kanban-board {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  padding-bottom: 12px;
  min-height: 520px;
}

/* Column */
.kanban-column {
  flex: 0 0 240px;
  min-width: 220px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  display: flex;
  flex-direction: column;
  transition: border-color 0.2s ease, background 0.2s ease;
}

.kanban-column.drag-over {
  border-color: var(--accent);
  background: oklch(56% 0.12 170 / 0.04);
}

.column-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-bottom: 1px solid var(--border);
}

.column-title {
  font-weight: 700;
  font-size: 0.9rem;
}

.column-count {
  font-size: 0.75rem;
  background: var(--border);
  color: var(--muted);
  padding: 1px 8px;
  border-radius: 10px;
  font-weight: 600;
}

.column-items {
  flex: 1;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
  min-height: 100px;
}

.column-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 60px;
  font-size: 0.82rem;
  color: var(--muted);
}

/* Cards */
.kanban-card {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 12px;
  cursor: grab;
  transition: all 0.15s ease;
  border-left: 3px solid transparent;
}

.kanban-card:hover {
  box-shadow: 0 2px 10px oklch(0 0 0 / 0.06);
  transform: translateY(-1px);
}

.kanban-card:active {
  cursor: grabbing;
}

.kanban-card.card-dragging {
  opacity: 0.5;
  transform: rotate(2deg);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
  gap: 8px;
}

.card-client {
  font-weight: 700;
  font-size: 0.88rem;
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-status-badge {
  font-size: 0.68rem;
  padding: 2px 8px;
  border-radius: 8px;
  font-weight: 600;
  flex-shrink: 0;
  white-space: nowrap;
}

.status-brief { background: oklch(62% 0.18 55 / 0.12); color: #b45309; }
.status-proposal { background: oklch(58% 0.14 245 / 0.1); color: var(--blue); }
.status-production { background: oklch(58% 0.16 280 / 0.1); color: var(--purple); }
.status-delivery { background: oklch(56% 0.12 170 / 0.12); color: #16a34a; }
.status-settlement { background: var(--border); color: var(--muted); }

.card-title {
  font-size: 0.82rem;
  color: var(--muted);
  margin-bottom: 8px;
}

.card-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 4px;
}

.card-amount {
  font-weight: 700;
  font-size: 0.95rem;
  color: var(--accent);
}

.card-due {
  font-size: 0.75rem;
  color: var(--muted);
}

.due-overdue { color: #e53e3e; font-weight: 600; }
.due-soon { color: var(--orange); font-weight: 600; }
.due-ok { color: var(--muted); }

/* Progress Bar */
.card-progress {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px solid var(--border);
}

.progress-bar-track {
  flex: 1;
  height: 6px;
  background: var(--border);
  border-radius: 3px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--grad1), var(--grad2));
  border-radius: 3px;
  transition: width 0.3s ease;
}

.progress-label {
  font-size: 0.72rem;
  color: var(--muted);
  font-weight: 600;
  white-space: nowrap;
}

/* Blockers */
.card-blockers {
  margin-top: 8px;
  padding-top: 6px;
  border-top: 1px solid var(--border);
}

.blocker-label {
  font-size: 0.7rem;
  color: var(--muted);
  margin-bottom: 4px;
}

.blocker-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.74rem;
  color: var(--muted);
  padding: 2px 0;
}

.blocker-item.blockerMet {
  color: var(--green);
}

.blocker-icon {
  font-size: 0.7rem;
}

/* Responsive */
@media (max-width: 768px) {
  .kanban-board {
    flex-direction: column;
  }
  .kanban-column {
    flex: none;
    width: 100%;
    min-height: 200px;
  }
}
</style>
