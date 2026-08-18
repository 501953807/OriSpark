<template>
  <div class="messages-view">
    <div class="m-page-header">
      <h1 class="m-page-title">消息中心</h1>
      <p class="m-page-subtitle">系统通知与平台消息</p>
    </div>

    <div class="messages-layout">
      <div class="messages-sidebar">
        <div class="messages-tab" :class="{ active: activeTab === 'all' }" @click="activeTab = 'all'">
          <span class="material-icons">inbox</span>
          全部 ({{ totalUnread }})
          <span v-if="totalUnread > 0" class="msg-dot"></span>
        </div>
        <div class="messages-tab" :class="{ active: activeTab === 'system' }" @click="activeTab = 'system'">
          <span class="material-icons">notifications</span>
          系统通知 (5)
        </div>
        <div class="messages-tab" :class="{ active: activeTab === 'alerts' }" @click="activeTab = 'alerts'">
          <span class="material-icons">warning</span>
          风险预警 ({{ alertCount }})
          <span v-if="alertCount > 0" class="msg-dot"></span>
        </div>
        <div class="messages-tab" :class="{ active: activeTab === 'transactions' }" @click="activeTab = 'transactions'">
          <span class="material-icons">payments</span>
          交易提醒 (0)
        </div>
      </div>

      <div class="messages-main">
        <div class="messages-header-bar">
          <span class="messages-title">{{ tabLabel }}</span>
          <button class="btn btn-ghost btn-sm" @click="markAllRead" v-if="hasUnread">
            <span class="material-icons" style="font-size:16px">done_all</span>
            全部已读
          </button>
        </div>

        <div class="messages-empty">
          <span class="material-icons" style="font-size:48px;color:var(--m-grey-300)">mail_outline</span>
          <p style="color:var(--m-muted);margin:12px 0 4px;font-size:.95rem">暂无消息</p>
          <p style="color:var(--m-muted);font-size:.8rem;margin:0">消息将在此处显示</p>
          <span class="status-badge planned">规划中 — 后续对接消息 API</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAppStore } from '@/stores/useAppStore'

const appStore = useAppStore()
const activeTab = ref<'all' | 'system' | 'alerts' | 'transactions'>('all')

const alertCount = computed(() => appStore.alertCount)
const totalUnread = computed(() => alertCount.value > 0 ? alertCount.value + 1 : 0)
const hasUnread = computed(() => totalUnread.value > 0)

const tabLabels: Record<string, string> = {
  all: '全部消息',
  system: '系统通知',
  alerts: '风险预警',
  transactions: '交易提醒',
}
const tabLabel = computed(() => tabLabels[activeTab.value] || '消息')

function markAllRead() {
  // 占位：后续对接 API
}
</script>

<style scoped>
.messages-view {
  padding: 24px;
  max-width: 1200px;
}

.messages-layout {
  display: flex;
  gap: 24px;
  margin-top: 20px;
}

.messages-sidebar {
  width: 200px;
  flex-shrink: 0;
  background: var(--m-surface, #fff);
  border: 1px solid var(--m-border, rgba(46,38,61,0.12));
  border-radius: var(--m-radius-md, 10px);
  padding: 8px;
}

.messages-tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: var(--m-radius-sm, 6px);
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--m-sidebar-fg-dim, #8A8D93);
  cursor: pointer;
  transition: all 0.15s;
}
.messages-tab:hover {
  background: var(--m-sidebar-hover-bg, var(--m-bg-subtle, #F1F5F9));
  color: var(--m-on-surface, #2E263D);
}
.messages-tab.active {
  background: linear-gradient(135deg, #5585FF, #2A52B0);
  color: var(--m-surface, #fff);
  font-weight: 600;
}
.messages-tab .material-icons { font-size: 1.15rem; }
.msg-dot {
  margin-left: auto;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #DC2626;
}

.messages-main {
  flex: 1;
  min-width: 0;
  background: var(--m-surface, #fff);
  border: 1px solid var(--m-border, rgba(46,38,61,0.12));
  border-radius: var(--m-radius-md, 10px);
  overflow: hidden;
}

.messages-header-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--m-border, rgba(46,38,61,0.12));
}
.messages-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--m-on-surface, #2E263D);
}
.messages-empty {
  padding: 60px 20px;
  text-align: center;
}
.status-badge {
  display: inline-block; margin-top: 12px; padding: 4px 14px; border-radius: 100px;
  font-size: 0.72rem; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase;
}
.status-badge.planned {
  background: rgba(var(--m-primary-rgb, 140,87,255), 0.1); color: var(--m-primary);
}

@media (max-width: 767px) {
  .messages-layout { flex-direction: column; }
  .messages-sidebar {
    width: 100%;
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }
  .messages-tab {
    flex: 1;
    min-width: 120px;
    justify-content: center;
    font-size: 0.78rem;
    padding: 8px;
  }
}
</style>
