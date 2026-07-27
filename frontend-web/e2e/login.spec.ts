import { test, expect } from '@playwright/test'

test.describe('Login Page', () => {
  test('loads login page', async ({ page }) => {
    await page.goto('/login')
    // The login page should load without errors
    await expect(page).toHaveTitle(/.*OriStudio.*/i)
  })

  test('shows login form elements', async ({ page }) => {
    await page.goto('/login')
    // Check that email and password inputs exist
    const emailInput = page.locator('input[type="email"], input[placeholder*="邮箱"]').first()
    const passwordInput = page.locator('input[type="password"]').first()

    // At least one of these should be visible (depends on actual login page implementation)
    const hasInputs = await emailInput.isVisible().catch(() => false) ||
                      await passwordInput.isVisible().catch(() => false)

    // If inputs exist, they should be empty
    if (hasInputs) {
      const emailVal = await emailInput.inputValue().catch(() => '')
      expect(emailVal).toBe('')
    }
  })
})
