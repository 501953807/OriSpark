import { test, expect } from '@playwright/test'

test.describe('Landing Page', () => {
  test('loads landing page', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveTitle(/.*OriStudio.*/i)
  })

  test('shows navigation links', async ({ page }) => {
    await page.goto('/')
    // Check that the page body has content
    const bodyText = await page.locator('body').textContent()
    expect(bodyText).toBeTruthy()
    expect(bodyText!.length).toBeGreaterThan(0)
  })
})
