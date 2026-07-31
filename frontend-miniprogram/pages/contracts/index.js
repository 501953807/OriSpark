// pages/contracts/index.js
const { getPublicContracts } = require('../../api/contracts')
const { isLowEndDevice } = require('../../utils/motion')

Page({
  data: {
    contracts: [],
    loading: false,
    itemDelay: isLowEndDevice() ? 0 : 40,
  },
  onLoad() { this.loadContracts() },
  async loadContracts() {
    this.setData({ loading: true })
    try { const res = await getPublicContracts(); this.setData({ contracts: Array.isArray(res) ? res : (res?.data || []) }) }
    catch (e) { console.error(e) }
    finally { this.setData({ loading: false }) }
  },
  goDetail(e) { wx.navigateTo({ url: `/pages/contracts/detail?id=${e.currentTarget.dataset.id}` }) },
})
