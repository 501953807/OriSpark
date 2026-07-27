import { Page, expect } from '@playwright/test'

export class BasePage {
  constructor(public readonly page: Page) {}

  async goto(path: string) {
    await this.page.goto(path)
    await this.page.waitForLoadState('networkidle')
  }

  async waitForNavBar() {
    // Wait for the sidebar to be visible
    await this.page.waitForSelector('.dynamic-sidebar', { state: 'visible', timeout: 10000 })
  }
}
