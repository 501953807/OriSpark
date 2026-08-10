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
      localStorage.setItem('orispark-token', data.token)
      localStorage.setItem('orispark-user', JSON.stringify(data.user))
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
    localStorage.removeItem('orispark-token')
    localStorage.removeItem('orispark-user')
  }

  return { token, user, loading, error, isLoggedIn, displayName, participantRoles, isOperator, login, logout }
})
