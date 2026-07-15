<template>
  <div class="integrations-view">
    <!-- Category tabs -->
    <div class="cat-tabs">
      <button v-for="cat in categories" :key="cat.key" :class="['cat-tab', { active: activeCat === cat.key }]" @click="activeCat = cat.key">
        {{ cat.label }}
      </button>
    </div>

    <!-- Integration cards -->
    <div class="integrations-grid">
      <div v-for="item in filteredIntegrations" :key="item.key" class="integration-card card">
        <div class="ic-top">
          <div class="ic-logo" :class="item.category">{{ item.icon }}</div>
          <div class="ic-info">
            <div class="ic-name">{{ item.name }}</div>
            <div class="ic-cat">{{ item.categoryLabel }}</div>
          </div>
        </div>
        <div class="ic-desc">{{ item.description }}</div>
        <div class="ic-meta">
          <span class="ic-tag" :class="item.pricing === 'free' ? 'free' : 'paid'">{{ item.pricing === 'free' ? '免费' : '付费' }}</span>
          <span class="ic-tag" :class="item.connected ? 'active' : 'inactive'">{{ item.connected ? '已连接' : '未连接' }}</span>
        </div>
        <div class="ic-actions">
          <button v-if="item.connected" class="btn btn-secondary btn-sm" style="width:100%">断开</button>
          <button v-else class="btn btn-primary btn-sm" style="width:100%" @click="connectItem(item)">连接</button>
        </div>
      </div>
    </div>

    <!-- Platform Config Section -->
    <div class="platform-config-section card">
      <h3 style="margin:0 0 16px;font-size:1rem">🖨️ 外部平台配置</h3>
      <p style="color:var(--muted);font-size:0.85rem;margin:0 0 16px">配置 POD 平台 API Key 以启用自动上架和预览功能</p>
      <div class="platform-config-grid">
        <div v-for="pc in platformConfigs" :key="pc.key" class="platform-config-card">
          <div class="pc-header">
            <span class="pc-icon">{{ pc.icon }}</span>
            <div>
              <div class="pc-name">{{ pc.name }}</div>
              <div class="pc-status" :class="pc.connected ? 'connected' : 'disconnected'">
                {{ pc.connected ? '已配置' : '未配置' }}
              </div>
            </div>
          </div>
          <div class="pc-desc">{{ pc.description }}</div>
          <div class="pc-input-row">
            <input
              v-model="pc.apiKey"
              type="password"
              :placeholder="pc.connected ? '••••••••' : '输入 API Key'"
              class="form-input pc-key-input"
              :disabled="!pc.connected"
            />
          </div>
          <div class="pc-actions">
            <button class="btn btn-sm" :class="pc.connected ? 'btn-secondary' : 'btn-primary'" @click="savePlatformConfig(pc)">
              {{ pc.connected ? '更新' : '保存' }}
            </button>
            <button class="btn btn-sm btn-secondary" @click="testPlatformConnection(pc)">测试连接</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import client from '@/api/client'

const activeCat = ref('all')

const categories = [
  { key: 'all', label: '全部' },
  { key: 'notary', label: '存证平台' },
  { key: 'monitor', label: '侵权监测' },
  { key: 'publish', label: '电商发布' },
  { key: 'ai', label: 'AI 模型' },
]

const integrations = [
  {
    key: 'banquanjia', name: '版权家', icon: '🏛️', category: 'notary', categoryLabel: '存证平台',
    description: '国家版权局 DCI 体系，法律效力最高的数字版权登记平台', pricing: 'paid', connected: false,
  },
  {
    key: 'antchain', name: '蚂蚁链', icon: '🐜', category: 'notary', categoryLabel: '存证平台',
    description: '支付宝蚂蚁区块链存证服务，商用级区块链存证', pricing: 'paid', connected: false,
  },
  {
    key: 'zhixinchain', name: '至信链', icon: '⚖️', category: 'notary', categoryLabel: '存证平台',
    description: '腾讯/互联网法院司法链，司法级证据效力', pricing: 'paid', connected: false,
  },
  {
    key: 'baidu', name: '百度识图', icon: '🔍', category: 'monitor', categoryLabel: '侵权监测',
    description: '百度以图搜图 API，每日 100 次免费查询', pricing: 'free', connected: false,
  },
  {
    key: 'google', name: 'Google Vision', icon: '🤖', category: 'monitor', categoryLabel: '侵权监测',
    description: 'Google Cloud Vision API，每月 1000 次免费', pricing: 'free', connected: false,
  },
  {
    key: 'taobao', name: '淘宝', icon: '🛒', category: 'publish', categoryLabel: '电商发布',
    description: '淘宝/天猫店铺商品发布', pricing: 'free', connected: false,
  },
  {
    key: 'xiaohongshu', name: '小红书', icon: '📕', category: 'publish', categoryLabel: '电商发布',
    description: '小红书笔记/商品发布 (Playwright 自动化)', pricing: 'free', connected: false,
  },
  {
    key: 'ollama', name: 'Ollama', icon: '🧠', category: 'ai', categoryLabel: 'AI 模型',
    description: '本地 LLM 运行环境，用于生成商品描述', pricing: 'free', connected: false,
  },
]

