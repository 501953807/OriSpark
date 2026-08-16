<!-- Materio Vuetify-Style Input Component -->
<template>
  <div class="m-field" :class="[
    `m-field--variant-${variant}`,
    { 'm-field--focused': isFocused },
    { 'm-field--error': !!error },
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
        :class="{ 'm-field__input--error': !!error }"
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
  display: flex; align-items: center; gap: 3px;
  padding-inline-start: 12px;
  font-size: 14px;
  color: var(--m-grey-500);
  pointer-events: none;
  transform-origin: left top;
  transition: all var(--m-transition-fast);
}
.m-field__required { color: var(--m-error); font-size: 12px; }
.m-field__wrapper {
  position: relative; display: flex; align-items: center;
  min-height: 48px;
  border: 1px solid var(--m-border);
  border-radius: var(--m-radius-sm);
  transition: border-color var(--m-transition-fast);
  overflow: hidden;
  background: var(--m-surface);
}
.m-field--focused .m-field__wrapper {
  border-color: var(--m-primary);
  border-width: 2px;
  padding: 0;
}
.m-field--error .m-field__wrapper {
  border-color: var(--m-error);
  border-width: 2px;
  padding: 0;
}
.m-field__input {
  flex: 1; width: 100%; height: 100%;
  padding: 16px 12px 8px;
  font-size: 14px; font-family: var(--m-font-family);
  color: var(--m-on-surface); background: transparent;
  border: none; outline: none;
}
.m-field__input::placeholder { color: transparent; }
.m-field__input--error { color: var(--m-error); }
.m-field--disabled .m-field__input { opacity: var(--m-disabled-opacity); cursor: not-allowed; }
.m-field__label--floating {
  transform: translateY(-16px) scale(0.8);
  padding-inline-start: 8px;
  color: var(--m-primary);
}
.m-field--focused .m-field__label { color: var(--m-primary); }
.m-field--error .m-field__label { color: var(--m-error); }
.m-field--disabled .m-field__label { color: var(--m-grey-500); opacity: 0.6; }
.m-field__prefix, .m-field__suffix {
  display: flex; align-items: center; padding: 0 8px;
  color: var(--m-grey-500); font-size: 14px;
}
.m-field__hint { padding: 4px 12px; font-size: 12px; color: var(--m-grey-500); }
.m-field__error { padding: 4px 12px; font-size: 12px; color: var(--m-error); }
</style>
