// pages/contracts/detail.js
const { getContractDetail } = require('../../api/contracts')

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
      const res = await getContractDetail(id)
      this.setData({ contract: res?.data || res, loading: false })
    } catch (e) {
      console.error('loadContract failed:', e)
      this.setData({ loading: false })
    }
  },

  onContactCreator() {
    wx.showToast({ title: '联系客服对接', icon: 'none' })
  },
})
