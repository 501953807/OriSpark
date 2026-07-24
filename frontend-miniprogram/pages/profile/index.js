// pages/profile/index.js
const app = getApp()

Page({
  data: { nickname: '点击登录', avatar: '' },
  onLoad() { this.loadProfile() },
  loadProfile() {
    const token = wx.getStorageSync('token')
    if (token) {
      // TODO: fetch user info from API
      this.setData({ nickname: '用户' })
    }
  },
  onLogout() {
    wx.removeStorageSync('token')
    app.globalData.token = ''
    wx.reLaunch({ url: '/pages/index/index' })
  },
})
