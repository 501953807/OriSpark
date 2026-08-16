<!-- Materio Tooltip Component -->
<template>
  <span class="m-tooltip-host" ref="host" @mouseenter="show" @mouseleave="hide" @focus="show" @blur="hide">
    <slot />
    <transition name="m-tooltip-fade">
      <span v-if="visible" class="m-tooltip" :class="`m-tooltip--${position}`" :style="{ '--tx': offsetX + 'px', '--ty': offsetY + 'px' }">
        {{ text }}
      </span>
    </transition>
  </span>
</template>

<script setup lang="ts">
import { ref } from 'vue'
const props = defineProps<{
  text: string
  position?: 'top' | 'bottom' | 'left' | 'right'
}>()
const visible = ref(false)
let timer: ReturnType<typeof setTimeout> | null = null
const host = ref<HTMLElement | null>(null)
function show() {
  if (timer) clearTimeout(timer)
  visible.value = true
}
function hide() {
  timer = setTimeout(() => { visible.value = false }, 100)
}
</script>

<style scoped>
.m-tooltip-host { position: relative; display: inline-flex; }
.m-tooltip {
  position: absolute; z-index: 100;
  background: rgba(46, 38, 61, 0.9);
  color: #fff;
  padding: 6px 12px;
  border-radius: var(--m-radius-sm);
  font-size: 12px;
  white-space: nowrap;
  pointer-events: none;
  opacity: 0;
  transition: opacity var(--m-transition-fast);
}
.m-tooltip--top { bottom: calc(100% + 8px); left: 50%; transform: translateX(-50%); }
.m-tooltip--bottom { top: calc(100% + 8px); left: 50%; transform: translateX(-50%); }
.m-tooltip--left { right: calc(100% + 8px); top: 50%; transform: translateY(-50%); }
.m-tooltip--right { left: calc(100% + 8px); top: 50%; transform: translateY(-50%); }
.m-tooltip-fade-enter-active, .m-tooltip-fade-leave-active { transition: opacity var(--m-transition-fast); }
.m-tooltip-fade-enter-from, .m-tooltip-fade-leave-to { opacity: 0; }
</style>
