<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '~/stores/auth'

const auth = useAuthStore()
const stats = ref({ totalWorks: 0, totalContracts: 0, activeCreators: 0, avgSplit: 0 })
const targetStats = ref({ totalWorks: 0, totalContracts: 0, activeCreators: 0, avgSplit: 0 })
const displayStats = ref({ totalWorks: 0, totalContracts: 0, activeCreators: 0, avgSplit: 0 })
const featuredWorks = ref<any[]>([])
const featuredContracts = ref<any[]>([])
const heroError = ref<string | null>(null)
let rollingTimer: ReturnType<typeof setTimeout> | null = null

function animateNumber(current: number, target: number, duration: number = 800): number {
  if (target === 0) return 0
  const start = performance.now()
  const step = (now: number) => {
    const elapsed = now - start
    const progress = Math.min(elapsed / duration, 1)
    // easeOutExpo
    const eased = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress)
    displayStats.value = {
      totalWorks: Math.round(eased * targetStats.value.totalWorks),
      totalContracts: Math.round(eased * targetStats.value.totalContracts),
      activeCreators: Math.round(eased * targetStats.value.activeCreators),
      avgSplit: Math.round(eased * targetStats.value.avgSplit),
    }
    if (progress < 1) {
      rollingTimer = requestAnimationFrame(step)
    }
  }
  rollingTimer = requestAnimationFrame(step)
  return 0
}

function stopRolling() {
  if (rollingTimer) { cancelAnimationFrame(rollingTimer); rollingTimer = null }
}

onMounted(async () => {
  try {
    const apiBase = useRuntimeConfig().public.apiBase
    const [statsRes, worksRes, contractsRes] = await Promise.allSettled([
      $fetch(`${apiBase}/public/dashboard-stats`),
      $fetch(`${apiBase}/public/works?featured=true&limit=6`),
      $fetch(`${apiBase}/public/contracts?recent=true&limit=5`),
    ])

    if (statsRes.status === 'fulfilled') {
      const raw = {
        totalWorks: statsRes.value?.total_works || 0,
        totalContracts: statsRes.value?.total_contracts || 0,
        activeCreators: statsRes.value?.active_creators || 0,
        avgSplit: statsRes.value?.avg_split_rate || 0,
      }
      targetStats.value = raw
      animateNumber(0, raw.totalWorks)
    }
    if (worksRes.status === 'fulfilled' && Array.isArray(worksRes.value)) {
      featuredWorks.value = worksRes.value.slice(0, 6)
    }
    if (contractsRes.status === 'fulfilled' && Array.isArray(contractsRes.value)) {
      featuredContracts.value = contractsRes.value.slice(0, 5)
    }
  } catch (e) {
    heroError.value = e instanceof Error ? e.message : '加载失败'
  }
})

// Redirect to market if already logged in
onMounted(() => {
  if (auth.isLoggedIn) {
    navigateTo('/market')
  }
})

onUnmounted(() => {
  stopRolling()
})
</script>

