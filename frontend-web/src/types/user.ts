/** User model returned by auth API. */

export interface User {
  id: string
  username: string
  email: string
  role: string
  avatar_url?: string
  phone?: string
  onboarded?: boolean
  created_at?: string
  last_login_at?: string
  login_count?: number
}
