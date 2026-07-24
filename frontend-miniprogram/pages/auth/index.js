// pages/auth/index.js
const app = getApp()

Page({
  data: { loggingIn: false },
  async onLoad() {
    const token = wx.getStorageSync('token')
    if (token) {
      wx.switchTab({ url: '/pages/index/index' })
      return
    }
    await this.wxLogin()
  },
  async wxLogin() {
    this.setData({ loggingIn: true })
    try {
      const loginRes = await wx.login()
      const { data } = await app.request({
        url: '/auth/wechat/login',
        method: 'POST',
        data: { code: loginRes.code }
      })
      app.globalData.token = data.token
      wx.setStorageSync('token', data.token)
      wx.switchTab({ url: '/pages/index/index' })
    } catch (e) {
      console.error('Login failed:', e)
      wx.showToast({ title: '登录失败', icon: 'none' })
    } finally {
      this.setData({ loggingIn: false })
    }
  },
})
