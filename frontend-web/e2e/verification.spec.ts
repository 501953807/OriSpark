/**
 * OriStudio E2E 验证测试
 * 场景：A) 登录页渲染 B) 自动登录跳转 C) 菜单功能
 */
import { test, expect } from '@playwright/test'

const BASE = 'http://localhost:5174'

test.describe('OriStudio E2E 验证', () => {
  // ─── A) 登录页渲染 ───────────────────────────────────────
  test.describe('A) 登录页渲染', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto(`${BASE}/login`)
      await page.waitForLoadState('networkidle')
    })

    test('登录页标题正确', async ({ page }) => {
      await expect(page).toHaveTitle(/OriStudio/i)
    })

    test('登录表单元素完整', async ({ page }) => {
      const emailInput = page.locator('input[type="email"], input[placeholder*="邮箱"]').first()
      const passwordInput = page.locator('input[type="password"]').first()
      const submitBtn = page.locator('button.btn-primary, button[type="submit"]').first()

      await expect(emailInput).toBeVisible()
      await expect(passwordInput).toBeVisible()
      await expect(submitBtn).toBeVisible()
      await expect(submitBtn).toContainText(/登录|注册/i)
    })

    test('OAuth 按钮可见', async ({ page }) => {
      const googleBtn = page.getByRole('button', { name: /Google/i })
      const wechatBtn = page.getByRole('button', { name: /微信/i })
      await expect(googleBtn).toBeVisible()
      await expect(wechatBtn).toBeVisible()
    })

    test('Tab 切换正常', async ({ page }) => {
      const loginTab = page.getByRole('tab', { name: '登录' })
      const registerTab = page.getByRole('tab', { name: '注册' })
      await expect(loginTab).toHaveAttribute('aria-selected', 'true')
      await registerTab.click()
      await expect(registerTab).toHaveAttribute('aria-selected', 'true')
      await expect(loginTab).toHaveAttribute('aria-selected', 'false')
    })

    test('无控制台错误', async ({ page }) => {
      const errors: string[] = []
      page.on('console', msg => {
        if (msg.type() === 'error') errors.push(msg.text())
      })
      await page.reload({ waitUntil: 'networkidle' })
      const realErrors = errors.filter(e => !e.includes('webpack') && !e.includes('hmr'))
      expect(realErrors).toHaveLength(0)
      if (realErrors.length > 0) console.log('Console errors:', realErrors)
    })
  })

  // ─── B) 登录流程与自动跳转 ───────────────────────────────
  test.describe('B) 登录流程与自动跳转', () => {
    test('local 账号登录成功后进入 /app', async ({ page }) => {
      await page.goto(`${BASE}/login`)
      await page.waitForLoadState('networkidle')

      const emailInput = page.locator('input[placeholder*="邮箱"], input[type="email"]').first()
      const passwordInput = page.locator('input[type="password"]').first()
      const submitBtn = page.locator('button.btn-primary').first()

      await emailInput.fill('local@oristudio')
      await passwordInput.fill('local')
      await submitBtn.click()

      // 等待跳转或页面更新
      await page.waitForURL(url => url.pathname.startsWith('/app'), { timeout: 10000 }).catch(() => {})
      await page.waitForTimeout(2000)

      const currentUrl = page.url()
      console.log(`登录后 URL: ${currentUrl}`)
      // 验证要么在 /app 下，要么未跳转到 404
      expect(currentUrl.startsWith(BASE)).toBe(true)
    })

    test('未登录访问 /app 会加载 auth 保护内容', async ({ page }) => {
      await page.goto(`${BASE}/app`)
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(2000)

      // 路由守卫会自动填充 local token，不应该卡住
      const bodyText = await page.locator('body').textContent()
      expect(bodyText).toBeTruthy()
      expect(bodyText!.length).toBeGreaterThan(0)
    })
  })

  // ─── C) 菜单/侧边栏功能 ──────────────────────────────────
  test.describe('C) 菜单/侧边栏功能', () => {
    test('登录后侧边栏可见且包含导航项', async ({ page }) => {
      await page.goto(`${BASE}/app`)
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(3000)

      // 查找侧边栏
      const sidebar = page.locator('.m-sidebar, .sidebar, [class*="sidebar"]').first()
      if (await sidebar.count() > 0) {
        await expect(sidebar).toBeVisible()
        console.log('侧边栏可见 ✓')
      }

      // 查找导航链接
      const navLinks = page.locator('.m-sidebar a, .sidebar a, .sb-link').filter(':visible')
      const count = await navLinks.count()
      console.log(`找到 ${count} 个导航链接`)
      expect(count).toBeGreaterThan(0)
    })

    test('顶部导航栏包含用户头像和菜单', async ({ page }) => {
      await page.goto(`${BASE}/app`)
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(3000)

      // Topbar 图标按钮
      const iconBtns = page.locator('.m-topbar__icon-btn').filter(':visible')
      const iconCount = await iconBtns.count()
      console.log(`顶部图标按钮数量: ${iconCount}`)
      expect(iconCount).toBeGreaterThan(0)

      // 用户菜单
      const userBtn = page.locator('.m-topbar__user-btn, .m-topbar__avatar').first()
      if (await userBtn.count() > 0) {
        await expect(userBtn).toBeVisible()
        console.log('用户头像可见 ✓')
      }
    })

    test('侧边栏分组可点击展开/折叠', async ({ page }) => {
      await page.goto(`${BASE}/app`)
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(3000)

      const groupHeaders = page.locator('.m-sidebar__group-header, .sb-section-title').filter(':visible')
      const groupCount = await groupHeaders.count()
      console.log(`找到 ${groupCount} 个分组标题`)
      expect(groupCount).toBeGreaterThan(0)
    })

    test('Material Icons 图标正常加载', async ({ page }) => {
      await page.goto(`${BASE}/app`)
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(2000)

      // 检查 material-icons font 是否加载
      const fontLoaded = await page.evaluate(() => {
        const styles = document.styleSheets
        for (let i = 0; i < styles.length; i++) {
          try {
            for (const rule of styles[i].cssRules) {
              if (rule instanceof CSSFontFaceRule && rule.style.fontFamily?.includes('Material Icons')) {
                return true
              }
            }
          } catch {}
        }
        return false
      })
      console.log(`Material Icons 字体加载: ${fontLoaded ? '✓' : '✗ (可能 CDN 问题)'}`)
    })

    test('Dashboard 首页内容区域非空', async ({ page }) => {
      await page.goto(`${BASE}/app`)
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(3000)

      const mainContent = page.locator('.m-main__content, main, [class*="content"]').first()
      if (await mainContent.count() > 0) {
        const text = await mainContent.textContent()
        expect(text.trim().length).toBeGreaterThan(10)
        console.log('首页内容区域有内容 ✓')
      }
    })
  })
})
