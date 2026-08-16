<!-- Materio Tabs Component -->
<template>
  <div class="m-tabs">
    <div class="m-tabs__nav" :class="{ 'm-tabs__nav--stretched': stretched }">
      <button
        v-for="(tab, i) in tabs" :key="tab.value ?? i"
        class="m-tabs__item"
        :class="{ 'm-tabs__item--active': modelValue === (tab.value ?? i) }"
        @click="$emit('update:modelValue', tab.value ?? i)"
      >
        <span v-if="tab.icon" class="m-tabs__icon"><slot :name="`icon-${tab.value ?? i}`" :tab="tab" /></span>
        <span class="m-tabs__label">{{ tab.label }}</span>
        <span v-if="tab.badge !== undefined" class="m-tabs__badge">{{ tab.badge }}</span>
      </button>
      <div class="m-tabs__indicator" :style="{ left: indicatorLeft, width: indicatorWidth }" />
    </div>
    <div class="m-tabs__content"><slot /></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
defineProps<{
  modelValue?: string | number
  tabs: { label: string; value?: string | number; badge?: number | string; icon?: boolean }[]
  stretched?: boolean
}>()
defineEmits<{ (e: 'update:modelValue', v: string | number): void }>()
const indicatorLeft = ref('0px')
const indicatorWidth = ref('0px')
const navEl = ref<HTMLElement | null>(null)
function updateIndicator(index: number) {
  requestAnimationFrame(() => {
    if (!navEl.value) return
    const items = navEl.value.querySelectorAll('.m-tabs__item')
    const item = items[index] as HTMLElement | undefined
    if (!item) return
    const navRect = navEl.value.getBoundingClientRect()
    const itemRect = item.getBoundingClientRect()
    indicatorLeft.value = `${itemRect.left - navRect.left}px`
    indicatorWidth.value = `${itemRect.width}px`
  })
}
onMounted(() => updateIndicator(0))
watch(() => props.modelValue, () => {
  const idx = (props.tabs.map(t => t.value ?? String(t.label)).indexOf(String(props.modelValue)))
  updateIndicator(Math.max(0, idx))
})
</script>

<style scoped>
.m-tabs { width: 100%; }
.m-tabs__nav {
  display: flex; gap: 0;
  border-bottom: 2px solid var(--m-border);
  position: relative;
  overflow-x: auto;
}
.m-tabs__nav--stretched { flex-wrap: nowrap; }
.m-tabs__item {
  position: relative;
  padding: 12px 20px;
  font-size: 14px; font-weight: 500;
  color: var(--m-grey-500);
  background: none; border: none; cursor: pointer;
  white-space: nowrap;
  display: flex; align-items: center; gap: 6px;
  transition: color var(--m-transition-fast);
  font-family: var(--m-font-family);
}
.m-tabs__item:hover { color: var(--m-primary); }
.m-tabs__item--active { color: var(--m-primary); }
.m-tabs__indicator {
  position: absolute; bottom: -2px; left: 0;
  height: 2px; background: var(--m-primary);
  transition: left 200ms ease, width 200ms ease;
  border-radius: 2px 2px 0 0;
}
.m-tabs__icon { display: flex; }
.m-tabs__badge {
  background: var(--m-error); color: #fff;
  font-size: 11px; font-weight: 600;
  padding: 1px 6px; border-radius: 100px;
  min-width: 18px; text-align: center;
}
.m-tabs__content { padding-top: 16px; }
</style>
