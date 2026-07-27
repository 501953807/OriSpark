import { Page, expect } from '@playwright/test'
import { BasePage } from './basePage'

export class LoginPage extends BasePage {
  private readonly emailInput = this.page.locator('input[type="email"], input[placeholder*="邮箱"]').first()
  private readonly passwordInput = this.page.locator('input[type="password"]').first()
  private readonly loginBtn = this.page.locator('button[type="submit"], button:has-text("登录")').first()
  private readonly registerLink = this.page.locator('a:has-text("注册"), button:has-text("注册")').first()

  async goto() {
    await this.page.goto('/login')
  }

  async fillEmail(email: string) {
    await this.emailInput.fill(email)
  }

  async fillPassword(password: string) {
    await this.passwordInput.fill(password)
  }

  async clickLogin() {
    await this.loginBtn.click()
  }

  async clickRegister() {
    await this.registerLink.click()
  }

  async login(email: string, password: string) {
    await this.fillEmail(email)
    await this.fillPassword(password)
    await this.clickLogin()
  }
}
