/** Global auth middleware for OriSpark — SSR-safe cookie-based auth */
import { useAuthStore } from '~/stores/auth'

export default defineNuxtRouteMiddleware(async (to) => {
  const auth = useAuthStore()

  // Skip auth for API routes and public pages
  if (to.path.startsWith('/api/')) return
  const publicPages = ['/', '/gallery', '/auth/login', '/auth/register']
  if (publicPages.includes(to.path)) return

  // Restore from cookie (works on both server and client)
  if (!auth.isLoggedIn) {
    const savedToken = useCookie('orispark-token').value
    const savedUserStr = useCookie('orispark-user').value
    if (savedToken) {
      auth.token = savedToken
    }
    if (savedUserStr) {
      try {
        auth.user = JSON.parse(savedUserStr)
      } catch {
        /* ignore */
      }
    }
  }

  // Redirect to login if not authenticated
  if (!auth.isLoggedIn) {
    return navigateTo('/auth/login')
  }
})
