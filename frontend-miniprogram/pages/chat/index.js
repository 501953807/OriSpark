// pages/chat/index.js
const app = getApp()

Page({
  data: { sessions: [], loading: false },

  onLoad() {
    this.loadSessions()
  },

  onShow() {
    if (this.data.sessions.length > 0) {
      this.loadSessions()
    }
  },

  async loadSessions() {
    this.setData({ loading: true })
    try {
      const res = await app.request({
        url: '/api/chat/sessions?limit=50',
        method: 'GET',
      })
      const sessions = (Array.isArray(res) ? res : []).map(s => ({
        ...s,
        _time: this.formatTime(s.last_message_at),
      }))
      this.setData({ sessions, loading: false })
    } catch (e) {
      console.error('Failed to load sessions:', e)
      this.setData({ loading: false })
    }
  },

  formatTime(ts) {
    if (!ts) return ''
    const d = new Date(ts)
    const h = String(d.getHours()).padStart(2, '0')
    const m = String(d.getMinutes()).padStart(2, '0')
    return `${h}:${m}`
  },

  enterSession(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/chat/detail?id=${id}` })
  },
})
