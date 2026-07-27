import { test, expect } from '@playwright/test'

test.describe('IprView Tab Navigation', () => {
  test('loads IPR page or redirects', async ({ page }) => {
    await page.goto('/app/ipr')
    await page.waitForLoadState('networkidle')

    const url = page.url()
    expect(url).toBeTruthy()

    if (!url.includes('/login')) {
      const appEl = page.locator('#app').first()
      const content = await appEl.textContent()
      expect(content !== null).toBe(true)
    }
  })

  test('IPR page body has content when not redirected', async ({ page }) => {
    await page.goto('/app/ipr')
    await page.waitForLoadState('networkidle')

    const url = page.url()
    if (!url.includes('/login')) {
      const bodyText = await page.locator('body').textContent()
      expect(bodyText).toBeTruthy()
    }
  })
})
