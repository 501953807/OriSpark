/**
 * P3.3.4-P3.3.5: Lightweight i18n composable.
 * Translates UI strings for zh-CN and en-US without requiring vue-i18n dependency.
 */

import { ref, computed, watch } from 'vue'

export type Locale = 'zh-CN' | 'en-US'

const messages: Record<Locale, Record<string, string>> = {
  'zh-CN': {
    'app.title': 'OriStudio',
    'app.subtitle': '创作者全链路助手',
    'sidebar.overview': '概览',
    'sidebar.core': '核心模块',
    'sidebar.settings': '设置',
    'sidebar.dashboard': '工作台',
    'sidebar.works': '作品管理',
    'sidebar.projects': '项目分组',
    'sidebar.notary': '存证确权',
    'sidebar.monitor': '侵权监测',
    'sidebar.ipr': 'IP 登记',
    'sidebar.supply': '供应链',
    'sidebar.publish': '发布变现',
    'sidebar.preferences': '偏好设置',
    'sidebar.integrations': '第三方对接',
    'common.save': '保存',
    'common.cancel': '取消',
    'common.confirm': '确认',
    'common.delete': '删除',
    'common.edit': '编辑',
    'common.create': '创建',
    'common.upload': '上传',
    'common.export': '导出',
    'common.import': '导入作品',
    'common.search': '搜索',
    'common.refresh': '刷新',
    'common.loading': '处理中...',
    'common.success': '操作成功',
    'common.error': '操作失败',
    'common.back': '返回',
    'common.next': '下一步',
    'common.skip': '跳过',
    'common.submit': '提交',
    'common.language': '语言',
    'common.theme': '切换主题',
    'common.light': '浅色模式',
    'common.dark': '暗色模式',
    'common.close': '关闭',
    'common.more': '更多',
    'auth.login': '登录',
    'auth.register': '注册',
    'auth.email': '邮箱',
    'auth.password': '密码',
    'auth.username': '用户名',
    'auth.logout': '退出登录',
    'auth.skip': '跳过登录，直接进入（本地模式）',
    'settings.profile': '个人资料',
    'settings.appearance': '外观设置',
    'settings.linked': '关联账号',
    'settings.health': '系统健康',
    'settings.data': '数据管理',
    'settings.notifications': '通知渠道',
    'settings.plugins': '插件管理',
    'settings.password': '密码管理',
    'settings.mcp': 'MCP 服务',
    'settings.about': '关于',
  },
  'en-US': {
    'app.title': 'OriStudio',
    'app.subtitle': 'Creator All-in-One Toolkit',
    'sidebar.overview': 'Overview',
    'sidebar.core': 'Core Modules',
    'sidebar.settings': 'Settings',
    'sidebar.dashboard': 'Dashboard',
    'sidebar.works': 'Works',
    'sidebar.projects': 'Projects',
    'sidebar.notary': 'Notarization',
    'sidebar.monitor': 'Monitor',
    'sidebar.ipr': 'IP Registry',
    'sidebar.supply': 'Supply Chain',
    'sidebar.publish': 'Publish',
    'sidebar.preferences': 'Preferences',
    'sidebar.integrations': 'Integrations',
    'common.save': 'Save',
    'common.cancel': 'Cancel',
    'common.confirm': 'Confirm',
    'common.delete': 'Delete',
    'common.edit': 'Edit',
    'common.create': 'Create',
    'common.upload': 'Upload',
    'common.export': 'Export',
    'common.import': 'Import Works',
    'common.search': 'Search',
    'common.refresh': 'Refresh',
    'common.loading': 'Processing...',
    'common.success': 'Success',
    'common.error': 'Error',
    'common.back': 'Back',
    'common.next': 'Next',
    'common.skip': 'Skip',
    'common.submit': 'Submit',
    'common.language': 'Language',
    'common.theme': 'Toggle Theme',
    'common.light': 'Light Mode',
    'common.dark': 'Dark Mode',
    'common.close': 'Close',
    'common.more': 'More',
    'auth.login': 'Login',
    'auth.register': 'Register',
    'auth.email': 'Email',
    'auth.password': 'Password',
    'auth.username': 'Username',
    'auth.logout': 'Logout',
    'auth.skip': 'Skip login, enter directly (local mode)',
    'settings.profile': 'Profile',
    'settings.appearance': 'Appearance',
    'settings.linked': 'Linked Accounts',
    'settings.health': 'System Health',
    'settings.data': 'Data Management',
    'settings.notifications': 'Notifications',
    'settings.plugins': 'Plugin Manager',
    'settings.password': 'Password',
    'settings.mcp': 'MCP Service',
    'settings.about': 'About',
  },
}

const STORAGE_KEY = 'oristudio-locale'
const currentLocale = ref<Locale>((localStorage.getItem(STORAGE_KEY) as Locale) || 'zh-CN')

export function useI18n() {
  const locale = computed(() => currentLocale.value)

  function t(key: string): string {
    return messages[currentLocale.value]?.[key] || messages['zh-CN'][key] || key
  }

  function setLocale(loc: Locale) {
    currentLocale.value = loc
    localStorage.setItem(STORAGE_KEY, loc)
    document.documentElement.lang = loc
  }

  return { locale, t, setLocale }
}

// Initialize html lang attribute
if (typeof document !== 'undefined') {
  document.documentElement.lang = currentLocale.value
}
