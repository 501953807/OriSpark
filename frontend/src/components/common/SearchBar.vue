<template>
  <div class="search-bar">
    <span class="search-icon">🔍</span>
    <input
      v-model="query"
      class="search-input"
      :placeholder="placeholder"
      @input="$emit('update:modelValue', query)"
      @keyup.enter="$emit('search', query)"
    />
    <button v-if="query" class="search-clear" @click="clearSearch">×</button>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = withDefaults(defineProps<{
  modelValue?: string
  placeholder?: string
}>(), {
  placeholder: '搜索作品名称...',
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  search: [value: string]
}>()

const query = ref(props.modelValue || '')

watch(() => props.modelValue, (val) => {
  query.value = val || ''
})

function clearSearch() {
  query.value = ''
  emit('update:modelValue', '')
  emit('search', '')
}
</script>

<style scoped>
.search-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  transition: border-color 0.2s;
}
.search-bar:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px oklch(56% 0.12 170 / 0.1);
}
.search-icon { font-size: 1rem; }
.search-input {
  flex: 1;
  border: none;
  outline: none;
  background: none;
  font-size: 0.9rem;
  color: var(--fg);
  font-family: var(--font-body);
}
.search-input::placeholder { color: var(--muted); }
.search-clear {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.2rem;
  color: var(--muted);
  padding: 0 4px;
}
</style>
