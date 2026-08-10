// pages/profile/index.js
const { getProfile } = require('../../api/profile')

Page({
  data: { nickname: '点击登录', avatar: '' },
  onLoad() { this.loadProfile() },
  async loadProfile() {
    const token = wx.getStorageSync('token')
    if (!token) return
    try {
      const res = await getProfile()
      const user = res.data
      this.setData({
        nickname: user.username || '用户',
        avatar: user.avatar_url || '',
      })
    } catch {
      this.setData({ nickname: '登录已过期' })
    }
  },
  onLogout() {
    wx.removeStorageSync('token')
    const app = getApp()
    app.globalData.token = ''
    wx.reLaunch({ url: '/pages/index/index' })
  },
})
