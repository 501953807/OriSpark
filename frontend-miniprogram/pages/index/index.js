// pages/index/index.js
const { getMyWorks } = require('../../api/works')
const { getMyContracts } = require('../../api/contracts')
const { getMyNotifications } = require('../../api/notifications')
const { getMotionManager } = require('../../utils/motion')

Page({
  data: {
    featuredWorks: [],
    recentContracts: [],
    notifications: [],
    loading: false,
    statCounts: { works: 0, contracts: 0, creators: 0 },
  },

  onLoad() {
    const motionMgr = getMotionManager()
    motionMgr.registerPage('pages/index/index', this)
    this.loadDashboard()
  },

  onUnload() {
    getMotionManager().unregisterPage('pages/index/index')
  },

  onShow() {
    this.loadNotifications()
  },

  async loadDashboard() {
    this.setData({ loading: true })
    try {
      const token = wx.getStorageSync('token')
      if (token) {
        const [worksRes, contractsRes] = await Promise.all([
          getMyWorks({ limit: 6 }),
          getMyContracts({ limit: 5 }),
        ])
        const worksList = Array.isArray(worksRes) ? worksRes : (worksRes?.data || [])
        const contractsList = Array.isArray(contractsRes) ? contractsRes : (contractsRes?.data || [])

      // 统计计数：从全局缓存或后端获取
      const savedStats = wx.getStorageSync('stats_cache')
      const now = Date.now()
      let stats = { works: 0, contracts: 0, creators: 0 }
      if (savedStats && savedStats.expire > now) {
        stats = savedStats.stats
      }

      // 用实际返回数量作为最低值
      if (worksList.length > stats.works) stats.works = worksList.length
      if (contractsList.length > stats.contracts) stats.contracts = contractsList.length

      // 简单估算创作者数（去重）
      const creatorIds = new Set()
      worksList.forEach((w) => { if (w.author_id) creatorIds.add(w.author_id) })
      if (creatorIds.size > stats.creators) stats.creators = creatorIds.size
      if (stats.creators === 0) stats.creators = 128 // 初始占位值

      // 缓存 10 分钟
      wx.setStorageSync('stats_cache', { stats, expire: now + 600000 })

      this.setData({
        featuredWorks: worksList,
        recentContracts: contractsList,
        statCounts: stats,
      })
    } catch (e) {
      console.error('loadDashboard failed:', e)
    } finally {
      this.setData({ loading: false })
    }
  },

  async loadNotifications() {
    try {
      const res = await getMyNotifications({ limit: 3 })
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

  goWorkDetail(e) {
    wx.navigateTo({ url: `/pages/works/detail?id=${e.currentTarget.dataset.id}` })
  },

  goContractDetail(e) {
    wx.navigateTo({ url: `/pages/contracts/detail?id=${e.currentTarget.dataset.id}` })
  },
})
