/** Auth Pinia store for frontend-nuxt (OriSpark trading platform) */
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

interface User {
  id: string
  username: string
  email: string
  role: string
  participant_roles: string[]
  participant_role_names: string[]
  login_platform?: string
  avatar_url?: string
}

interface AuthResponse {
  token: string
  user: User
}

export const useAuthStore = defineStore('nuxt-auth', () => {
  const token = ref<string | null>(null)
  const user = ref<User | null>(null)
  const loading = ref(false)
  const error = ref('')

  const isLoggedIn = computed(() => !!token.value)
  const displayName = computed(() => user.value?.username || user.value?.email || '用户')
  const participantRoles = computed(() => user.value?.participant_roles || [])
  const isOperator = computed(() => participantRoles.value.some(r => r !== 'creator'))

  // SSR-safe cookie helpers
  function getCookie(name: string): string | null {
    if (import.meta.server) {
      const cookies = useCookie(name)
      return cookies.value || null
    }
    const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'))
    return match ? decodeURIComponent(match[2]) : null
  }

  function setCookie(name: string, value: string, days = 7): void {
    if (import.meta.server) {
      const cookies = useCookie(name, { maxAge: 60 * 60 * 24 * days })
      cookies.value = value
      return
    }
    document.cookie = `${name}=${encodeURIComponent(value)}; path=/; max-age=${60 * 60 * 24 * days}`
  }

  function deleteCookie(name: string): void {
    if (import.meta.server) {
      const cookies = useCookie(name)
      cookies.value = null
      return
    }
    document.cookie = `${name}=; path=/; max-age=0`
  }

  async function login(email: string, password: string): Promise<boolean> {
    loading.value = true
    error.value = ''
    try {
      const apiBase = useRuntimeConfig().public.apiBase
      const resp = await $fetch(`${apiBase}/auth/login`, {
        method: 'POST',
        body: { email, password },
      })
      const data = resp.data as AuthResponse
      token.value = data.token
      user.value = data.user
      setCookie('orispark-token', data.token)
      setCookie('orispark-user', JSON.stringify(data.user))
      return true
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : '登录失败'
      return false
    } finally {
      loading.value = false
    }
  }

  async function logout(): Promise<void> {
    token.value = null
    user.value = null
    deleteCookie('orispark-token')
    deleteCookie('orispark-user')
  }

  async function forgotPassword(email: string): Promise<boolean> {
    loading.value = true
    error.value = ''
    try {
      const apiBase = useRuntimeConfig().public.apiBase
      await $fetch(`${apiBase}/system/password/reset/request`, {
        method: 'POST',
        body: { email },
      })
      return true
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : '发送失败'
      return false
    } finally {
      loading.value = false
    }
  }

  async function resetPassword(token: string, password: string): Promise<boolean> {
    loading.value = true
    error.value = ''
    try {
      const apiBase = useRuntimeConfig().public.apiBase
      await $fetch(`${apiBase}/system/password/reset/confirm`, {
        method: 'POST',
        body: { token, new_password: password },
      })
      return true
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : '重置失败'
      return false
    } finally {
      loading.value = false
    }
  }

  return { token, user, loading, error, isLoggedIn, displayName, participantRoles, isOperator, login, logout, forgotPassword, resetPassword }
})
