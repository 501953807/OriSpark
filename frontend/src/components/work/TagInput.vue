<template>
  <div class="tag-input">
    <div class="tag-pills">
      <span
        v-for="(tag, i) in tags"
        :key="tag.id || tag.tag || i"
        class="tag-pill"
      >
        <span class="tag-label">{{ tag.tag }}</span>
        <button class="tag-remove" @click.stop="removeTag(i)" title="移除">×</button>
      </span>
    </div>
    <div class="tag-input-wrap">
      <input
        ref="inputRef"
        v-model="inputVal"
        @input="onInput(inputVal)"
        @keydown="onKeydown($event)"
        @focus="showSuggestions = suggestions.length > 0"
        placeholder="输入标签…"
        class="tag-field"
      />
      <div v-if="showSuggestions && suggestions.length" class="suggestions-dropdown">
        <div
          v-for="(s, i) in suggestions"
          :key="s"
          class="suggestion-item"
          :class="{ selected: i === selectedIdx }"
          @mouseenter="selectedIdx = i"
          @click="addSuggestion(i)"
        >
          {{ s }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { TagItem } from '@/composables/useTagInput'

const props = defineProps<{
  modelValue?: TagItem[]
}>()

const emit = defineEmits<{
  'update:modelValue': [val: TagItem[]]
}>()

const tags = ref<TagItem[]>(props.modelValue || [])
const inputVal = ref('')
const suggestions = ref<string[]>([])
const showSuggestions = ref(false)
const selectedIdx = ref(0)
const inputRef = ref<HTMLInputElement | null>(null)

watch(() => props.modelValue, (v) => {
  if (v) tags.value = v.map(t => ({ ...t }))
}, { immediate: true })

function onInput(val: string) {
  inputVal.value = val
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && inputVal.value.trim()) {
    e.preventDefault()
    addTag(inputVal.value.trim())
    inputVal.value = ''
    showSuggestions.value = false
    selectedIdx.value = 0
  } else if (e.key === 'Backspace' && !inputVal.value && tags.value.length > 0) {
    removeTag(tags.value.length - 1)
  } else if (e.key === 'Escape') {
    showSuggestions.value = false
  } else if (e.key === 'ArrowDown' && showSuggestions.value) {
    e.preventDefault()
    selectedIdx.value = Math.min(selectedIdx.value + 1, suggestions.value.length - 1)
  } else if (e.key === 'ArrowUp' && showSuggestions.value) {
    e.preventDefault()
    selectedIdx.value = Math.max(selectedIdx.value - 1, 0)
  } else if ((e.key === 'Enter' || e.key === 'Tab') && showSuggestions.value && suggestions.value.length > 0) {
    e.preventDefault()
    addSuggestion(selectedIdx.value)
  }
}

function addTag(label: string) {
  if (tags.value.some(t => t.tag === label)) return
  tags.value.push({ id: '', tag: label })
  emit('update:modelValue', [...tags.value])
  suggestions.value = []
  showSuggestions.value = false
}

function addSuggestion(index: number) {
  addTag(suggestions.value[index])
}

function removeTag(index: number) {
  tags.value.splice(index, 1)
  emit('update:modelValue', [...tags.value])
}
</script>

<style scoped>
.tag-input {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tag-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.tag-pill {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 2px 6px 2px 8px;
  border-radius: 100px;
  font-size: 0.75rem;
  background: oklch(56% 0.12 170 / 0.1);
  color: var(--accent);
}

.tag-label {
  font-weight: 500;
}

.tag-remove {
  background: none;
  border: none;
  cursor: pointer;
  color: inherit;
  font-size: 0.9rem;
  padding: 0 2px;
  line-height: 1;
  opacity: 0.6;
}

.tag-remove:hover {
  opacity: 1;
}

.tag-input-wrap {
  position: relative;
}

.tag-field {
  width: 100%;
  padding: 6px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  font-family: var(--font-body);
  color: var(--fg);
  background: var(--surface);
  outline: none;
}

.tag-field:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px oklch(56% 0.12 170 / 0.1);
}

.suggestions-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  box-shadow: 0 4px 12px oklch(0 0 0 / 0.1);
  z-index: 10;
  max-height: 160px;
  overflow-y: auto;
}

.suggestion-item {
  padding: 6px 10px;
  font-size: 0.82rem;
  cursor: pointer;
}

.suggestion-item:hover,
.suggestion-item.selected {
  background: oklch(56% 0.12 170 / 0.08);
}
</style>
