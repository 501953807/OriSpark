<!-- Materio Vuetify-Style Tabs Component -->
<template>
  <div class="m-tabs">
    <div class="m-tabs__bar" ref="barRef">
      <button
        v-for="(tab, index) in tabs"
        :key="tab.value"
        class="m-tabs__item"
        :class="{ 'm-tabs__item--active': modelValue === tab.value }"
        @click="select(index)"
        @mouseenter="onHover(index)"
        @mouseleave="resetIndicator"
      >
        <i v-if="tab.icon" class="material-icons m-tabs__item-icon">{{ tab.icon }}</i>
        <span class="m-tabs__item-label">{{ tab.label }}</span>
        <span v-if="tab.badge" class="m-tabs__item-badge">{{ tab.badge }}</span>
      </button>
      <div class="m-tabs__indicator" :style="indicatorStyle" />
    </div>
    <div class="m-tabs__content">
      <slot :name="modelValue" :value="modelValue" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'

interface Tab {
  value: string
  label: string
  icon?: string
  badge?: string
}

const props = defineProps<{
  modelValue: string
  tabs: Tab[]
}>()

const emit = defineEmits<{ (e: 'update:modelValue', value: string): void }>()

const barRef = ref<HTMLElement | null>(null)
const indicatorStyle = ref({ left: '0px', width: '0px' })
const isHovering = ref(false)

function select(index: number) {
  const tab = props.tabs[index]
  if (tab) emit('update:modelValue', tab.value)
}

function positionIndicator(el: Element) {
  if (!barRef.value) return
  const barRect = barRef.value.getBoundingClientRect()
  const tabRect = el.getBoundingClientRect()
  indicatorStyle.value = {
    left: (tabRect.left - barRect.left) + 'px',
    width: tabRect.width + 'px',
  }
}

function onHover(index: number) {
  isHovering.value = true
  const items = barRef.value?.querySelectorAll('.m-tabs__item')
  if (items?.[index]) positionIndicator(items[index])
}

function resetIndicator() {
  isHovering.value = false
  const activeItem = barRef.value?.querySelector('.m-tabs__item--active')
  if (activeItem) positionIndicator(activeItem)
}

watch(() => props.modelValue, () => {
  if (!isHovering.value) {
    const items = barRef.value?.querySelectorAll('.m-tabs__item')
    const currentIndex = props.tabs.findIndex(t => t.value === props.modelValue)
    if (items?.[currentIndex]) positionIndicator(items[currentIndex])
  }
})

onMounted(() => {
  const items = barRef.value?.querySelectorAll('.m-tabs__item')
  const currentIndex = props.tabs.findIndex(t => t.value === props.modelValue)
  if (items?.[currentIndex]) positionIndicator(items[currentIndex])
})

onBeforeUnmount(() => { isHovering.value = false })
</script>

<style scoped>
.m-tabs { width: 100%; }
.m-tabs__bar {
  position: relative;
  display: flex;
  border-bottom: 1px solid var(--m-border, rgba(46, 38, 61, 0.12));
  gap: 0;
}
.m-tabs__item {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.75rem 1.25rem;
  font-size: var(--m-font-size-base, 0.9375rem);
  font-weight: var(--m-font-weight-medium, 500);
  color: var(--m-grey-600, #757575);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: color var(--m-transition-fast, 150ms);
  white-space: nowrap;
  position: relative;
  z-index: 1;
}
.m-tabs__item:hover { color: var(--m-on-surface, #2E263D); }
.m-tabs__item--active { color: rgb(var(--m-primary-rgb, 85, 133, 255)); }
.m-tabs__item-icon { font-size: 18px; }
.m-tabs__item-badge {
  background: rgba(var(--m-primary-rgb, 85, 133, 255), 0.12);
  color: rgb(var(--m-primary-rgb, 85, 133, 255));
  font-size: 0.6875rem;
  font-weight: 600;
  padding: 0.1rem 0.375rem;
  border-radius: var(--m-radius-full, 9999px);
}
.m-tabs__indicator {
  position: absolute;
  bottom: -1px;
  left: 0;
  height: 2px;
  background: rgb(var(--m-primary-rgb, 85, 133, 255));
  border-radius: 2px 2px 0 0;
  transition: left 250ms cubic-bezier(0.4, 0, 0.2, 1),
              width 250ms cubic-bezier(0.4, 0, 0.2, 1);
}
.m-tabs__content { padding-top: 1rem; }
</style>
