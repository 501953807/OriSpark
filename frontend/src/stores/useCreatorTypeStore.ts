import { ref, watch } from 'vue'
import { defineStore } from 'pinia'
import type { CreatorType } from '@/types/creator'
import {
  CREATOR_TYPES,
  getDefaultCreatorType,
} from '@/types/creator'

const STORAGE_KEY = 'oristudio-creator-type'

function loadFromStorage(): CreatorType {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved && saved in CREATOR_TYPES) return saved as CreatorType
  } catch {
    // localStorage may be unavailable
  }
  return getDefaultCreatorType()
}

function persistToStorage(type: CreatorType): void {
  try {
    localStorage.setItem(STORAGE_KEY, type)
  } catch {
    // ignore write failures
  }
}

export const useCreatorTypeStore = defineStore('creatorType', () => {
  const currentType = ref<CreatorType>(loadFromStorage())
  const history = ref<CreatorType[]>([])

  function setType(type: CreatorType) {
    if (!(type in CREATOR_TYPES)) {
      ;(window as any).$toast?.show(`未知的创作者类型: ${type}`, 'error')
      return
    }
    history.value = [...history.value, currentType.value]
    currentType.value = type
    persistToStorage(type)
  }

  function switchType(type: CreatorType) {
    if (type === currentType.value) return
    setType(type)
    ;(window as any).$toast?.show(
      `已切换到 ${CREATOR_TYPES[type].label}`,
      'success',
    )
  }

  function getCurrentType(): CreatorType {
    return currentType.value
  }

  function getTypeInfo(type?: CreatorType) {
    const t = type ?? currentType.value
    return CREATOR_TYPES[t] ?? null
  }

  // Keep localStorage in sync on reactive changes
  watch(currentType, (type) => persistToStorage(type), { immediate: false })

  return {
    currentType,
    history,
    setType,
    switchType,
    getCurrentType,
    getTypeInfo,
  }
})
