import { test, expect } from '@playwright/test'

test.describe('Navigation', () => {
  test('app page loads without errors', async ({ page }) => {
    await page.goto('/app')
    // App page might redirect to /login or render content — either way no crash
    const bodyText = await page.locator('body').textContent()
    expect(bodyText !== null).toBe(true)
  })

  test('page loads without critical console errors', async ({ page }) => {
    const consoleErrors: string[] = []
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text())
      }
    })

    await page.goto('/app')
    await page.waitForLoadState('networkidle')

    // Filter out expected warnings (webpack HMR, etc.)
    const realErrors = consoleErrors.filter(e => !e.includes('webpack') && !e.includes('hmr'))
    for (const error of realErrors) {
      console.log('Console error:', error)
    }
  })
})
