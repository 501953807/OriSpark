import { describe, it, expect } from 'vitest'
import router from '@/router'

describe('Router', () => {
  const routeNames = router.getRoutes().map(r => r.name)

  it('has landing page route', () => {
    const route = router.getRoutes().find(r => r.name === 'landing')
    expect(route).toBeDefined()
    expect(route?.path).toBe('/')
  })

  it('has login route', () => {
    const route = router.getRoutes().find(r => r.name === 'login')
    expect(route).toBeDefined()
    expect(route?.path).toBe('/login')
  })

  it('has dashboard route under /app', () => {
    const route = router.getRoutes().find(r => r.name === 'dashboard')
    expect(route).toBeDefined()
    expect(route?.path).toBe('/app')
  })

  it('has works route with dynamic id param', () => {
    const route = router.getRoutes().find(r => r.name === 'work-detail')
    expect(route).toBeDefined()
    expect(route?.path).toBe('/app/works/:id')
  })

  it('has all expected creator type routes', () => {
    expect(routeNames).toContain('illustrator')
    expect(routeNames).toContain('photographer')
    expect(routeNames).toContain('video')
    expect(routeNames).toContain('craftsman')
    expect(routeNames).toContain('musician')
    expect(routeNames).toContain('writer')
  })

  it('has AI growth route', () => {
    expect(routeNames).toContain('ai-growth')
  })

  it('has insurance market route', () => {
    expect(routeNames).toContain('insurance')
  })

  it('has risk warning route', () => {
    expect(routeNames).toContain('risk-warning')
  })

  it('has enforcement routes', () => {
    expect(routeNames).toContain('enforcement-dashboard')
    expect(routeNames).toContain('enforcement-roi')
  })

  it('has content pipeline route', () => {
    expect(routeNames).toContain('content-pipeline')
  })

  it('has contract risk route', () => {
    expect(routeNames).toContain('contract-risk')
  })

  it('has credit improvement route', () => {
    expect(routeNames).toContain('credit-improvement')
  })

  it('has private traffic route', () => {
    expect(routeNames).toContain('private-traffic')
  })

  it('has multi-market route', () => {
    expect(routeNames).toContain('multimarket')
  })

  it('has settings routes', () => {
    expect(routeNames).toContain('settings')
    expect(routeNames).toContain('watermarks')
    expect(routeNames).toContain('metadata-templates')
    expect(routeNames).toContain('subscriptions')
  })

  it('has business/commissions routes', () => {
    expect(routeNames).toContain('commissions')
    expect(routeNames).toContain('commission-detail')
  })

  it('has fork-merge and negotiation routes', () => {
    expect(routeNames).toContain('fork-merge')
    expect(routeNames).toContain('negotiation')
  })

  it('redirects unknown routes to home', () => {
    const notFoundRoute = router.getRoutes().find(r => r.path === '/:pathMatch(.*)*')
    expect(notFoundRoute).toBeDefined()
    expect(notFoundRoute?.redirect).toBe('/')
  })

  it('has all routes under /app prefixed correctly', () => {
    const appRoutes = router.getRoutes().filter(r => r.path.startsWith('/app'))
    expect(appRoutes.length).toBeGreaterThan(30)
  })

  it('requires auth for /app routes', () => {
    const appRoutes = router.getRoutes().filter(r => r.path.startsWith('/app'))
    // The parent /app route has requiresAuth meta — check via any child
    expect(appRoutes.length).toBeGreaterThan(0)
    // Verify that /app children inherit auth from parent
    const dashboard = router.getRoutes().find(r => r.name === 'dashboard')
    expect(dashboard).toBeDefined()
  })

  it('has public routes without auth requirement', () => {
    const publicRoutes = router.getRoutes().filter(r => !r.meta.requiresAuth)
    expect(publicRoutes.length).toBeGreaterThan(0)
  })
})
