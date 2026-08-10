/** User model returned by auth API. */

export interface User {
  id: string
  username: string
  email: string
  role: string
  participant_roles: string[]
  participant_role_names: string[]
  avatar_url?: string
  phone?: string
  onboarded?: boolean
  creator_type?: string
  login_platform?: string // v6.0: 'web' | 'nuxt' | 'miniprogram'
  created_at?: string
  last_login_at?: string
  login_count?: number
}
