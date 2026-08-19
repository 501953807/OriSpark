<!-- OriSpark Profile Page — 个人/企业信息管理 -->
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '~/stores/auth'

definePageMeta({ layout: 'materio-topnav' })

const auth = useAuthStore()
const loading = ref(false)
const activeTab = ref('basic')

const basicInfo = ref({
  name: '',
  email: '',
  phone: '',
  company: '',
  role: '',
  credit_score: 0,
  join_date: '',
})

const documents = ref([
  { type: '营业执照', status: '已认证', date: '2026-01-15' },
  { type: '身份证', status: '已认证', date: '2026-01-15' },
  { type: '税务登记证', status: '待上传', date: '' },
])

const notifications = ref([
  { id: '1', type: 'system', title: '信用评分更新', content: '您的信用评分已提升至 780 分', date: '2026-08-18', read: false },
  { id: '2', type: 'contract', title: '合约即将到期', content: '合约 #2026001 将在 3 天后到期', date: '2026-08-17', read: false },
  { id: '3', type: 'payment', title: '结算通知', content: '本月结算已完成，金额 ¥12,500', date: '2026-08-15', read: true },
])

const unreadCount = computed(() => notifications.value.filter(n => !n.read).length)

async function loadProfile() {
  loading.value = true
  try {
    // TODO: 对接后端 API
    basicInfo.value = {
      name: auth.user?.name || '张三',
      email: auth.user?.email || 'zhangsan@orispark.com',
      phone: '138****8888',
      company: '某某文化有限公司',
      role: auth.user?.role || 'trader',
      credit_score: 780,
      join_date: '2025-06-01',
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadProfile()
})

function markAsRead(id: string) {
  const notif = notifications.value.find(n => n.id === id)
  if (notif) notif.read = true
}
</script>

<template>
  <div class="page-profile">
    <!-- Header -->
    <div class="profile-header">
      <h1 class="page-title">个人中心</h1>
      <div class="header-actions">
        <button class="btn-secondary" @click="$router.push('/settings')">⚙️ 设置</button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <span>加载中...</span>
    </div>

    <template v-else>
      <!-- User Card -->
      <div class="card">
        <div class="user-card">
          <div class="avatar">{{ basicInfo.name.charAt(0) }}</div>
          <div class="user-info">
            <h2>{{ basicInfo.name }}</h2>
            <p class="user-role">{{ basicInfo.role }}</p>
            <p class="user-email">{{ basicInfo.email }}</p>
          </div>
          <div class="credit-badge">
            <span class="credit-score">{{ basicInfo.credit_score }}</span>
            <span class="credit-label">信用分</span>
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="tabs">
        <button :class="['tab-btn', { active: activeTab === 'basic' }]" @click="activeTab = 'basic'">基本信息</button>
        <button :class="['tab-btn', { active: activeTab === 'docs' }]" @click="activeTab = 'docs'">认证资料</button>
        <button :class="['tab-btn', { active: activeTab === 'notify' }]" @click="activeTab = 'notify'">
          通知
          <span v-if="unreadCount" class="badge">{{ unreadCount }}</span>
        </button>
      </div>

      <!-- Basic Info Tab -->
      <div v-if="activeTab === 'basic'" class="card tab-content">
        <div class="card-header">
          <h3 class="card-title">基本信息</h3>
        </div>
        <div class="card-body">
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">姓名</span>
              <span class="info-value">{{ basicInfo.name }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">邮箱</span>
              <span class="info-value">{{ basicInfo.email }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">手机</span>
              <span class="info-value">{{ basicInfo.phone }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">公司</span>
              <span class="info-value">{{ basicInfo.company || '未填写' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">角色</span>
              <span class="info-value">{{ basicInfo.role }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">注册时间</span>
              <span class="info-value">{{ basicInfo.join_date }}</span>
            </div>
          </div>
          <div class="action-footer">
            <button class="btn-primary">编辑信息</button>
          </div>
        </div>
      </div>

      <!-- Documents Tab -->
      <div v-if="activeTab === 'docs'" class="card tab-content">
        <div class="card-header">
          <h3 class="card-title">认证资料</h3>
        </div>
        <div class="card-body">
          <div class="doc-list">
            <div v-for="(doc, i) in documents" :key="i" class="doc-item">
              <div class="doc-info">
                <span class="doc-name">{{ doc.type }}</span>
                <span :class="['doc-status', doc.status === '已认证' ? 'status-ok' : 'status-pending']">
                  {{ doc.status }}
                </span>
              </div>
              <div class="doc-actions">
                <span v-if="doc.date" class="doc-date">{{ doc.date }}</span>
                <button class="btn-small" :disabled="doc.status === '已认证'">
                  {{ doc.status === '已认证' ? '已认证' : '上传' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Notifications Tab -->
      <div v-if="activeTab === 'notify'" class="card tab-content">
        <div class="card-header">
          <h3 class="card-title">通知中心</h3>
        </div>
        <div class="card-body">
          <div class="notify-list">
            <div v-if="notifications.length === 0" class="empty-state">暂无通知</div>
            <div v-for="n in notifications" :key="n.id" class="notify-item" :class="{ unread: !n.read }" @click="markAsRead(n.id)">
              <div class="notify-icon" :class="`type-${n.type}`">
                {{ n.type === 'system' ? '🔔' : n.type === 'contract' ? '📝' : '💰' }}
              </div>
              <div class="notify-content">
                <div class="notify-title">{{ n.title }}</div>
                <div class="notify-desc">{{ n.content }}</div>
                <div class="notify-date">{{ n.date }}</div>
              </div>
              <div class="notify-unread-dot" v-if="!n.read"></div>
            </div>
          </div>
          <div class="action-footer">
            <button class="btn-secondary" @click="notifications.forEach(n => n.read = true)">全部已读</button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.page-profile {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem;
}

.profile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  margin-bottom: 1.5rem;
  overflow: hidden;
}

.card-header {
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.card-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #1f2937;
}

.card-body {
  padding: 1.5rem;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 1.5rem;
}

.avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, #7c3aed, #3b82f6);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: 700;
}

.user-info h2 {
  margin: 0 0 0.25rem;
  font-size: 1.25rem;
  color: #1f2937;
}

.user-role {
  margin: 0 0 0.25rem;
  font-size: 0.875rem;
  color: #7c3aed;
  font-weight: 600;
}

.user-email {
  margin: 0;
  font-size: 0.875rem;
  color: #6b7280;
}

.credit-badge {
  margin-left: auto;
  text-align: center;
}

.credit-score {
  display: block;
  font-size: 2rem;
  font-weight: 700;
  color: #10b981;
}

.credit-label {
  font-size: 0.75rem;
  color: #6b7280;
}

.tabs {
  display: flex;
  gap: 0.5rem;
  border-bottom: 1px solid #e5e7eb;
  margin-bottom: 0;
  padding: 0 1.5rem;
  background: #fff;
  border-radius: 12px 12px 0 0;
}

.tab-btn {
  padding: 0.875rem 1.25rem;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 0.9375rem;
  font-weight: 500;
  color: #6b7280;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.tab-btn.active {
  color: #7c3aed;
  border-bottom-color: #7c3aed;
}

.badge {
  background: #ef4444;
  color: #fff;
  font-size: 0.7rem;
  padding: 2px 6px;
  border-radius: 10px;
}

.tab-content {
  animation: fadeIn 0.2s;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.info-label {
  font-size: 0.8rem;
  color: #6b7280;
}

.info-value {
  font-size: 0.9375rem;
  color: #1f2937;
  font-weight: 500;
}

.action-footer {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.doc-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.doc-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  background: #f9fafb;
  border-radius: 8px;
}

.doc-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.doc-name {
  font-weight: 600;
  color: #1f2937;
}

.doc-status {
  font-size: 0.8rem;
  padding: 2px 8px;
  border-radius: 4px;
}

.status-ok {
  background: #d1fae5;
  color: #065f46;
}

.status-pending {
  background: #fef3c7;
  color: #92400e;
}

.doc-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.doc-date {
  font-size: 0.8rem;
  color: #6b7280;
}

.btn-small {
  padding: 0.375rem 0.75rem;
  font-size: 0.8rem;
  border-radius: 6px;
  border: 1px solid #d1d5db;
  background: #fff;
  cursor: pointer;
}

.btn-small:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.notify-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.notify-item {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.notify-item:hover {
  background: #f9fafb;
}

.notify-item.unread {
  background: #ede9fe;
}

.notify-icon {
  font-size: 1.25rem;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #fff;
  flex-shrink: 0;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.notify-content {
  flex: 1;
}

.notify-title {
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.25rem;
}

.notify-desc {
  font-size: 0.875rem;
  color: #6b7280;
  margin-bottom: 0.25rem;
}

.notify-date {
  font-size: 0.75rem;
  color: #9ca3af;
}

.notify-unread-dot {
  width: 8px;
  height: 8px;
  background: #7c3aed;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 0.5rem;
}

.empty-state {
  color: #9ca3af;
  text-align: center;
  padding: 2rem;
}

.loading-state {
  text-align: center;
  padding: 3rem;
  color: #6b7280;
}
</style>
