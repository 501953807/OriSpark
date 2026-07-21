<template>
  <div class="private-traffic-view">
    <LoadingSpinner v-if="store.loading" text="加载中..." />
    <template v-else>
      <h2>私域流量管理</h2>
      <p class="subtitle">付费订阅 · 粉丝社群 · 转化漏斗</p>

      <!-- 付费订阅 -->
      <div class="section">
        <h3>付费订阅入口</h3>
        <div class="sub-grid">
          <div v-for="s in store.subscriptions" :key="s.id" class="sub-card">
            <div class="sub-platform">{{ platformLabel(s.platform) }}</div>
            <div class="sub-stats">
              <span>{{ s.subscriber_count }} 订阅者</span>
              <span>¥{{ s.monthly_revenue.toLocaleString() }}/月</span>
            </div>
            <a :href="s.url" target="_blank" class="sub-link">访问链接 →</a>
          </div>
          <div class="sub-card add-card" @click="showAddSub = true">
            <span class="add-icon">+</span>
            <span>添加订阅链接</span>
          </div>
        </div>
        <div class="total-bar">
          <strong>月总收入：</strong>
          ¥{{ totalMonthly.toLocaleString() }}
        </div>
      </div>

      <!-- 粉丝社群 -->
      <div class="section">
        <h3>粉丝社群</h3>
        <div class="community-list">
          <div v-for="c in store.communities" :key="c.id" class="community-card">
            <div class="comm-header">
              <strong>{{ c.name }}</strong>
              <span class="comm-platform">{{ platformLabel(c.platform) }}</span>
            </div>
            <div class="comm-members">{{ c.member_count }} 成员</div>
            <div v-if="c.tags" class="comm-tags">
              <span v-for="t in c.tags" :key="t" class="tag">{{ t }}</span>
            </div>
            <a v-if="c.invite_url" :href="c.invite_url" target="_blank" class="join-link">加入链接 →</a>
          </div>
        </div>
      </div>

      <!-- 转化漏斗 -->
      <div class="section">
        <h3>公域→私域转化漏斗</h3>
        <div v-if="store.funnel" class="funnel-chart">
          <div class="funnel-step">
            <div class="funnel-bar" :style="{ width: funnelWidth(store.funnel.total_public_views) }">
              {{ store.funnel.total_public_views.toLocaleString() }}
            </div>
            <span class="funnel-label">公域曝光</span>
          </div>
          <div class="funnel-step">
            <div class="funnel-bar" :style="{ width: funnelWidth(store.funnel.total_profile_clicks) }">
              {{ store.funnel.total_profile_clicks.toLocaleString() }}
            </div>
            <span class="funnel-label">主页点击</span>
          </div>
          <div class="funnel-step">
            <div class="funnel-bar" :style="{ width: funnelWidth(store.funnel.total_link_clicks) }">
              {{ store.funnel.total_link_clicks.toLocaleString() }}
            </div>
            <span class="funnel-label">链接点击</span>
          </div>
          <div class="funnel-step">
            <div class="funnel-bar highlight" :style="{ width: funnelWidth(store.funnel.total_converted) }">
              {{ store.funnel.total_converted.toLocaleString() }}
            </div>
            <span class="funnel-label">实际转化</span>
          </div>
        </div>
        <div v-if="store.funnel" class="funnel-rate">
          整体转化率: {{ store.funnel.overall_conversion_rate }}%
        </div>

        <div v-if="store.funnel?.by_platform.length" class="platform-breakdown">
          <table>
            <thead>
              <tr>
                <th>平台</th>
                <th>曝光</th>
                <th>点击率</th>
                <th>链接CTR</th>
                <th>转化率</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in store.funnel.by_platform" :key="p.platform">
                <td>{{ platformLabel(p.platform) }}</td>
                <td>{{ p.views.toLocaleString() }}</td>
                <td>{{ p.profile_ctr }}%</td>
                <td>{{ p.link_ctr }}%</td>
                <td>{{ p.conv_rate }}%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { usePrivateTrafficStore } from '@/stores/usePrivateTrafficStore'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const store = usePrivateTrafficStore()
