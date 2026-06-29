<template>
  <div class="virtual-scroll-container" ref="containerRef" @scroll="onScroll">
    <div class="virtual-spacer" :style="{ height: totalHeight + 'px' }"></div>
    <div class="virtual-content" :style="{ transform: `translateY(${offsetY}px)` }">
      <slot :items="visibleItems" />
    </div>
  </div>
</template>

<script setup lang="ts" generic="T">
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = withDefaults(defineProps<{
  items: T[]
  itemHeight?: number
  overscan?: number
}>(), {
  itemHeight: 72,
  overscan: 5,
})

const containerRef = ref<HTMLElement>()
const scrollTop = ref(0)
const containerHeight = ref(600)

const totalHeight = computed(() => props.items.length * props.itemHeight)

const startIndex = computed(() => Math.max(0, Math.floor(scrollTop.value / props.itemHeight) - props.overscan))

const endIndex = computed(() => Math.min(
  props.items.length,
  Math.ceil((scrollTop.value + containerHeight.value) / props.itemHeight) + props.overscan,
))

const visibleItems = computed(() => props.items.slice(startIndex.value, endIndex.value))

const offsetY = computed(() => startIndex.value * props.itemHeight)

function onScroll() {
  if (containerRef.value) {
    scrollTop.value = containerRef.value.scrollTop
  }
}

let resizeObs: ResizeObserver | null = null

onMounted(() => {
  if (containerRef.value) {
    containerHeight.value = containerRef.value.clientHeight
    resizeObs = new ResizeObserver(entries => {
      containerHeight.value = entries[0].contentRect.height
    })
    resizeObs.observe(containerRef.value)
  }
})

onUnmounted(() => resizeObs?.disconnect())
</script>

<style scoped>
.virtual-scroll-container {
  overflow-y: auto;
  position: relative;
  min-height: 200px;
}
.virtual-spacer {
  width: 1px;
}
.virtual-content {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
}
</style>
