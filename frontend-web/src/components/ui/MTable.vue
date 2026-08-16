<!-- Materio Vuetify-Style Table Component -->
<template>
  <div class="m-table-wrapper">
    <table class="m-table">
      <thead>
        <tr>
          <th
            v-for="col in columns"
            :key="col.accessor"
            class="m-table__header"
            :class="{ 'm-table__header--sorted': sortKey === col.accessor }"
            @click="col.sortable ? onSort(col.accessor) : null"
          >
            <span class="m-table__header-text">{{ col.header }}</span>
            <span v-if="col.sortable" class="m-table__header-sort">
              <svg v-if="sortKey !== col.accessor" width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
                <path d="M6 2l4 4H2l4-4z"/>
              </svg>
              <svg v-else width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
                <path v-if="sortDir === 'asc'" d="M6 10l-4-4h8l-4 4z"/>
                <path v-else d="M6 2l4 4H2l4-4z"/>
              </svg>
            </span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(row, rowIndex) in sortedData"
          :key="rowIndex"
          class="m-table__row"
          :class="{ 'm-table__row--hover': hoverable, 'm-table__row--striped': rowIndex % 2 === 1 }"
        >
          <td
            v-for="col in columns"
            :key="col.accessor"
            class="m-table__cell"
          >
            <slot :name="col.accessor" :row="row" :value="row[col.accessor]">
              {{ row[col.accessor] }}
            </slot>
          </td>
        </tr>
        <tr v-if="sortedData.length === 0">
          <td :colspan="columns.length" class="m-table__empty">
            <slot name="empty">
              <span>暂无数据</span>
            </slot>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Pagination -->
    <div v-if="paginated && totalPages > 1" class="m-table__pagination">
      <span class="m-table__pagination-info">
        第 {{ (currentPage - 1) * pageSize + 1 }}-{{ Math.min(currentPage * pageSize, totalRows) }} 条，共 {{ totalRows }} 条
      </span>
      <div class="m-table__pagination-controls">
        <button class="m-table__page-btn" :disabled="currentPage === 1" @click="currentPage--">‹</button>
        <button
          v-for="page in visiblePages"
          :key="page"
          class="m-table__page-btn"
          :class="{ 'm-table__page-btn--active': page === currentPage }"
          @click="currentPage = page"
        >
          {{ page }}
        </button>
        <button class="m-table__page-btn" :disabled="currentPage === totalPages" @click="currentPage++">›</button>
      </div>
      <select v-model="pageSize" class="m-table__rows-per-page">
        <option :value="5">5 条/页</option>
        <option :value="10">10 条/页</option>
        <option :value="20">20 条/页</option>
        <option :value="50">50 条/页</option>
      </select>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

export interface TableField {
  accessor: string
  header: string
  sortable?: boolean
  width?: string
}

const props = defineProps<{
  columns: TableField[]
  data: Record<string, any>[]
  paginated?: boolean
  hoverable?: boolean
}>()

const sortKey = ref<string>('')
const sortDir = ref<'asc' | 'desc'>('asc')
const currentPage = ref(1)
const pageSize = ref(10)

const sortedData = computed(() => {
  if (!sortKey.value) return props.data
  return [...props.data].sort((a, b) => {
    const aVal = a[sortKey.value]
    const bVal = b[sortKey.value]
    if (aVal < bVal) return sortDir.value === 'asc' ? -1 : 1
    if (aVal > bVal) return sortDir.value === 'asc' ? 1 : -1
    return 0
  })
})

const totalRows = computed(() => props.data.length)
const totalPages = computed(() => Math.ceil(totalRows.value / pageSize.value))

const visiblePages = computed(() => {
  const pages = []
  const total = totalPages.value
  const current = currentPage.value
  const start = Math.max(1, current - 2)
  const end = Math.min(total, start + 4)
  for (let i = start; i <= end; i++) pages.push(i)
  return pages
})

const onSort = (accessor: string) => {
  if (sortKey.value === accessor) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = accessor
    sortDir.value = 'asc'
  }
  currentPage.value = 1
}
</script>

<style scoped>
.m-table-wrapper {
  width: 100%;
  background: var(--m-surface);
  border-radius: var(--m-radius-lg);
  overflow: hidden;
  border: 1px solid var(--m-border);
}

.m-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--m-font-size-base);
}

/* ── Header ── */
.m-table__header {
  background: #f6f7fb;
  padding: 0.75rem 1rem;
  font-weight: var(--m-font-weight-semibold);
  font-size: var(--m-font-size-sm);
  color: var(--m-on-surface);
  text-align: left;
  border-bottom: 1px solid var(--m-border);
  white-space: nowrap;
  cursor: default;
  user-select: none;
}
.m-table__header--sorted {
  color: rgb(var(--m-primary-rgb, 85, 133, 255));
}
.m-table__header:hover {
  background: #eef0f4;
}
.m-table__header-text {
  display: inline;
}
.m-table__header-sort {
  display: inline-flex;
  margin-inline-start: 0.25rem;
  opacity: 0.5;
}
.m-table__header-sort svg {
  transition: transform var(--m-transition-fast, 150ms);
  display: inline-block;
}
.m-table__row--striped {
  background: rgba(var(--m-primary-rgb, 85, 133, 255), 0.02);
}
.m-table__row--striped:hover {
  background: rgba(var(--m-primary-rgb, 85, 133, 255), 0.05);
}

/* ── Body ── */
.m-table__row {
  border-bottom: 1px solid var(--m-border);
  transition: background var(--m-transition-fast);
}
.m-table__row:last-child {
  border-bottom: none;
}
.m-table__row--hover:hover {
  background: rgba(var(--m-primary-rgb, 85, 133, 255), 0.04);
}
.m-table__cell {
  padding: 0.75rem 1rem;
  color: var(--m-on-surface);
  vertical-align: middle;
}

/* ── Empty State ── */
.m-table__empty {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--m-grey-500);
  font-size: var(--m-font-size-sm);
}

/* ── Pagination ── */
.m-table__pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  border-top: 1px solid var(--m-border);
  flex-wrap: wrap;
  gap: 0.5rem;
}
.m-table__pagination-info {
  font-size: var(--m-font-size-sm);
  color: var(--m-grey-600);
}
.m-table__pagination-controls {
  display: flex;
  gap: 0.25rem;
}
.m-table__page-btn {
  min-width: 32px;
  height: 32px;
  padding: 0 0.5rem;
  border: 1px solid var(--m-border);
  border-radius: var(--m-radius-sm);
  background: var(--m-surface);
  color: var(--m-on-surface);
  font-size: var(--m-font-size-sm);
  cursor: pointer;
  transition: all var(--m-transition-fast);
}
.m-table__page-btn:hover:not(:disabled) {
  border-color: rgb(var(--m-primary-rgb, 85, 133, 255));
  color: rgb(var(--m-primary-rgb, 85, 133, 255));
}
.m-table__page-btn--active {
  background: rgb(var(--m-primary-rgb, 85, 133, 255));
  border-color: rgb(var(--m-primary-rgb, 85, 133, 255));
  color: var(--m-on-primary);
}
.m-table__page-btn:disabled {
  opacity: var(--m-disabled-opacity);
  cursor: not-allowed;
}
.m-table__rows-per-page {
  height: 32px;
  padding: 0 0.5rem;
  border: 1px solid var(--m-border);
  border-radius: var(--m-radius-sm);
  font-size: var(--m-font-size-sm);
  color: var(--m-on-surface);
  background: var(--m-surface);
  cursor: pointer;
}
</style>
