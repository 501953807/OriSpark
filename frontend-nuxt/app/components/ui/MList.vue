<!-- Materio List Component -->
<template>
  <div class="m-list">
    <div v-if="$slots.header" class="m-list__header"><slot name="header" /></div>
    <div class="m-list__items">
      <div v-for="(item, i) in items" :key="i"
           class="m-list__item"
           :class="{ 'm-list__item--active': activeIndex === i, 'm-list__item--clickable': clickable }"
           @click="clickable && select(i)">
        <div v-if="$slots.default" class="m-list__item-content">
          <slot :name="`item-${i}`" :item="item" :index="i">
            {{ typeof item === 'object' ? (item.label ?? item.name ?? JSON.stringify(item)) : String(item) }}
          </slot>
        </div>
        <div v-else class="m-list__item-text">{{ typeof item === 'object' ? (item.label ?? item.name ?? JSON.stringify(item)) : String(item) }}</div>
        <div v-if="$slots.actions" class="m-list__item-actions"><slot name="actions" :item="item" :index="i" /></div>
      </div>
    </div>
    <div v-if="$slots.footer" class="m-list__footer"><slot name="footer" /></div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
defineProps<{
  items?: any[]
  clickable?: boolean
}>()
defineEmits<{ (e: 'select', index: number, item: any): void }>()
const activeIndex = ref<number | null>(null)
function select(i: number) {
  activeIndex.value = i
  emit('select', i, props.items?.[i])
}
</script>

<style scoped>
.m-list { background: var(--m-surface); border-radius: var(--m-radius-sm); box-shadow: var(--m-shadow-sm); overflow: hidden; }
.m-list__header, .m-list__footer { padding: 12px 16px; font-size: 13px; color: var(--m-grey-500); border-bottom: 1px solid var(--m-border); }
.m-list__footer { border-bottom: none; border-top: 1px solid var(--m-border); }
.m-list__items { }
.m-list__item {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--m-border);
  transition: background var(--m-transition-fast);
}
.m-list__item:last-child { border-bottom: none; }
.m-list__item:hover { background: var(--m-grey-100); }
.m-list__item--active { background: var(--m-primary-light); color: var(--m-primary); }
.m-list__item--clickable { cursor: pointer; }
.m-list__item-text { flex: 1; font-size: 14px; color: var(--m-on-surface); }
.m-list__item-content { flex: 1; }
.m-list__item-actions { display: flex; gap: 8px; }
</style>
