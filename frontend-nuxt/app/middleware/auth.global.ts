/** Global auth middleware for OriSpark */
import { useAuthStore } from '~/stores/auth'

export default defineNuxtRouteMiddleware(async (to) => {
  const auth = useAuthStore()
  
  // Public pages that don't require auth
  const publicPages = ['/', '/gallery', '/auth/login', '/auth/register']
  if (publicPages.includes(to.path)) return

  // Check if user is logged in
  if (!auth.isLoggedIn) {
    // Try to restore from localStorage
    const savedToken = localStorage.getItem('orispark-token')
    const savedUser = localStorage.getItem('orispark-user')
    if (savedToken && savedUser) {
      auth.token = savedToken
      auth.user = JSON.parse(savedUser)
    }
  }

  // Redirect to login if not authenticated
  if (!auth.isLoggedIn) {
    return navigateTo('/auth/login')
  }
})
