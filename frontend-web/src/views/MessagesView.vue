<template>
  <div class="messages-view">
    <div class="messages-header">
      <h1 class="messages-title">消息中心</h1>
      <div class="messages-actions">
        <button class="btn btn-ghost btn-sm" @click="markAllRead">全部已读</button>
        <button class="btn btn-ghost btn-sm">设置</button>
      </div>
    </div>

    <div class="messages-layout">
      <!-- Category sidebar -->
      <aside class="messages-sidebar">
        <button
          v-for="cat in categories"
          :key="cat.key"
          :class="['messages-cat', { active: activeCategory === cat.key }]"
          @click="activeCategory = cat.key"
        >
          <span class="messages-cat-icon material-icons">{{ cat.icon }}</span>
          <span class="messages-cat-label">{{ cat.label }}</span>
          <span v-if="cat.count > 0" class="messages-cat-badge">{{ cat.count }}</span>
        </button>
      </aside>

      <!-- Message list -->
      <main class="messages-main">
        <div v-if="messages.length === 0" class="messages-empty">
          <span class="material-icons messages-empty-icon">chat_bubble_outline</span>
          <p>暂无消息</p>
          <span class="messages-empty-hint">系统通知和交易提醒将在此显示</span>
        </div>

        <div v-for="msg in messages" :key="msg.id" class="message-item" :class="{ unread: !msg.read }" @click="readMessage(msg)">
          <div class="message-icon" :style="{ background: msg.color || 'var(--m-accent)' }">
            <span class="material-icons">{{ msg.icon }}</span>
          </div>
          <div class="message-body">
            <div class="message-title">{{ msg.title }}</div>
            <div class="message-content">{{ msg.content }}</div>
            <div class="message-meta">
              <span class="message-type">{{ msg.typeLabel }}</span>
              <span class="message-time">{{ msg.time }}</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Message {
  id: string
  title: string
  content: string
  type: string
  typeLabel: string
  icon: string
  color: string
  time: string
  read: boolean
}

const activeCategory = ref('all')

const categories = [
  { key: 'all', label: '全部', icon: 'inbox', count: 12 },
  { key: 'system', label: '系统通知', icon: 'notifications', count: 5 },
  { key: 'trade', label: '交易提醒', icon: 'payments', count: 7 },
]

const messages = ref<Message[]>([])
</script>

<style scoped>
.messages-view {
  max-width: 960px;
}
.messages-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.messages-title {
  font-size: 1.25rem;
  font-weight: 700;
  margin: 0;
  color: var(--m-on-surface, #2E263D);
}
.messages-actions {
  display: flex;
  gap: 8px;
}

.messages-layout {
  display: flex;
  gap: 20px;
}

/* Category sidebar */
.messages-sidebar {
  width: 160px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.messages-cat {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: none;
  background: none;
  border-radius: var(--m-radius-sm);
  cursor: pointer;
  font-size: 0.875rem;
  color: var(--m-muted, #8A8D93);
  text-align: left;
  width: 100%;
  transition: all 0.15s;
  font-family: inherit;
}
.messages-cat:hover {
  background: var(--m-sidebar-hover-bg, #F4F5FA);
  color: var(--m-on-surface, #2E263D);
}
.messages-cat.active {
  background: linear-gradient(135deg, #8C57FF, #6A3FCC);
  color: #fff;
}
.messages-cat-icon { font-size: 1.1rem !important; }
.messages-cat-label { flex: 1; }
.messages-cat-badge {
  background: rgba(255,255,255,0.25);
  color: #fff;
  font-size: 0.65rem;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 100px;
}
.messages-cat.active .messages-cat-badge {
  background: rgba(255,255,255,0.35);
}

/* Message list */
.messages-main {
  flex: 1;
  min-width: 0;
}
.message-item {
  display: flex;
  gap: 12px;
  padding: 14px;
  border-radius: var(--m-radius-sm);
  border: 1px solid var(--m-border, rgba(46,38,61,0.12));
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.15s;
  background: var(--m-surface, #fff);
}
.message-item:hover {
  box-shadow: 0 2px 8px rgba(46,38,61,0.08);
  border-color: rgba(139,92,246,0.3);
}
.message-item.unread {
  background: rgba(139,92,255,0.04);
  border-color: rgba(139,92,255,0.2);
}
.message-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #fff;
}
.message-icon .material-icons { font-size: 1.1rem !important; }
.message-body { flex: 1; min-width: 0; }
.message-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--m-on-surface, #2E263D);
  margin-bottom: 2px;
}
.message-content {
  font-size: 0.82rem;
  color: var(--m-muted, #8A8D93);
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.message-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.72rem;
  color: var(--m-muted, #8A8D93);
}
.message-type {
  padding: 1px 6px;
  background: var(--m-surface-2, #EEF0F4);
  border-radius: 4px;
}
.message-time { color: var(--m-muted, #8A8D93); }

/* Empty state */
.messages-empty {
  text-align: center;
  padding: 60px 20px;
  color: var(--m-muted, #8A8D93);
}
.messages-empty-icon {
  font-size: 3rem;
  color: var(--m-muted, #8A8D93);
  opacity: 0.4;
  margin-bottom: 12px;
  display: block;
}
.messages-empty p {
  font-size: 1rem;
  margin: 0 0 8px;
  color: var(--m-on-surface, #2E263D);
}
.messages-empty-hint {
  font-size: 0.82rem;
  color: var(--m-muted, #8A8D93);
}

@media (max-width: 767px) {
  .messages-layout { flex-direction: column; }
  .messages-sidebar { width: 100%; flex-direction: row; overflow-x: auto; }
  .messages-cat { white-space: nowrap; }
}
</style>
