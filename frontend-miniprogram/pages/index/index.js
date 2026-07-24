// pages/index/index.js
const { getFeaturedWorks } = require('../../api/works')
const { getPublicContracts } = require('../../api/contracts')
const { getPublicNotifications } = require('../../api/notifications')

Page({
  data: {
    featuredWorks: [],
    recentContracts: [],
    notifications: [],
    loading: false,
  },

  onLoad() {
    this.loadDashboard()
  },

  onShow() {
    this.loadNotifications()
  },

  async loadDashboard() {
    this.setData({ loading: true })
    try {
      const [worksRes, contractsRes] = await Promise.all([
        getFeaturedWorks({ limit: 6 }),
        getPublicContracts({ limit: 5 }),
      ])
      // Backend returns array directly (not wrapped in {data: []})
      this.setData({
        featuredWorks: Array.isArray(worksRes) ? worksRes : (worksRes?.data || []),
        recentContracts: Array.isArray(contractsRes) ? contractsRes : (contractsRes?.data || []),
      })
    } catch (e) {
      console.error('loadDashboard failed:', e)
    } finally {
      this.setData({ loading: false })
    }
  },

  async loadNotifications() {
    try {
      const res = await getPublicNotifications({ limit: 3 })
      // Backend returns array directly
      this.setData({ notifications: Array.isArray(res) ? res : (res?.data || []) })
    } catch (e) {
      console.error('loadNotifications failed:', e)
    }
  },

  navigateToWorks() {
    wx.navigateTo({ url: '/pages/works/index' })
  },

  navigateToContracts() {
    wx.navigateTo({ url: '/pages/contracts/index' })
  },

  navigateToNotifications() {
    wx.navigateTo({ url: '/pages/notifications/index' })
  },
})