// ─── Platform Config (POD) ───
const platformConfigs = [
  { key: 'printful', name: 'Printful', icon: '📦', apiKey: '', connected: false, description: '全球最大 POD 平台之一' },
  { key: 'redbubble', name: 'Redbubble', icon: '🎨', apiKey: '', connected: false, description: '澳大利亚 POD 平台' },
  { key: 'spring', name: 'Spring', icon: '📘', apiKey: '', connected: false, description: 'Spring POD 平台' },
  { key: 'gelato', name: 'Gelato', icon: '🌍', apiKey: '', connected: false, description: '覆盖 50+ 国家的 POD 平台' },
  { key: 'society6', name: 'Society6', icon: '🖼️', apiKey: '', connected: false, description: '艺术家社区 POD 平台' },
  { key: 'zazzle', name: 'Zazzle', icon: '✂️', apiKey: '', connected: false, description: '可定制产品 POD 平台' },
]

async function loadPlatformConfig() {
  try {
    const res = await client.get('/system/platform-config')
    const data = res.data.data || {}
    platformConfigs.forEach(pc => {
      pc.connected = !!data[pc.key + '_api_key']
    })
  } catch {
    // Silently keep defaults
  }
}

async function savePlatformConfig(pc: any) {
  try {
    await client.patch('/system/platform-config', {
      [pc.key + '_api_key']: pc.apiKey || null,
    })
    pc.connected = !!pc.apiKey
    ;(window as any).$toast?.show(`${pc.name} 配置已保存`, 'success')
  } catch {
    ;(window as any).$toast?.show('保存失败', 'error')
  }
}

async function testPlatformConnection(pc: any) {
  try {
    ;(window as any).$toast?.show(`正在测试连接 ${pc.name}...`, 'info')
    await client.get(`/supply/pod/test/${pc.key}`)
    ;(window as any).$toast?.show(`${pc.name} 连接成功`, 'success')
  } catch {
    ;(window as any).$toast?.show(`${pc.name} 连接失败`, 'error')
  }
}

onMounted(() => {
  loadPlatformConfig()
})

const filteredIntegrations = computed(() => {
  if (activeCat.value === 'all') return integrations
  return integrations.filter(i => i.category === activeCat.value)
})

function connectItem(item: any) {
  const supported: Record<string, string> = {
    baidu: '百度识图已在侵权监测模块中使用，无需额外配置',
    google: 'Google Vision 已在侵权监测模块中使用，无需额外配置',
    ollama: '请在偏好设置 → AI 模型中配置 Ollama 地址',
  }
  if (supported[item.key]) {
    ;(window as any).$toast?.show(supported[item.key], 'info')
    return
  }
  ;(window as any).$toast?.show(`${item.name} 连接功能规划中，敬请期待`, 'info')
}
</script>

<style scoped>
.integrations-view { display: flex; flex-direction: column; gap: 24px; }
.cat-tabs { display: flex; gap: 8px; flex-wrap: wrap; }
.cat-tab {
  padding: 8px 18px; border-radius: 100px; font-size: 0.84rem; font-weight: 600;
  cursor: pointer; border: 1px solid var(--border); background: var(--surface);
  transition: all 0.2s; font-family: var(--font-body); color: var(--muted);
}
.cat-tab.active { background: var(--accent); color: #fff; border-color: var(--accent); }
.cat-tab:hover:not(.active) { border-color: var(--accent); color: var(--accent); }
.integrations-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 20px; }
.integration-card { padding: 24px; display: flex; flex-direction: column; gap: 14px; }
.ic-top { display: flex; align-items: flex-start; gap: 14px; }
.ic-logo {
  width: 52px; height: 52px; border-radius: var(--radius);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.6rem; flex-shrink: 0;
}
.ic-logo.notary { background: oklch(56% 0.12 170 / 0.12); }
.ic-logo.monitor { background: oklch(62% 0.18 55 / 0.12); }
.ic-logo.publish { background: oklch(58% 0.16 280 / 0.12); }
.ic-logo.ai { background: oklch(58% 0.14 245 / 0.12); }
.ic-info { flex: 1; min-width: 0; }
.ic-name { font-family: var(--font-display); font-size: 1.05rem; font-weight: 700; }
.ic-cat { font-size: 0.72rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; }
.ic-desc { font-size: 0.85rem; color: var(--muted); line-height: 1.6; }
.ic-meta { display: flex; flex-wrap: wrap; gap: 8px; font-size: 0.75rem; }
.ic-tag { padding: 3px 10px; border-radius: 100px; font-weight: 600; }
.ic-tag.active { background: oklch(56% 0.12 170 / 0.1); color: var(--accent); }
.ic-tag.inactive { background: oklch(0 0 0 / 0.04); color: var(--muted); }
.ic-tag.free { background: oklch(56% 0.12 170 / 0.08); color: var(--green); }
.ic-tag.paid { background: oklch(62% 0.18 55 / 0.1); color: var(--orange); }
.ic-actions { display: flex; gap: 10px; margin-top: auto; }
.btn-sm { padding: 6px 14px; font-size: 0.8rem; }

/* Platform Config */
.platform-config-section { padding: 24px; }
.platform-config-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
.platform-config-card { padding: 16px; border: 1px solid var(--border); border-radius: var(--radius-md); background: var(--surface); }
.pc-header { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.pc-icon { font-size: 1.5rem; }
.pc-name { font-weight: 700; font-size: 0.9rem; }
.pc-status { font-size: 0.72rem; font-weight: 600; }
.pc-status.connected { color: var(--accent); }
.pc-status.disconnected { color: var(--muted); }
.pc-desc { font-size: 0.78rem; color: var(--muted); margin-bottom: 10px; }
.pc-input-row { margin-bottom: 10px; }
.pc-key-input { width: 100%; padding: 6px 10px; border: 1px solid var(--border); border-radius: var(--radius-sm); font-size: 0.82rem; background: var(--bg); }
.pc-actions { display: flex; gap: 6px; }
</style>
