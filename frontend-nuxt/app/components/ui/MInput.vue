<!-- Materio Vuetify-Style Input Component (Nuxt version) -->
<template>
  <div class="m-field" :class="[
    `m-field--variant-${variant}`,
    { 'm-field--focused': isFocused },
    { 'm-field--error': error },
    { 'm-field--disabled': disabled },
  ]">
    <label v-if="label" class="m-field__label" :class="{ 'm-field__label--floating': isFocused || modelValue }">
      {{ label }}
      <span v-if="required" class="m-field__required">*</span>
    </label>
    <div class="m-field__wrapper">
      <span v-if="$slots.prefix" class="m-field__prefix"><slot name="prefix" /></span>
      <input
        v-if="!multiline"
        :type="type"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        class="m-field__input"
        :class="{ 'm-field__input--error': error }"
        @input="$emit('update:modelValue', $event.target.value)"
        @focus="isFocused = true"
        @blur="isFocused = false"
      />
      <textarea
        v-else
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        rows="3"
        class="m-field__input m-field__input--textarea"
        @input="$emit('update:modelValue', $event.target.value)"
        @focus="isFocused = true"
        @blur="isFocused = false"
      />
      <span v-if="$slots.suffix" class="m-field__suffix"><slot name="suffix" /></span>
    </div>
    <div class="m-field__underline" :class="{ 'm-field__underline--error': error }" />
    <div v-if="hint && !error" class="m-field__hint">{{ hint }}</div>
    <div v-if="error" class="m-field__error">{{ error }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
defineProps<{
  modelValue?: string
  label?: string
  placeholder?: string
  type?: string
  error?: string | boolean
  hint?: string
  disabled?: boolean
  required?: boolean
  multiline?: boolean
  variant?: 'outlined' | 'filled' | 'plain'
}>()
defineEmits<{ (e: 'update:modelValue', v: string): void }>()
const isFocused = ref(false)
</script>

<style scoped>
.m-field { position: relative; width: 100%; font-family: var(--m-font-family); }
.m-field__label {
  position: absolute; top: 0; left: 0;
  display: flex; align-items: center; gap: 0.125rem;
  padding-inline-start: 0.75rem;
  font-size: 0.9375rem;
  color: rgba(var(--m-on-surface-rgb, 46, 38, 61), 0.6);
  pointer-events: none;
  transform-origin: left top;
  transition: all var(--m-transition);
}
.m-field__required { color: var(--m-error); font-size: 0.75rem; }
.m-field__wrapper {
  position: relative; display: flex; align-items: center;
  min-height: 56px;
  border: 1px solid rgba(var(--m-on-surface-rgb, 46, 38, 61), 0.23);
  border-radius: var(--m-radius-sm);
  transition: border-color var(--m-transition);
  overflow: hidden;
}
.m-field--focused .m-field__wrapper { border-color: rgb(var(--m-primary-rgb, 140, 87, 255)); border-width: 2px; }
.m-field--error .m-field__wrapper { border-color: var(--m-error); border-width: 2px; }
.m-field__input {
  flex: 1; width: 100%; height: 100%;
  padding: 1.25rem 0.75rem 0.375rem;
  font-size: 0.9375rem; font-family: var(--m-font-family);
  color: var(--m-on-surface); background: transparent;
  border: none; outline: none;
}
.m-field__input::placeholder { color: transparent; }
.m-field__input--error { color: var(--m-error); }
.m-field--disabled .m-field__input { opacity: var(--m-disabled-opacity); cursor: not-allowed; }
.m-field__label--floating { transform: translateY(-1.25rem) scale(0.75); padding-inline-start: 0.5rem; }
.m-field--focused .m-field__label, .m-field__label--floating { color: rgb(var(--m-primary-rgb, 140, 87, 255)); }
.m-field--error .m-field__label { color: var(--m-error); }
.m-field--disabled .m-field__label { color: rgba(var(--m-on-surface-rgb, 46, 38, 61), 0.38); }
.m-field__underline {
  position: absolute; bottom: 0; left: 0; right: 0; height: 2px;
  background: rgba(var(--m-on-surface-rgb, 46, 38, 61), 0.23);
  transform: scaleX(0); transform-origin: bottom;
  transition: all var(--m-transition); border-radius: 0 0 var(--m-radius-sm) var(--m-radius-sm);
}
.m-field--focused .m-field__underline { transform: scaleX(1); background: rgb(var(--m-primary-rgb, 140, 87, 255)); }
.m-field--error .m-field__underline { background: var(--m-error); transform: scaleX(1); }
.m-field__hint { padding: 0.25rem 0.75rem; font-size: 0.75rem; color: rgba(var(--m-on-surface-rgb, 46, 38, 61), 0.6); }
.m-field__error { padding: 0.25rem 0.75rem; font-size: 0.75rem; color: var(--m-error); }
</style>
