// pages/notifications/index.js
const { getPublicNotifications } = require('../../api/notifications')

Page({
  data: { notifications: [], loading: false },
  onLoad() { this.loadNotifications() },
  async loadNotifications() {
    this.setData({ loading: true })
    try {
      const res = await getPublicNotifications()
      this.setData({ notifications: Array.isArray(res) ? res : (res?.data || []) })
    } catch (e) { console.error(e) }
    finally { this.setData({ loading: false }) }
  },
})