<template>
  <div class="hero-page">
    <!-- Hero Section -->
    <section class="hero-section">
      <div class="hero-content">
        <h1 class="hero-title">AI 时代的创作者信任枢纽</h1>
        <p class="hero-subtitle">作品存证 · 合约交易 · 运营合作 · 全球分润</p>
        <div class="hero-actions">
          <NuxtLink to="/auth/register" class="btn-primary">
            注册运营者账号
          </NuxtLink>
          <NuxtLink to="/gallery" class="btn-secondary">
            浏览作品画廊
          </NuxtLink>
          <a href="http://localhost:5174" target="_blank" class="btn-ghost">
            创作者入口 →
          </a>
        </div>
      </div>
      <div class="hero-visual">
        <div class="hero-stats">
          <div class="stat-card">
            <div class="stat-value">{{ displayStats.totalWorks }}</div>
            <div class="stat-label">作品总数</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ displayStats.totalContracts }}</div>
            <div class="stat-label">活跃合约</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ displayStats.activeCreators }}</div>
            <div class="stat-label">创作者</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ displayStats.avgSplit }}%</div>
            <div class="stat-label">平均分润</div>
          </div>
        </div>
      </div>
    </section>

    <!-- Featured Works -->
    <section class="section">
      <div class="section-header">
        <h2>精选作品</h2>
        <NuxtLink to="/gallery" class="view-all">查看全部 →</NuxtLink>
      </div>
      <div class="works-grid">
        <div v-for="work in featuredWorks" :key="work.id" class="work-card">
          <div class="work-thumb" :style="{ backgroundImage: `url(${work.thumbnail || work.thumbnail_path || ''})` }"></div>
          <div class="work-info">
            <h3>{{ work.title }}</h3>
            <p class="work-creator">{{ work.creator_name || '匿名创作者' }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Recent Contracts -->
    <section class="section">
      <div class="section-header">
        <h2>最新合约</h2>
        <NuxtLink to="/contracts" class="view-all">查看全部 →</NuxtLink>
      </div>
      <div class="contracts-list">
        <div v-for="contract in featuredContracts" :key="contract.id" class="contract-item">
          <div class="contract-title">{{ contract.title }}</div>
          <div class="contract-meta">
            <span class="contract-type">{{ contract.contract_type || '标准合约' }}</span>
            <span class="contract-amount">¥{{ contract.total_amount?.toLocaleString() || '0' }}</span>
            <span class="contract-status" :class="contract.status">{{ contract.status }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Capabilities -->
    <section class="section">
      <h2>核心能力</h2>
      <div class="capabilities-grid">
        <div class="capability-card">
          <div class="cap-icon">🛡️</div>
          <h3>权益保护</h3>
          <p>C2PA存证 · 区块链锚定 · 全网监测</p>
        </div>
        <div class="capability-card">
          <div class="cap-icon">📝</div>
          <h3>合约交易</h3>
          <p>挂牌认购 · 第三方支付托管 · 市场化分润</p>
        </div>
        <div class="capability-card">
          <div class="cap-icon">🤝</div>
          <h3>运营合作</h3>
          <p>包装授权 · 工厂对接 · 全球分销</p>
        </div>
        <div class="capability-card">
          <div class="cap-icon">📊</div>
          <h3>数据洞察</h3>
          <p>创作者排行 · 品类趋势 · 行业报告</p>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.hero-page {
  min-height: 100vh;
  background: #fff;
}
.hero-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 80px 64px;
  gap: 64px;
  border-bottom: 1px solid #e2e8f0;
}
.hero-content {
  flex: 1;
  max-width: 520px;
}
.hero-title {
  font-size: 42px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.2;
  margin: 0 0 16px;
}
.hero-subtitle {
  font-size: 16px;
  color: #64748b;
  margin: 0 0 32px;
}
.hero-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.btn-primary, .btn-secondary, .btn-ghost {
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.15s;
}
.btn-primary {
  background: #1e293b;
  color: #fff;
}
.btn-primary:hover { background: #334155; }
.btn-secondary {
  background: #f8fafc;
  color: #1e293b;
  border: 1px solid #e2e8f0;
}
.btn-secondary:hover { background: #f1f5f9; }
.btn-ghost {
  background: transparent;
  color: #3b82f6;
  border: 1px solid #3b82f6;
}
.btn-ghost:hover { background: #eff6ff; }
.hero-visual {
  flex: 1;
  max-width: 480px;
}
.hero-stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}
.stat-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
}
.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #1e293b;
}
.stat-label {
  font-size: 13px;
  color: #64748b;
  margin-top: 4px;
}
.section {
  padding: 64px;
  border-bottom: 1px solid #e2e8f0;
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}
.section-header h2 {
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
}
.view-all {
  font-size: 14px;
  color: #3b82f6;
  text-decoration: none;
}
.view-all:hover { text-decoration: underline; }
.works-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}
.work-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
  transition: box-shadow 0.15s;
}
.work-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.work-thumb {
  height: 160px;
  background-size: cover;
  background-position: center;
  background-color: #e2e8f0;
}
.work-info {
  padding: 16px;
}
.work-info h3 {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.work-creator {
  font-size: 13px;
  color: #64748b;
  margin: 0;
}
.contracts-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.contract-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
}
.contract-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
}
.contract-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 13px;
}
.contract-type {
  color: #64748b;
}
.contract-amount {
  font-weight: 600;
  color: #1e293b;
}
.contract-status {
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}
.contract-status.active, .contract-status.listed { background: #dcfce7; color: #16a34a; }
.contract-status.subscribed { background: #fef3c7; color: #d97706; }
.capabilities-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}
.capability-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
}
.cap-icon { font-size: 32px; margin-bottom: 12px; }
.capability-card h3 { font-size: 16px; font-weight: 600; color: #1e293b; margin: 0 0 8px; }
.capability-card p { font-size: 13px; color: #64748b; margin: 0; }

@media (max-width: 768px) {
  .hero-section { flex-direction: column; padding: 40px 24px; }
  .hero-title { font-size: 28px; }
  .works-grid, .capabilities-grid { grid-template-columns: 1fr; }
  .section { padding: 40px 24px; }
}
</style>
