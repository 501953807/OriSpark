// app.js
const { request } = require('./utils/request')

App({
  globalData: {
    userInfo: null,
    token: null,
    userId: null,
    apiBase: 'https://api.orispark.local/api',
  },

  onLaunch() {
    const token = wx.getStorageSync('token')
    if (token) {
      this.globalData.token = token
    }
  },

  // Expose request for pages that need it
  request,

  // 微信一键登录
  async wxLogin() {
    try {
      const loginRes = await wx.login()
      if (loginRes.code) {
        const res = await request({
          url: '/auth/wechat/login',
          method: 'POST',
          data: { code: loginRes.code },
        })
        this.globalData.token = res.token
        this.globalData.userId = res.user?.id || res.user_id || res.id || null
        this.globalData.userInfo = res.user
        wx.setStorageSync('token', res.token)
        return res
      }
      throw new Error('Login failed: no code')
    } catch (e) {
      console.error('wxLogin failed:', e)
      throw e
    }
  },

  logout() {
    this.globalData.token = null
    this.globalData.userInfo = null
    wx.removeStorageSync('token')
    wx.removeStorageSync('userInfo')
  },
})
