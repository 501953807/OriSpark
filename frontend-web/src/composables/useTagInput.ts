/** 标签输入逻辑 composable.

支持标签增删、键盘快捷键、API 联想.
*/

import { ref, watch } from 'vue'
import { worksApi } from '@/api/works'

export interface TagItem {
  id: string
  tag: string
}

export function useTagInput(initialTags: TagItem[] = []) {
  const tags = ref<TagItem[]>(initialTags.map(t => ({ ...t })))
  const inputVal = ref('')
  const suggestions = ref<string[]>([])
  const showSuggestions = ref(false)
  const loading = ref(false)

  let debounceTimer: ReturnType<typeof setTimeout> | null = null

  async function fetchSuggestions(query: string) {
    if (!query || query.length < 1) {
      suggestions.value = []
      showSuggestions.value = false
      return
    }
    try {
      loading.value = true
      const res = await worksApi.suggestTags(query)
      const data = res.data.data || []
      suggestions.value = data.map((s: any) => typeof s === 'string' ? s : s.tag || s.name || s)
      showSuggestions.value = suggestions.value.length > 0
    } catch {
      suggestions.value = []
      showSuggestions.value = false
    } finally {
      loading.value = false
    }
  }

  function onInput(input: string) {
    inputVal.value = input
    if (debounceTimer) clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => {
      fetchSuggestions(input)
    }, 300)
  }

  function onKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter' && inputVal.value.trim()) {
      e.preventDefault()
      addTag(inputVal.value.trim())
      inputVal.value = ''
      showSuggestions.value = false
    } else if (e.key === 'Backspace' && !inputVal.value && tags.value.length > 0) {
      tags.value.pop()
    } else if (e.key === 'Escape') {
      showSuggestions.value = false
    }
  }

  function addTag(label: string) {
    if (tags.value.some(t => t.tag === label)) return
    tags.value.push({ id: '', tag: label })
    suggestions.value = []
    showSuggestions.value = false
  }

  function addSuggestion(index: number) {
    addTag(suggestions.value[index])
  }

  function removeTag(index: number) {
    tags.value.splice(index, 1)
  }

  function reset() {
    tags.value = []
    inputVal.value = ''
    suggestions.value = []
    showSuggestions.value = false
  }

  return {
    tags,
    inputVal,
    suggestions,
    showSuggestions,
    loading,
    onInput,
    onKeydown,
    addTag,
    addSuggestion,
    removeTag,
    reset,
  }
}
