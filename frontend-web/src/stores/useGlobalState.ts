import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * 全局状态 Store — 聚合跨模块全局状态
 *
 * 职责:
 * - 统一管理全局计数 (workCount, notaryCount, alertCount)
 * - 统一管理用户偏好 (creatorType, participantRole, isOnboarded)
 * - 提供统一的 localStorage 读写入口
 */
export const useGlobalState = defineStore('global', () => {
  // ── 全局计数 ─────────────────────────────────────────────────────
  const workCount = ref(0)
  const notaryCount = ref(0)
  const alertCount = ref(0)

  function updateStats(stats: { total_works: number; total_notarized: number; infringement_alerts: number }) {
    workCount.value = stats.total_works
    notaryCount.value = stats.total_notarized
    alertCount.value = stats.infringement_alerts
  }

  // ── 用户偏好 ─────────────────────────────────────────────────────
  const creatorType = ref<string | null>(null)
  const participantRole = ref<string | null>(null)
  const isOnboarded = ref(false)

  function setCreatorType(type: string) {
    creatorType.value = type
  }

  function setParticipantRole(role: string) {
    participantRole.value = role
  }

  function markOnboarded() {
    isOnboarded.value = true
  }

  function clearOnboarding() {
    creatorType.value = null
    participantRole.value = null
    isOnboarded.value = false
  }

  return {
    // 计数
    workCount,
    notaryCount,
    alertCount,
    updateStats,
    // 用户偏好
    creatorType,
    participantRole,
    isOnboarded,
    setCreatorType,
    setParticipantRole,
    markOnboarded,
    clearOnboarding,
  }
}, {
  persist: {
    key: 'oristudio-global',
    storage: localStorage,
    pick: ['creatorType', 'participantRole', 'isOnboarded'],
  },
})