const showAddSub = ref(false)

const totalMonthly = computed(() =>
  store.subscriptions.reduce((sum, s) => sum + s.monthly_revenue, 0)
)

function funnelWidth(value: number): string {
  const max = Math.max(
    store.funnel?.total_public_views || 1,
    store.funnel?.total_profile_clicks || 1,
    store.funnel?.total_link_clicks || 1,
    store.funnel?.total_converted || 1,
  )
  return `${Math.max((value / max) * 100, 2)}%`
}

function platformLabel(key: string): string {
  const map: Record<string, string> = {
    patreon: 'Patreon', aidian: '爱发电', zsxq: '知识星球',
    discord: 'Discord', wechat: '微信', telegram: 'Telegram', qq: 'QQ',
    xiaohongshu: '小红书', douyin: '抖音', youtube: 'YouTube',
    bilibili: 'B站', weibo: '微博', tiktok: 'TikTok',
  }
  return map[key] || key
}

// Init
store.loadAll()
</script>

<style scoped>
.private-traffic-view {
  max-width: 960px;
  margin: 0 auto;
}
h2 { font-size: 1.4rem; margin-bottom: 4px; }
.subtitle { color: var(--muted); font-size: 0.85rem; margin-bottom: 24px; }

.section { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; margin-bottom: 16px; }
.section h3 { margin: 0 0 16px; font-size: 1rem; }

/* Subscriptions */
.sub-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.sub-card {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
}
.sub-platform { font-weight: 700; font-size: 0.9rem; margin-bottom: 8px; }
.sub-stats { display: flex; justify-content: space-between; font-size: 0.8rem; color: var(--muted); margin-bottom: 8px; }
.sub-link { font-size: 0.8rem; color: var(--accent); text-decoration: none; }
.add-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--muted);
  border-style: dashed;
}
.add-icon { font-size: 2rem; line-height: 1; }
.total-bar { margin-top: 12px; padding: 12px; background: #f0fdf4; border-radius: var(--radius-sm); text-align: center; font-size: 0.95rem; }

/* Communities */
.community-list { display: grid; gap: 8px; }
.community-card {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 12px;
}
.comm-header { display: flex; justify-content: space-between; align-items: center; }
.comm-header strong { font-size: 0.9rem; }
.comm-platform { font-size: 0.75rem; color: var(--muted); }
.comm-members { font-size: 0.8rem; color: var(--muted); margin-top: 4px; }
.comm-tags { display: flex; gap: 4px; margin-top: 6px; flex-wrap: wrap; }
.tag { font-size: 0.7rem; padding: 2px 8px; background: var(--bg); border-radius: 10px; }
.join-link { font-size: 0.8rem; color: var(--accent); text-decoration: none; margin-top: 4px; display: inline-block; }

/* Funnel */
.funnel-chart { display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px; }
.funnel-step { display: flex; align-items: center; gap: 12px; }
.funnel-label { width: 80px; font-size: 0.8rem; text-align: right; color: var(--muted); flex-shrink: 0; }
.funnel-bar {
  height: 32px;
  background: var(--accent);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  padding: 0 12px;
  color: white;
  font-size: 0.8rem;
  font-weight: 600;
  min-width: 60px;
  transition: width 0.3s;
}
.funnel-bar.highlight { background: #22c55e; }
.funnel-rate { text-align: center; font-size: 1.1rem; font-weight: 700; color: #22c55e; }

.platform-breakdown { margin-top: 16px; }
.platform-breakdown table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.platform-breakdown th, .platform-breakdown td { padding: 8px 12px; border-bottom: 1px solid var(--border); text-align: left; }
.platform-breakdown th { color: var(--muted); font-weight: 600; }
</style>
