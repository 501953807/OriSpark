<template>
  <div class="notif-wrapper">
    <button class="btn btn-ghost notif-btn" @click="togglePanel" title="通知">
      🔔
      <span v-if="unreadCount > 0" class="notif-badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
    </button>

    <!-- Dropdown panel -->
    <div v-if="panelOpen" class="notif-panel" @click.stop>
      <div class="notif-header">
        <span class="notif-title">通知</span>
        <button v-if="unreadCount > 0" class="notif-mark-all" @click="markAllRead">
          全部已读
        </button>
      </div>

      <div class="notif-list" v-if="notifications.length > 0">
        <div
          v-for="n in notifications"
          :key="n.id"
          class="notif-item"
          :class="{ unread: !n.is_read }"
          @click="onClickNotif(n)"
        >
          <div class="notif-dot" v-if="!n.is_read"></div>
          <div class="notif-body">
            <div class="notif-item-title">{{ n.title }}</div>
            <div class="notif-item-content" v-if="n.content">{{ n.content }}</div>
            <div class="notif-item-meta">
              <span class="notif-type">{{ typeLabel(n.type) }}</span>
              <span class="notif-time">{{ formatTime(n.created_at) }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="notif-empty">
        暂无通知
      </div>
    </div>

    <!-- Backdrop -->
    <div v-if="panelOpen" class="notif-backdrop" @click="panelOpen = false"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { systemApi } from '@/api/system'

const panelOpen = ref(false)
const notifications = ref<any[]>([])
const unreadCount = ref(0)
let pollTimer: any = null

function togglePanel() {
  panelOpen.value = !panelOpen.value
  if (panelOpen.value) {
    fetchNotifications()
  }
}

async function fetchNotifications() {
  try {
    const [notifRes, countRes] = await Promise.all([
      systemApi.notifications({ page: 1, page_size: 50 }),
      systemApi.unreadCount(),
    ])
    notifications.value = notifRes.data.data?.items || []
    unreadCount.value = countRes.data.data?.count || 0
  } catch {
    // Notifications API not available — silent fail
    notifications.value = []
    unreadCount.value = 0
  }
}

async function markAllRead() {
  try {
    await systemApi.markAllRead()
    notifications.value.forEach(n => { n.is_read = true })
    unreadCount.value = 0
  } catch (err) {
    console.error('[NotifPanel] Failed to mark all read:', err)
  }
}

async function onClickNotif(n: any) {
  if (!n.is_read) {
    try {
      await systemApi.markRead(n.id)
      n.is_read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    } catch (err) {
      console.error('[NotifPanel] Failed to mark read:', err)
    }
  }
  // 可扩展: 点击跳转到关联页面
}

const typeLabels: Record<string, string> = {
  cert_ready: '存证完成',
  scan_result: '扫描结果',
  reminder: '到期提醒',
  renewal: '续展提醒',
  order_update: '订单状态',
  quota_warning: '配额预警',
  backup_complete: '备份完成',
  system_update: '系统更新',
}

function typeLabel(type: string): string {
  return typeLabels[type] || type
}

function formatTime(ts: string | null): string {
  if (!ts) return ''
  const d = new Date(ts)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 60_000) return '刚刚'
  if (diff < 3600_000) return Math.floor(diff / 60_000) + '分钟前'
  if (diff < 86400_000) return Math.floor(diff / 3600_000) + '小时前'
  return d.toLocaleDateString('zh-CN')
}

// 定时轮询未读数
onMounted(() => {
  fetchNotifications()
  pollTimer = setInterval(async () => {
    try {
      const res = await systemApi.unreadCount()
      unreadCount.value = res.data.data?.count || 0
    } catch { /* ignore */ }
  }, 30_000) // 每30秒轮询
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
.notif-wrapper { position: relative; }
.notif-btn { position: relative; }
.notif-badge {
  position: absolute;
  top: 2px;
  right: 2px;
  background: #e53e3e;
  color: #fff;
  font-size: 0.6rem;
  font-weight: 700;
  min-width: 16px;
  height: 16px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 3px;
}

.notif-panel {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 360px;
  max-height: 480px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: 0 12px 40px oklch(0 0 0 / 0.12);
  z-index: 100;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.notif-backdrop {
  position: fixed;
  inset: 0;
  z-index: 99;
}

.notif-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border);
}
.notif-title {
  font-weight: 700;
  font-size: 0.95rem;
}
.notif-mark-all {
  font-size: 0.78rem;
  color: var(--accent);
  background: none;
  border: none;
  cursor: pointer;
  font-family: var(--font-body);
}
.notif-mark-all:hover { opacity: 0.8; }

.notif-list {
  overflow-y: auto;
  flex: 1;
}
.notif-item {
  display: flex;
  gap: 10px;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 1px solid oklch(0 0 0 / 0.04);
}
.notif-item:hover { background: oklch(96% 0.004 240); }
.notif-item.unread { background: oklch(56% 0.12 170 / 0.03); }

.notif-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent);
  margin-top: 6px;
  flex-shrink: 0;
}
.notif-body { flex: 1; min-width: 0; }
.notif-item-title {
  font-size: 0.88rem;
  font-weight: 600;
  margin-bottom: 2px;
}
.notif-item-content {
  font-size: 0.8rem;
  color: var(--muted);
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.notif-item-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.72rem;
  color: var(--muted);
}
.notif-type {
  padding: 1px 6px;
  border-radius: 4px;
  background: oklch(95% 0.01 240);
}

.notif-empty {
  padding: 40px 16px;
  text-align: center;
  color: var(--muted);
  font-size: 0.88rem;
}
</style>
