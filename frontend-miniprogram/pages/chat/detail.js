// pages/chat/detail.js
const app = getApp()

Page({
  data: { sessionId: '', messages: [], inputText: '', scrollIntoView: '' },

  onLoad(e) {
    this.setData({ sessionId: e.id })
    this.loadMessages()
  },

  async loadMessages() {
    const { sessionId } = this.data
    if (!sessionId) return
    try {
      const res = await app.request({
        url: `/api/chat/sessions/${sessionId}/messages?limit=50`,
        method: 'GET',
      })
      // Backend returns messages in desc order, reverse for display + format time
      const messages = (Array.isArray(res) ? res.reverse() : []).map((m, i) => ({
        ...m,
        _time: this.formatTime(m.created_at),
        _isMe: m.sender_id === app.globalData.userId || m.sender_id === 'me',
      }))
      this.setData({ messages })
      this.scrollToBottom()
    } catch (e) {
      console.error('Failed to load messages:', e)
    }
  },

  scrollToBottom() {
    setTimeout(() => {
      this.setData({ scrollIntoView: 'msg-' + (this.data.messages.length - 1) })
    }, 100)
  },

  formatTime(ts) {
    if (!ts) return ''
    const d = new Date(ts)
    const h = String(d.getHours()).padStart(2, '0')
    const m = String(d.getMinutes()).padStart(2, '0')
    return `${h}:${m}`
  },

  onInput(e) {
    this.setData({ inputText: e.detail.value })
  },

  async onSend() {
    const text = this.data.inputText.trim()
    if (!text) return

    const { sessionId } = this.data
    try {
      const res = await app.request({
        url: `/api/chat/sessions/${sessionId}/messages`,
        method: 'POST',
        data: { content: text },
      })

      // Add to local list immediately for optimistic UI
      const msgs = this.data.messages.concat([{
        id: res.id,
        sender_id: 'me',  // Will be corrected on next load
        content: res.content,
        created_at: res.created_at,
      }])
      this.setData({ messages: msgs, inputText: '' })
      this.scrollToBottom()
    } catch (e) {
      console.error('Failed to send message:', e)
      wx.showToast({ title: '发送失败', icon: 'none' })
    }
  },
})
