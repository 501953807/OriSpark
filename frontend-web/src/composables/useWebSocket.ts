/** WebSocket 连接管理 composable — 自动重连，按 user_id 推送通知. */
import { ref, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/useAuthStore'

const WS_PATH = '/ws/notifications'
const RECONNECT_BASE = 3000
const RECONNECT_MAX = 30000

let _ws: WebSocket | null = null
let _reconnectTimer: ReturnType<typeof setTimeout> | null = null
let _heartbeatTimer: ReturnType<typeof setInterval> | null = null
let _msgListeners: Set<(msg: any) => void> = new Set()

const _status = ref<'closed' | 'connecting' | 'open' | 'error'>('closed')
const _lastMessage = ref<any>(null)

function _getUrl(): string {
  const token = useAuthStore().token
  if (!token) return ''
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = import.meta.env.VITE_WS_URL || `${location.protocol}//${location.host}`
  return `${host}${WS_PATH}?token=${encodeURIComponent(token)}`
}

function _startHeartbeat() {
  _stopHeartbeat()
  _heartbeatTimer = setInterval(() => {
    if (_ws && _ws.readyState === WebSocket.OPEN) {
      _ws.send(JSON.stringify({ type: 'ping' }))
    }
  }, 25000)
}

function _stopHeartbeat() {
  if (_heartbeatTimer) { clearInterval(_heartbeatTimer); _heartbeatTimer = null }
}

function _scheduleReconnect() {
  if (_reconnectTimer) clearTimeout(_reconnectTimer)
  _reconnectTimer = setTimeout(() => {
    const delay = Math.min(RECONNECT_BASE * Math.pow(1.5, Math.random()), RECONNECT_MAX)
    _reconnectTimer = setTimeout(connect, delay)
  }, RECONNECT_BASE)
}

function connect() {
  if (_ws) return
  const url = _getUrl()
  if (!url) { _status.value = 'error'; return }
  _status.value = 'connecting'
  try {
    _ws = new WebSocket(url)
  } catch { _status.value = 'error'; _scheduleReconnect(); return }

  _ws.onopen = () => { _status.value = 'open'; _startHeartbeat() }
  _ws.onmessage = (e: MessageEvent) => {
    try { _lastMessage.value = JSON.parse(e.data as string) } catch { _lastMessage.value = e.data }
    for (const fn of _msgListeners) { try { fn(_lastMessage.value) } catch { /* ignore */ } }
  }
  _ws.onerror = () => { _status.value = 'error' }
  _ws.onclose = () => {
    _ws = null; _stopHeartbeat(); _status.value = 'closed'
    _scheduleReconnect()
  }
}

function send(data: any) {
  if (_ws && _ws.readyState === WebSocket.OPEN) _ws.send(JSON.stringify(data))
}

function onMessage(fn: (msg: any) => void) {
  _msgListeners.add(fn)
  return () => { _msgListeners.delete(fn) }
}

function disconnect() {
  if (_reconnectTimer) clearTimeout(_reconnectTimer)
  _stopHeartbeat()
  if (_ws) { _ws.close(); _ws = null }
  _status.value = 'closed'
}

export const useWebSocket = () => {
  onUnmounted(() => disconnect())
  return { status: _status, lastMessage: _lastMessage, connect, send, disconnect, onMessage }
}

export const wsClient = { connect, disconnect, send, onMessage, status: _status, lastMessage: _lastMessage }
