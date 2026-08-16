<!-- Materio Select Component -->
<template>
  <div class="m-select" :class="{ 'm-select--focused': isOpen, 'm-select--error': !!error, 'm-select--disabled': disabled }">
    <div class="m-select__trigger" @click="toggle">
      <span class="m-select__value" :class="{ 'm-select__placeholder': !modelValue }">
        {{ displayValue || placeholder || '请选择…' }}
      </span>
      <svg class="m-select__arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
        <polyline points="6 9 12 15 18 9"/>
      </svg>
    </div>
    <transition name="m-select-drop">
      <ul v-if="isOpen" class="m-select__dropdown" @click.outside="close">
        <li v-if="!modelValue" class="m-select__empty">{{ placeholder || '请选择…' }}</li>
        <li v-for="opt in options" :key="opt.value"
            class="m-select__option"
            :class="{ 'm-select__option--active': opt.value === modelValue, 'm-select__option--disabled': opt.disabled }"
            @click="select(opt)">
          <slot :name="`option-${opt.value}`" :option="opt">
            {{ opt.label ?? opt.text }}
          </slot>
        </li>
      </ul>
    </transition>
    <div v-if="error" class="m-select__error">{{ error }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
const props = defineProps<{
  modelValue?: string | number
  options: { value: string | number; label?: string; text?: string; disabled?: boolean }[]
  placeholder?: string
  error?: string
  disabled?: boolean
}>()
defineEmits<{ (e: 'update:modelValue', v: string | number): void }>()
const isOpen = ref(false)
const displayValue = ref('')
function toggle() { if (!props.disabled) isOpen.value = !isOpen.value }
function close() { isOpen.value = false }
function select(opt: any) {
  if (opt.disabled) return
  isOpen.value = false
  displayValue.value = opt.label ?? opt.text ?? String(opt.value)
  emit('update:modelValue', opt.value)
}
</script>

<style scoped>
.m-select { position: relative; width: 100%; font-family: var(--m-font-family); }
.m-select__trigger {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 12px;
  border: 1px solid var(--m-border);
  border-radius: var(--m-radius-sm);
  background: var(--m-surface);
  cursor: pointer;
  transition: border-color var(--m-transition-fast);
  font-size: 14px; color: var(--m-on-surface);
}
.m-select--focused .m-select__trigger { border-color: var(--m-primary); border-width: 2px; padding: 9px 11px; }
.m-select__placeholder { color: var(--m-grey-500); }
.m-select__arrow { color: var(--m-grey-500); transition: transform var(--m-transition-fast); }
.m-select--focused .m-select__arrow { transform: rotate(180deg); color: var(--m-primary); }
.m-select__dropdown {
  position: absolute; top: calc(100% + 4px); left: 0; right: 0;
  background: var(--m-surface); border: 1px solid var(--m-border);
  border-radius: var(--m-radius-sm);
  box-shadow: var(--m-shadow-md);
  list-style: none; margin: 0; padding: 4px 0;
  z-index: 50; max-height: 240px; overflow-y: auto;
}
.m-select__option {
  padding: 8px 12px; cursor: pointer; font-size: 14px; color: var(--m-on-surface);
  transition: background var(--m-transition-fast);
}
.m-select__option:hover:not(.m-select__option--disabled) { background: var(--m-primary-light); color: var(--m-primary); }
.m-select__option--active { background: var(--m-primary-light); color: var(--m-primary); font-weight: 500; }
.m-select__option--disabled { opacity: var(--m-disabled-opacity); cursor: not-allowed; }
.m-select__empty { padding: 8px 12px; color: var(--m-grey-500); font-size: 13px; }
.m-select--error .m-select__trigger { border-color: var(--m-error); border-width: 2px; padding: 9px 11px; }
.m-select__error { font-size: 12px; color: var(--m-error); margin-top: 4px; }
.m-select--disabled .m-select__trigger { opacity: var(--m-disabled-opacity); cursor: not-allowed; }
.m-select-drop-enter-active, .m-select-drop-leave-active { transition: all var(--m-transition-fast); }
.m-select-drop-enter-from, .m-select-drop-leave-to { opacity: 0; transform: translateY(-4px); }
</style>
