// pages/contracts/detail.js
const { getPublicContracts } = require('../../api/contracts')

Page({
  data: { contract: null, loading: true },

  onLoad(options) {
    if (options.id) {
      this.loadContract(options.id)
    } else {
      this.setData({ loading: false })
    }
  },

  async loadContract(id) {
    try {
      const res = await getPublicContracts({ limit: 100 })
      const contracts = Array.isArray(res) ? res : (res?.data || [])
      const contract = contracts.find(c => c.id === id)
      this.setData({ contract, loading: false })
    } catch (e) {
      console.error('loadContract failed:', e)
      this.setData({ loading: false })
    }
  },

  onContactCreator() {
    wx.showToast({ title: '联系客服对接', icon: 'none' })
  },
})
