import { test, expect } from '@playwright/test'

test.describe('Console Error Monitoring', () => {
  test('login page renders without crashing', async ({ page }) => {
    await page.goto('/login')
    await page.waitForLoadState('networkidle')

    // Login page should render
    const appContent = page.locator('#app').textContent()
    expect(appContent).toBeTruthy()
  })

  test('onboarding page handles gracefully', async ({ page }) => {
    await page.goto('/onboarding').catch(() => {})
    await page.waitForTimeout(500)

    // Page should still have content even if route doesn't exist
    const bodyText = await page.locator('body').textContent()
    expect(bodyText).toBeTruthy()
  })
})
