<template>
  <div class="calendar-view">
    <!-- Month navigation -->
    <div class="cal-nav">
      <button class="btn btn-ghost cal-nav-btn" :disabled="!canGoPrev" @click="prevMonth">&#8249;</button>
      <span class="cal-title">{{ currentYear }}年{{ currentMonth + 1 }}月</span>
      <button class="btn btn-ghost cal-nav-btn" @click="nextMonth">&#8250;</button>
    </div>

    <!-- Event legend -->
    <div class="cal-legend">
      <span class="legend-item"><span class="legend-dot legend-milestone"></span>里程碑</span>
      <span class="legend-item"><span class="legend-dot legend-payment"></span>收款</span>
      <span class="legend-item"><span class="legend-dot legend-deadline"></span>截止日</span>
    </div>

    <div class="cal-layout">
      <!-- Calendar grid -->
      <div class="cal-grid-wrapper">
        <div class="cal-weekdays">
          <div v-for="d in weekDays" :key="d" class="cal-wd">{{ d }}</div>
        </div>
        <div class="cal-days" role="grid">
          <!-- Padding cells for days before the first -->
          <div
            v-for="pad in firstDayOfWeek"
            :key="'pad-' + pad"
            class="cal-cell cal-empty"
          ></div>

          <!-- Day cells -->
          <div
            v-for="day in monthDays"
            :key="day"
            :class="[
              'cal-cell',
              { 'cal-today': isToday(day), 'cal-selected': selectedDate === formatDateStr(currentYear, currentMonth, day) },
            ]"
            role="gridcell"
            @click="selectDate(day)"
          >
            <span class="cal-day-num">{{ day }}</span>
            <div v-if="eventsForDay(day).length > 0" class="cal-event-indicators">
              <span
                v-for="ev in eventsForDay(day).slice(0, 3)"
                :key="ev.id"
                class="cal-event-dot"
                :class="dotClassFor(ev.type)"
              ></span>
              <span v-if="eventsForDay(day).length > 3" class="cal-more-num">+{{ eventsForDay(day).length - 3 }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Side panel: events for selected date -->
      <div v-if="selectedDateStr" class="cal-panel">
        <div class="cal-panel-header">
          <span class="cal-panel-date">{{ selectedDateStr }}</span>
          <button class="btn btn-ghost cal-panel-close" @click="selectedDateStr = null">&times;</button>
        </div>
        <div class="cal-panel-body">
          <div v-if="selectedEvents.length === 0" class="cal-panel-empty">当日无事件</div>
          <div v-else class="cal-event-list">
            <div
              v-for="ev in selectedEvents"
              :key="ev.id"
              class="cal-event-card"
              :class="cardClassFor(ev.type)"
            >
              <span class="cal-event-type-label">{{ typeLabel(ev.type) }}</span>
              <div class="cal-event-title">{{ ev.title }}</div>
              <div class="cal-event-date">{{ ev.date }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { CalendarEvent } from '@/types/commission'

interface Props {
  events: CalendarEvent[]
  loading: boolean
}

const props = defineProps<Props>()

const selectedDate = ref<string | null>(null)
const currentMonth = ref(new Date().getMonth())
const currentYear = ref(new Date().getFullYear())

const weekDays = ['日', '一', '二', '三', '四', '五', '六']

const firstDayOfWeek = computed(() => {
  return new Date(currentYear.value, currentMonth.value, 1).getDay()
})

const monthDays = computed(() => {
  return new Date(currentYear.value, currentMonth.value + 1, 0).getDate()
})

const canGoPrev = computed(() => {
  const now = new Date()
  return !(currentYear.value === now.getFullYear() && currentMonth.value === now.getMonth())
})

function formatDateStr(year: number, month: number, day: number): string {
  return `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
}

function isToday(day: number): boolean {
  const now = new Date()
  return now.getFullYear() === currentYear.value && now.getMonth() === currentMonth.value && now.getDate() === day
}

function eventsForDay(day: number): CalendarEvent[] {
  const dateStr = formatDateStr(currentYear.value, currentMonth.value, day)
  return props.events.filter((ev) => ev.date === dateStr)
}

function selectDate(day: number) {
  const dateStr = formatDateStr(currentYear.value, currentMonth.value, day)
  if (selectedDate.value === dateStr) {
    selectedDate.value = null
  } else {
    selectedDate.value = dateStr
  }
}

const selectedDateStr = computed<string | null>(() => selectedDate.value)

const selectedEvents = computed(() => {
  if (!selectedDate.value) return []
  return props.events.filter((ev) => ev.date === selectedDate.value)
})

function prevMonth() {
  if (!canGoPrev.value) return
  if (currentMonth.value === 0) {
    currentMonth.value = 11
    currentYear.value -= 1
  } else {
    currentMonth.value -= 1
  }
  selectedDate.value = null
}

function nextMonth() {
  if (currentMonth.value === 11) {
    currentMonth.value = 0
    currentYear.value += 1
  } else {
    currentMonth.value += 1
  }
  selectedDate.value = null
}

function dotClassFor(type: string): string {
  switch (type) {
    case 'milestone_due':
      return 'dot-milestone'
    case 'payment_received':
      return 'dot-payment'
    default:
      return 'dot-milestone'
  }
}

function cardClassFor(type: string): string {
  switch (type) {
    case 'milestone_due':
      return 'evt-milestone'
    case 'payment_received':
      return 'evt-payment'
    default:
      return 'evt-milestone'
  }
}

function typeLabel(type: string): string {
  switch (type) {
    case 'milestone_due':
      return '里程碑'
    case 'payment_received':
      return '收款'
    default:
      return type
  }
}
</script>

<style scoped>
.calendar-view {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Nav */
.cal-nav {
  display: flex;
  align-items: center;
  gap: 12px;
}
.cal-nav-btn {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  font-size: 1.1rem;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
.cal-nav-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}
.cal-title {
  font-size: 1.05rem;
  font-weight: 700;
  flex: 1;
  text-align: center;
}

/* Legend */
.cal-legend {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.78rem;
  color: var(--muted);
}
.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}
.legend-milestone { background: #3b82f6; }
.legend-payment { background: #16a34a; }
.legend-deadline { background: #ef4444; }

/* Layout: grid + panel */
.cal-layout {
  display: flex;
  gap: 16px;
  min-height: 340px;
}
.cal-grid-wrapper {
  flex: 1;
  min-width: 0;
}

/* Weekday headers */
.cal-weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 1px;
}
.cal-wd {
  text-align: center;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--muted);
  padding: 6px 0;
  text-transform: uppercase;
}

/* Day grid */
.cal-days {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 1px;
  background: var(--border);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}
.cal-cell {
  background: var(--surface);
  min-height: 72px;
  padding: 4px 6px;
  cursor: pointer;
  transition: background 0.12s ease;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.cal-cell:hover {
  background: oklch(95% 0.003 240);
}
.cal-cell.cal-empty {
  background: var(--bg);
  cursor: default;
}
.cal-cell.cal-empty:hover {
  background: var(--bg);
}
.cal-cell.cal-today .cal-day-num {
  background: var(--accent);
  color: #fff;
}
.cal-cell.cal-selected {
  border: 2px solid var(--accent);
}
.cal-day-num {
  font-size: 0.82rem;
  font-weight: 600;
  line-height: 1;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}
.cal-event-indicators {
  display: flex;
  gap: 3px;
  flex-wrap: wrap;
  margin-top: 2px;
}
.cal-event-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  display: inline-block;
}
.dot-milestone { background: #3b82f6; }
.dot-payment { background: #16a34a; }
.cal-more-num {
  font-size: 0.65rem;
  color: var(--muted);
  font-weight: 600;
}

/* Side panel */
.cal-panel {
  width: 240px;
  flex-shrink: 0;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.cal-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
}
.cal-panel-date {
  font-size: 0.85rem;
  font-weight: 700;
}
.cal-panel-close {
  width: 24px;
  height: 24px;
  font-size: 1.1rem;
  line-height: 1;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
}
.cal-panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}
.cal-panel-empty {
  font-size: 0.82rem;
  color: var(--muted);
  text-align: center;
  padding: 24px 0;
}

/* Event cards in panel */
.cal-event-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.cal-event-card {
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  border-left: 3px solid transparent;
}
.evt-milestone {
  background: oklch(58% 0.14 245 / 0.07);
  border-left-color: #3b82f6;
}
.evt-payment {
  background: oklch(56% 0.12 170 / 0.07);
  border-left-color: #16a34a;
}
.cal-event-type-label {
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.evt-milestone .cal-event-type-label { color: #3b82f6; }
.evt-payment .cal-event-type-label { color: #16a34a; }
.cal-event-title {
  font-size: 0.85rem;
  font-weight: 600;
  margin-top: 4px;
}
.cal-event-date {
  font-size: 0.72rem;
  color: var(--muted);
  margin-top: 2px;
}

@media (max-width: 768px) {
  .cal-layout {
    flex-direction: column;
  }
  .cal-panel {
    width: 100%;
  }
  .cal-cell {
    min-height: 52px;
  }
}
</style>
