<!-- Materio Table Component -->
<template>
  <div class="m-table-wrap">
    <table class="m-table" :class="{ 'm-table--striped': striped, 'm-table--hover': hover }">
      <thead>
        <tr><th v-for="col in columns" :key="col.key" :colspan="col.colspan || undefined">{{ col.label }}</th></tr>
      </thead>
      <tbody>
        <tr v-if="$slots.default">
          <td :colspan="columns.length"><slot /></td>
        </tr>
        <tr v-for="(row, ri) in rows" :key="ri" :class="{ 'm-table--selected': selectedRows.includes(row[keyProp || '_idx']) }" @click="$emit('row-click', row, ri)">
          <td v-for="col in columns" :key="col.key" :class="col.class">
            <slot :name="col.slot || col.key" :row="row" :value="row[col.key]">
              {{ row[col.key] }}
            </slot>
          </td>
        </tr>
        <tr v-if="!rows.length && !$slots.default">
          <td :colspan="columns.length" class="m-table__empty"><slot name="empty">暂无数据</slot></td>
        </tr>
      </tbody>
    </table>
    <div v-if="pagination" class="m-table__footer">
      <span class="m-table__info">{{ (currentPage - 1) * pageSize + 1 }}–{{ Math.min(currentPage * pageSize, rows.length) }} / {{ rows.length }}</span>
      <div class="m-table__pager">
        <button class="m-table__page-btn" :disabled="currentPage <= 1" @click="$emit('update:page', currentPage - 1)">‹</button>
        <template v-for="p in visiblePages" :key="p">
          <button v-if="p !== '...'" class="m-table__page-btn" :class="{ 'm-table__page-btn--active': p === currentPage }" @click="$emit('update:page', p)">{{ p }}</button>
          <span v-else class="m-table__ellipsis">…</span>
        </template>
        <button class="m-table__page-btn" :disabled="currentPage >= totalPages" @click="$emit('update:page', currentPage + 1)">›</button>
      </div>
      <select class="m-table__size" v-model.number="pageSizeLocal" @change="$emit('update:pageSize', pageSizeLocal)">
        <option v-for="n in [10, 20, 50]" :key="n" :value="n">{{ n }}/页</option>
      </select>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
defineProps<{
  columns: { key: string; label: string; class?: string; slot?: string; colspan?: number }[]
  rows: Record<string, any>[]
  pagination?: boolean
  page?: number
  pageSize?: number
  keyProp?: string
  striped?: boolean
  hover?: boolean
}>()
defineEmits<{
  (e: 'row-click', row: any, index: number): void
  (e: 'update:page', v: number): void
  (e: 'update:pageSize', v: number): void
}>()
const currentPage = computed(() => props.page ?? 1)
const pageSizeLocal = ref(props.pageSize ?? 10)
const totalPages = computed(() => Math.ceil((props.rows ?? []).length / pageSizeLocal.value))
const selectedRows = ref<any[]>([])
const visiblePages = computed(() => {
  const total = totalPages.value, current = currentPage.value
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  const pages: (number | string)[] = [1]
  if (current > 3) pages.push('...')
  for (let i = Math.max(2, current - 1); i <= Math.min(total - 1, current + 1); i++) pages.push(i)
  if (current < total - 2) pages.push('...')
  if (total > 1) pages.push(total)
  return pages
})
</script>

<style scoped>
.m-table-wrap { width: 100%; overflow-x: auto; background: var(--m-surface); border-radius: var(--m-radius-sm); box-shadow: var(--m-shadow-sm); }
.m-table { width: 100%; border-collapse: collapse; font-size: var(--m-font-size-base); }
.m-table th { padding: 12px 16px; text-align: left; font-size: 13px; font-weight: var(--m-font-weight-semibold); color: var(--m-grey-500); background: var(--m-bg); border-bottom: 1px solid var(--m-border); white-space: nowrap; }
.m-table td { padding: 12px 16px; color: var(--m-on-surface); border-bottom: 1px solid var(--m-border); vertical-align: middle; }
.m-table--striped tbody tr:nth-child(even) { background: var(--m-grey-100); }
.m-table--hover tbody tr:hover td { background: rgba(79, 70, 229, 0.04); cursor: pointer; }
.m-table--selected td { background: rgba(79, 70, 229, 0.08); }
.m-table__empty { padding: 32px; text-align: center; color: var(--m-grey-500); font-size: var(--m-font-size-sm); }
.m-table__footer { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; border-top: 1px solid var(--m-border); font-size: var(--m-font-size-sm); color: var(--m-grey-500); }
.m-table__pager { display: flex; gap: 4px; align-items: center; }
.m-table__page-btn { width: 32px; height: 32px; border: 1px solid var(--m-border); background: var(--m-surface); border-radius: var(--m-radius-sm); color: var(--m-on-surface); cursor: pointer; font-size: 14px; display: flex; align-items: center; justify-content: center; transition: all var(--m-transition-fast); }
.m-table__page-btn:hover:not(:disabled) { background: var(--m-primary-light); border-color: var(--m-primary); color: var(--m-primary); }
.m-table__page-btn--active { background: var(--m-primary); border-color: var(--m-primary); color: #fff; }
.m-table__page-btn:disabled { opacity: var(--m-disabled-opacity); cursor: not-allowed; }
.m-table__ellipsis { padding: 0 4px; color: var(--m-grey-500); }
.m-table__size { padding: 4px 8px; border: 1px solid var(--m-border); border-radius: var(--m-radius-sm); background: var(--m-surface); color: var(--m-on-surface); font-size: 13px; cursor: pointer; }
</style>
