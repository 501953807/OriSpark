import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { systemApi } from '@/api/system'

export interface DictItem {
  id: string
  group_key: string
  item_key: string
  item_value: string
  item_value_en?: string
  extra?: Record<string, any>
  is_active: boolean
  sort_order: number
}

/** 字典数据中心 Store — 全局缓存，支持懒加载 */
export const useDictStore = defineStore('dict', () => {
  const dicts = ref<Record<string, DictItem[]>>({})
  const loaded = ref(false)
  const loading = ref(false)

  /** 应用启动时预加载常用分组 */
  async function loadCommon() {
    if (loaded.value) return
    loading.value = true
    try {
      const commonKeys = [
        'work_statuses', 'file_types', 'ip_types', 'ip_statuses',
        'notary_statuses', 'match_statuses', 'order_statuses',
        'material_categories', 'pod_platforms', 'ai_desc_styles',
        'countries', 'currencies', 'notification_types',
      ]
      const res = await systemApi.dictItemsBulk(commonKeys)
      dicts.value = res.data.data || {}
      loaded.value = true
    } catch (err) {
      console.error('[DictStore] Failed to load common dicts:', err)
    } finally {
      loading.value = false
    }
  }

  /** 加载所有字典分组 */
  async function loadAll() {
    loading.value = true
    try {
      const res = await systemApi.dictItemsBulk()
      dicts.value = res.data.data || {}
      loaded.value = true
    } catch (err) {
      console.error('[DictStore] Failed to load all dicts:', err)
    } finally {
      loading.value = false
    }
  }

  /** 懒加载单个分组 */
  async function loadGroup(groupKey: string) {
    if (dicts.value[groupKey]) return
    try {
      const res = await systemApi.dictGroupItems(groupKey)
      dicts.value[groupKey] = res.data.data?.items || []
    } catch (err) {
      console.error(`[DictStore] Failed to load group '${groupKey}':`, err)
    }
  }

  /** 获取字典值(显示名) */
  function getLabel(groupKey: string, itemKey: string): string {
    const item = dicts.value[groupKey]?.find(i => i.item_key === itemKey)
    return item?.item_value || itemKey
  }

  /** 获取字典值(英文) */
  function getLabelEn(groupKey: string, itemKey: string): string {
    const item = dicts.value[groupKey]?.find(i => i.item_key === itemKey)
    return item?.item_value_en || itemKey
  }

  /** 获取字典条目的 extra 信息 */
  function getExtra(groupKey: string, itemKey: string): Record<string, any> | undefined {
    const item = dicts.value[groupKey]?.find(i => i.item_key === itemKey)
    return item?.extra
  }

  /** 获取分组所有已启用条目 */
  function getOptions(groupKey: string): DictItem[] {
    return dicts.value[groupKey]?.filter(i => i.is_active) || []
  }

  /** 获取分组的 key-value 映射 */
  function getMap(groupKey: string): Record<string, string> {
    const map: Record<string, string> = {}
    for (const item of getOptions(groupKey)) {
      map[item.item_key] = item.item_value
    }
    return map
  }

  /** 生成下拉选项 [{label, value}] */
  function toSelectOptions(groupKey: string): { label: string; value: string }[] {
    return getOptions(groupKey).map(item => ({
      label: item.item_value,
      value: item.item_key,
    }))
  }

  /** 检查分组是否已加载 */
  const hasGroup = (groupKey: string) => computed(() => !!dicts.value[groupKey])

  return {
    dicts,
    loaded,
    loading,
    loadCommon,
    loadAll,
    loadGroup,
    getLabel,
    getLabelEn,
    getExtra,
    getOptions,
    getMap,
    toSelectOptions,
    hasGroup,
  }
})
