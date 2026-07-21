<script setup lang="ts">
import { ref, computed } from 'vue'
import { aiSessionV2Api, achievementApi, invoiceApi } from '@/api/module9'

const activeTab = ref('sessions')
const sessions = ref<any[]>([])
const loading = ref(false)

async function loadSessions() {
  loading.value = true
  try {
    // placeholder: would fetch from /works/:id/ai-sessions
  } catch { /* handled */ } finally { loading.value = false }
}

loadSessions()

const badges = ref<any[]>([])
const achievements = ref<any[]>([])

async function loadBadges() {
  try {
    const res = await achievementApi.listBadges()
    badges.value = res.data || []
  } catch { /* handled */ }
}

loadBadges()
</script>

<template>
  <div class="ai-growth-view">
    <h2>AI 增长引擎</h2>
    <p class="subtitle">AI 创作会话对比、成就徽章与发票管理</p>

    <div class="tabs">
      <button :class="['tab', { active: activeTab === 'sessions' }]" @click="activeTab = 'sessions'">🤖 会话对比</button>
      <button :class="['tab', { active: activeTab === 'badges' }]" @click="activeTab = 'badges'">🏆 成就徽章</button>
      <button :class="['tab', { active: activeTab === 'invoices' }]" @click="activeTab = 'invoices'">🧾 发票管理</button>
    </div>

    <div v-if="activeTab === 'sessions'" class="section">
      <h3>AI 创作会话对比</h3>
      <p class="hint">选择两个会话进行参数对比，或批量导入外部工具记录。</p>
      <div class="placeholder">功能开发中...</div>
    </div>

    <div v-else-if="activeTab === 'badges'" class="section">
      <h3>成就徽章</h3>
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else class="badge-grid">
        <div v-for="badge in badges" :key="badge.id" class="badge-card">
          <div class="badge-icon" :style="{ background: badge.color_hex || '#667eea' }">🏅</div>
          <h4>{{ badge.badge_name }}</h4>
          <p>{{ badge.badge_description }}</p>
          <span class="xp">+{{ badge.xp_reward }} XP</span>
        </div>
      </div>
    </div>

    <div v-else class="section">
      <h3>发票管理</h3>
      <p class="hint">查看和管理订阅发票及自动续费配置。</p>
      <div class="placeholder">功能开发中...</div>
    </div>
  </div>
</template>

<style scoped>
.ai-growth-view { max-width: 1000px; }
.subtitle { color: var(--muted); margin-bottom: 16px; }
.tabs { display: flex; gap: 4px; border-bottom: 1px solid var(--border); margin-bottom: 20px; overflow-x: auto; }
.tab { padding: 10px 16px; border: none; background: none; cursor: pointer; font-size: 0.9rem; white-space: nowrap; opacity: 0.6; transition: opacity 0.2s; }
.tab:hover { opacity: 0.8; }
.tab.active { opacity: 1; border-bottom: 2px solid var(--primary); }
.section { margin-top: 16px; }
.hint { color: var(--muted); font-size: 0.85rem; margin-bottom: 16px; }
.badge-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.badge-card { padding: 16px; text-align: center; border: 1px solid var(--border); border-radius: 8px; }
.badge-icon { width: 48px; height: 48px; border-radius: 50%; margin: 0 auto 8px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; }
.badge-card h4 { margin: 4px 0; }
.badge-card p { font-size: 0.8rem; color: var(--muted); margin: 4px 0; }
.xp { font-size: 0.85rem; font-weight: 600; color: #059669; }
.placeholder { padding: 40px; text-align: center; color: var(--muted); }
.loading { text-align: center; padding: 40px; color: var(--muted); }
</style>
