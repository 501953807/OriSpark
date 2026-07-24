// pages/chat/detail.js
const app = getApp()

Page({
  data: { sessionId: '', messages: [], inputText: '', scrollIntoView: '' },
  wsTask: null,
  wsConnected: false,

  onLoad(e) {
    this.setData({ sessionId: e.id })
    this.connectWebSocket()
    this.loadMessages()
  },

  onUnload() {
    this.disconnectWebSocket()
  },

  disconnectWebSocket() {
    if (this.wsTask) {
      this.wsTask.close()
      this.wsTask = null
    }
    this.wsConnected = false
  },

  connectWebSocket() {
    const { sessionId } = this.data
    if (!sessionId) return

    // 获取后端地址（将 https://api.xxx.com/api 转为 wss://api.xxx.com/ws）
    const apiBase = app.globalData.apiBase
    const wsUrl = apiBase.replace(/^https?:\/\//, 'wss://').replace(/\/api$/, '/ws')
    const url = `${wsUrl}/chat/${sessionId}?token=${encodeURIComponent(app.globalData.token || '')}`

    this.wsTask = wx.connectSocket({
      url,
      protocols: [app.globalData.token || ''],
    })

    this.wsTask.onOpen(() => {
      console.log('WebSocket connected')
      this.wsConnected = true
      // 发送 join 消息
      this.wsTask.sendJSON({
        type: 'join',
        user_id: app.globalData.userId || 'local',
      })
    })

    this.wsTask.onMessage((res) => {
      try {
        const data = JSON.parse(res.data)
        this.handleWsMessage(data)
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    })

    this.wsTask.onError((err) => {
      console.error('WebSocket error:', err)
      this.wsConnected = false
    })

    this.wsTask.onClose(() => {
      console.log('WebSocket closed, reconnecting in 3s...')
      this.wsConnected = false
      setTimeout(() => {
        if (this.data.sessionId) {
          this.connectWebSocket()
        }
      }, 3000)
    })
  },

  handleWsMessage(data) {
    switch (data.type) {
      case 'joined':
        console.log('Joined chat session:', data.session_id)
        break

      case 'peer_joined':
        console.log('Peer joined:', data.user_id)
        break

      case 'message':
        // 收到新消息，追加到列表
        const msg = {
          id: Date.now().toString(),
          sender_id: data.sender_id,
          content: data.content,
          created_at: data.created_at,
          _time: this.formatTime(data.created_at),
          _isMe: data.sender_id === app.globalData.userId || data.sender_id === 'me',
        }
        this.setData({
          messages: this.data.messages.concat([msg]),
        })
        this.scrollToBottom()
        break

      case 'pong':
        // 心跳响应，不做处理
        break

      case 'error':
        wx.showToast({ title: data.message || '连接失败', icon: 'none' })
        break
    }
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
      const len = this.data.messages.length
      this.setData({ scrollIntoView: 'msg-' + (len - 1) })
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

    // 优先通过 WebSocket 发送（实时）
    if (this.wsConnected && this.wsTask) {
      try {
        this.wsTask.sendJSON({
          type: 'message',
          content: text,
        })
        // 乐观 UI 更新
        const now = new Date().toISOString()
        const msgs = this.data.messages.concat([{
          id: Date.now().toString(),
          sender_id: app.globalData.userId || 'me',
          content: text,
          created_at: now,
          _time: this.formatTime(now),
          _isMe: true,
        }])
        this.setData({ messages: msgs, inputText: '' })
        this.scrollToBottom()
        return
      } catch (e) {
        console.warn('WebSocket send failed, falling back to HTTP:', e)
      }
    }

    // 降级到 HTTP 发送
    try {
      const res = await app.request({
        url: `/api/chat/sessions/${sessionId}/messages`,
        method: 'POST',
        data: { content: text },
      })

      // Add to local list immediately for optimistic UI
      const msgs = this.data.messages.concat([{
        id: res.id,
        sender_id: 'me',
        content: res.content,
        created_at: res.created_at,
        _time: this.formatTime(res.created_at),
        _isMe: true,
      }])
      this.setData({ messages: msgs, inputText: '' })
      this.scrollToBottom()
    } catch (e) {
      console.error('Failed to send message:', e)
      wx.showToast({ title: '发送失败', icon: 'none' })
    }
  },
})
