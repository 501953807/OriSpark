// pages/works/index.js
const { getMyWorks } = require('../../api/works')
const { isLowEndDevice } = require('../../utils/motion')

Page({
  data: {
    works: [],
    loading: false,
    itemDelay: isLowEndDevice() ? 0 : 50,
  },

  onLoad() { this.loadWorks() },

  async loadWorks() {
    this.setData({ loading: true })
    try {
      const res = await getMyWorks({ limit: 20 })
      this.setData({ works: Array.isArray(res) ? res : (res?.data || []) })
    } catch (e) { console.error(e) }
    finally { this.setData({ loading: false }) }
  },

  goDetail(e) {
    wx.navigateTo({ url: `/pages/works/detail?id=${e.currentTarget.dataset.id}` })
  },
})
