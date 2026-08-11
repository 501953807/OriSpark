/**
 * Layout Context Composable
 *
 * 统一封装 Layout 组件所需的全局状态，
 * 消除各 Layout 组件对 useAppStore/useAuthStore 的直接依赖。
 */
import { useAppStore } from '@/stores/useAppStore'
import { useAuthStore } from '@/stores/useAuthStore'

export function useLayoutContext() {
  const appStore = useAppStore()
  const authStore = useAuthStore()

  return {
    // 侧边栏
    sidebarCollapsed: appStore.sidebarCollapsed,
    toggleSidebar: appStore.toggleSidebar,
    // 用户
    user: authStore.user,
    displayName: authStore.displayName,
    isLoggedIn: authStore.isLoggedIn,
    logout: authStore.logout,
    // 主题
    currentTheme: appStore.currentTheme,
    setTheme: appStore.setTheme,
    themePresets: appStore.themePresets,
    // 统计
    workCount: appStore.workCount,
    notaryCount: appStore.notaryCount,
    alertCount: appStore.alertCount,
  }
}
