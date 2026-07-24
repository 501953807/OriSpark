// pages/contracts/index.js
const { getPublicContracts } = require('../../api/contracts')

Page({
  data: { contracts: [], loading: false },
  onLoad() { this.loadContracts() },
  async loadContracts() {
    this.setData({ loading: true })
    try { const res = await getPublicContracts(); this.setData({ contracts: Array.isArray(res) ? res : (res?.data || []) }) }
    catch (e) { console.error(e) }
    finally { this.setData({ loading: false }) }
  },
  goDetail(e) { wx.navigateTo({ url: `/pages/contracts/detail?id=${e.currentTarget.dataset.id}` }) },
})
