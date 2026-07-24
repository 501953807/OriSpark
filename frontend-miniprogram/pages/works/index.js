// pages/works/index.js
const { getPublicWorks } = require('../../api/works')

Page({
  data: { works: [], loading: false },

  onLoad() { this.loadWorks() },

  async loadWorks() {
    this.setData({ loading: true })
    try {
      const res = await getPublicWorks({ limit: 20 })
      this.setData({ works: Array.isArray(res) ? res : (res?.data || []) })
    } catch (e) { console.error(e) }
    finally { this.setData({ loading: false }) }
  },

  goDetail(e) {
    wx.navigateTo({ url: `/pages/works/detail?id=${e.currentTarget.dataset.id}` })
  },
})
