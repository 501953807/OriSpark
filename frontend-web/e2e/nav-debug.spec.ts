import { test, expect } from '@playwright/test';

test('navigation debug', async ({ page }) => {
  await page.goto('http://localhost:5174/');
  await page.waitForLoadState('networkidle');
  
  // Get page content
  const bodyText = await page.locator('body').innerText();
  console.log('LANDING PAGE TEXT LENGTH:', bodyText.length);
  console.log('LANDING PREVIEW:', bodyText.substring(0, 200));
  
  // Click login
  await page.locator('a[href="/login"]').first().click();
  await page.waitForTimeout(2000);
  
  // Get login page content
  const loginText = await page.locator('body').innerText();
  console.log('LOGIN PAGE TEXT LENGTH:', loginText.length);
  console.log('LOGIN PREVIEW:', loginText.substring(0, 500));
  
  // Check for login form elements
  const passwordInput = await page.locator('input[type="password"]').count();
  const loginBtn = await page.locator('button:has-text("登录")').count();
  console.log('Has password input:', passwordInput > 0);
  console.log('Has login button:', loginBtn > 0);
});
