import { test, expect } from '@playwright/test';

test('landing page navigation', async ({ page }) => {
  await page.goto('http://localhost:5174/');
  await page.waitForLoadState('networkidle');

  console.log('URL:', page.url());
  console.log('Title:', await page.title());

  // Check if router links exist
  const loginLink = page.locator('a[href="/login"]');
  const appLink = page.locator('a[href="/app"]');

  console.log('Login link count:', await loginLink.count());
  console.log('App link count:', await appLink.count());

  // Try clicking login
  if (await loginLink.count() > 0) {
    await loginLink.first().click();
    await page.waitForTimeout(500);
    console.log('After login click URL:', page.url());
  } else {
    // Try router-link elements
    const routerLinks = page.locator('router-link');
    console.log('Router-link count:', await routerLinks.count());

    // Check all links on page
    const allLinks = await page.locator('a').all();
    console.log('All links:', allLinks.map(async l => await l.getAttribute('href')));
  }
});
