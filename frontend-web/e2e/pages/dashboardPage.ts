import { Page, expect } from '@playwright/test'
import { BasePage } from './basePage'

export class DashboardPage extends BasePage {
  async goto() {
    await this.page.goto('/app')
  }

  async waitForDashboard() {
    // Wait for stat cards to appear
    await this.page.waitForSelector('.stat-card', { state: 'visible', timeout: 10000 })
  }

  async getStatCardCount() {
    return this.page.locator('.stat-card').count()
  }

  async clickSidebarLink(text: string) {
    const link = this.page.locator(`.sb-link:has-text("${text}")`)
    await link.click()
    await this.page.waitForLoadState('networkidle')
  }

  async isSidebarVisible() {
    return this.page.isVisible('.dynamic-sidebar')
  }

  async collapseSidebar() {
    await this.page.locator('.sb-collapse-btn').click()
  }

  async expandSidebar() {
    // If sidebar is collapsed, hover over it to expand
    if (await this.page.locator('.dynamic-sidebar.collapsed').isVisible()) {
      await this.page.locator('.dynamic-sidebar').hover()
    }
  }
}
