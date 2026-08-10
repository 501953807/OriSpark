// pages/operations/index.js
const { getOperatorOperations, getCreatorPendingOperations, acceptCooperation, rejectCooperation } = require('../../api/operations')

Page({
  data: {
    operations: [],
    loading: false,
    activeTab: 'all',
  },

  onLoad() {
    this.loadOperations()
  },

  onShow() {
    this.loadOperations()
  },

  async loadOperations() {
    this.setData({ loading: true })
    try {
      const token = wx.getStorageSync('token')
      let res
      if (token) {
        // 尝试作为运营者获取列表
        try {
          res = await getOperatorOperations()
          this.setData({ operations: Array.isArray(res) ? res : (res?.data || []) })
          return
        } catch (e) {
          // 如果运营者接口失败，尝试创作者待办
        }
        try {
          res = await getCreatorPendingOperations()
          this.setData({ operations: Array.isArray(res) ? res : (res?.data || []) })
          return
        } catch (e2) {
          console.error('Both operations APIs failed:', e2)
        }
      }
      this.setData({ operations: [] })
    } catch (e) {
      console.error('loadOperations failed:', e)
    } finally {
      this.setData({ loading: false })
    }
  },

  switchTab(e) {
    const tab = e.currentTarget.dataset.tab
    this.setData({ activeTab: tab })
    this.loadOperations()
  },

  async handleAccept(e) {
    const id = e.currentTarget.dataset.id
    try {
      wx.showLoading({ title: '处理中...' })
      await acceptCooperation(id)
      wx.hideLoading()
      wx.showToast({ title: '已接受', icon: 'success' })
      this.loadOperations()
    } catch (err) {
      wx.hideLoading()
      wx.showToast({ title: '操作失败', icon: 'none' })
    }
  },

  async handleReject(e) {
    const id = e.currentTarget.dataset.id
    try {
      wx.showLoading({ title: '处理中...' })
      await rejectCooperation(id)
      wx.hideLoading()
      wx.showToast({ title: '已拒绝', icon: 'none' })
      this.loadOperations()
    } catch (err) {
      wx.hideLoading()
      wx.showToast({ title: '操作失败', icon: 'none' })
    }
  },

  formatTime(iso) {
    if (!iso) return ''
    const d = new Date(iso)
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  },

  goToDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/operations/detail?id=${id}` })
  },
})
