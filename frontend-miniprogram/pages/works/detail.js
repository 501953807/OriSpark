// pages/works/detail.js
const { getMyWorkDetail } = require('../../api/works')

Page({
  data: { work: null, loading: true },

  onLoad(options) {
    if (options.id) {
      this.loadWork(options.id)
    } else {
      this.setData({ loading: false })
    }
  },

  async loadWork(id) {
    try {
      const res = await getMyWorkDetail(id)
      this.setData({ work: res?.data || res, loading: false })
    } catch (e) {
      console.error('loadWork failed:', e)
      this.setData({ loading: false })
    }
  },
})
