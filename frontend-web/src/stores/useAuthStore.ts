/** Auth Pinia store — manages token lifecycle, user state, and logout. */

import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import client from '@/api/client'
import type { User } from '@/types/user'

interface AuthResponse {
  token: string
  user: User
}

interface LoginPayload {
  email: string
  password: string
}

interface RegisterPayload extends LoginPayload {
  username: string
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('oristudio-token'))
  const user = ref<User | null>(
    (() => {
      const raw = localStorage.getItem('oristudio-user')
      return raw ? JSON.parse(raw) : null
    })()
  )
  const loading = ref(false)
  const error = ref('')

  const isLoggedIn = computed(() => !!token.value)
  const displayName = computed(() => user.value?.username || user.value?.email || '创作者')

  // ── Login ──────────────────────────────────────────────────────

  async function login(payload: LoginPayload): Promise<boolean> {
    loading.value = true
    error.value = ''
    try {
      const resp = await client.post('/auth/login', payload)
      const data = resp.data.data as AuthResponse
      token.value = data.token
      user.value = data.user
      localStorage.setItem('oristudio-token', data.token)
      localStorage.setItem('oristudio-user', JSON.stringify(data.user))
      // Update client headers
      client.defaults.headers.common['Authorization'] = `Bearer ${data.token}`
      return true
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '登录失败'
      error.value = msg
      return false
    } finally {
      loading.value = false
    }
  }

  // ── Register ───────────────────────────────────────────────────

  async function register(payload: RegisterPayload): Promise<boolean> {
    loading.value = true
    error.value = ''
    try {
      await client.post('/auth/register', payload)
      // Auto-login after registration
      return await login({ email: payload.email, password: payload.password })
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '注册失败'
      error.value = msg
      return false
    } finally {
      loading.value = false
    }
  }

  // ── Logout ─────────────────────────────────────────────────────

  async function logout(): Promise<void> {
    try {
      if (token.value) {
        await client.post('/auth/logout')
      }
    } catch {
      // Best-effort — clear locally regardless
    } finally {
      token.value = null
      user.value = null
      localStorage.removeItem('oristudio-token')
      localStorage.removeItem('oristudio-user')
      delete client.defaults.headers.common['Authorization']
    }
  }

  // ── Fetch current user ─────────────────────────────────────────

  async function fetchUser(): Promise<User | null> {
    try {
      const resp = await client.get('/auth/me')
      const userData = resp.data.data as User
      user.value = userData
      localStorage.setItem('oristudio-user', JSON.stringify(userData))
      return userData
    } catch {
      user.value = null
      return null
    }
  }

  // ── Reset ──────────────────────────────────────────────────────

  function clearError() {
    error.value = ''
  }

  return {
    token, user, loading, error,
    isLoggedIn, displayName,
    login, register, logout, fetchUser, clearError,
  }
})
