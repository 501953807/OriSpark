<template>
  <div class="illustrator-view">
    <!-- Stats bar -->
    <div class="stats-bar">
      <div class="stat-item">
        <span class="stat-label">🎨 总作品</span>
        <span class="stat-value">{{ workStore.total }}</span>
      </div>
      <div class="stat-item stat-verified">
        <span class="stat-label">🔒 已存证</span>
        <span class="stat-value">{{ verifiedCount }}</span>
      </div>
      <div class="stat-item stat-pending">
        <span class="stat-label">📋 待存证</span>
        <span class="stat-value">{{ pendingCount }}</span>
      </div>
      <div class="stat-item stat-images">
        <span class="stat-label">🌠 图片</span>
        <span class="stat-value">{{ imageCount }}</span>
      </div>
      <div class="stat-item stat-designs">
        <span class="stat-label">🎨 设计</span>
        <span class="stat-value">{{ designCount }}</span>
      </div>
    </div>

    <!-- Tab bar -->
    <div class="tab-bar">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab-btn', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >
        {{ tab.icon }} {{ tab.label }}
      </button>
    </div>

    <!-- ========== 作品概览 tab ========== -->
    <div v-if="activeTab === 'overview'" class="tab-panel">
      <div class="overview-grid">
        <div v-for="work in workStore.works.slice(0, 8)" :key="work.id" class="work-card">
          <div class="work-thumb">
            <img v-if="work.thumbnail_url" :src="work.thumbnail_url" :alt="work.title" />
            <div v-else class="work-thumb-placeholder">{{ fileTypeEmoji[work.file_type] || '📄' }}</div>
          </div>
          <div class="work-info">
            <span class="work-title">{{ work.title }}</span>
            <span class="work-meta">{{ work.imported_at?.slice(0, 10) }}</span>
          </div>
          <router-link :to="`/app/works/${work.id}`" class="work-link">查看详情 &rarr;</router-link>
        </div>
        <div v-if="!workStore.works.length" class="empty-state">
          <span class="empty-icon">🎨</span>
          <p>暂无作品，前往作品管理导入你的第一个插画作品。</p>
          <router-link to="/app/works" class="btn btn-primary">进入作品管理</router-link>
        </div>
      </div>
    </div>

    <!-- ========== AIGC 防护 tab ========== -->
    <div v-if="activeTab === 'aigc'" class="tab-panel">
      <div class="panel-content">
        <h3 class="section-title">🛡 AIGC 防护中心</h3>
        <p class="section-desc">检测作品是否被 AI 模型训练使用，保护原创插画风格。</p>
        <div class="info-cards">
          <div class="info-card">
            <span class="info-icon">🔍</span>
            <h4>风格检测</h4>
            <p>分析插画风格特征，生成风格指纹用于侵权比对</p>
          </div>
          <div class="info-card">
            <span class="info-icon">💳</span>
            <h4>AI 训练监测</h4>
            <p>监控主流 AI 模型是否使用了你的作品进行训练</p>
          </div>
          <div class="info-card">
            <span class="info-icon">🔒</span>
            <h4>风格保护</h4>
            <p>为你的独特插画风格提供数字存证和维权支持</p>
          </div>
        </div>
      </div>
    </div>

    <!-- ========== 风格分析 tab ========== -->
    <div v-if="activeTab === 'style'" class="tab-panel">
      <div class="panel-content">
        <h3 class="section-title">🎨 风格分析</h3>
        <p class="section-desc">自动分析作品的艺术风格、色彩倾向和构图特征。</p>
        <div class="analysis-placeholder">
          <span class="placeholder-icon">📈</span>
          <p>选择作品进行风格分析</p>
          <router-link to="/app/works" class="btn btn-secondary">浏览作品</router-link>
        </div>
      </div>
    </div>

    <!-- ========== 版权登记 tab ========== -->
    <div v-if="activeTab === 'copyright'" class="tab-panel">
      <div class="panel-content">
        <h3 class="section-title">📝 版权登记</h3>
        <p class="section-desc">快速完成作品著作权登记申请。</p>
        <div class="info-cards">
          <div class="info-card">
            <span class="info-icon">📋</span>
            <h4>在线申请</h4>
            <p>填写作品信息，自动生成申请材料</p>
          </div>
          <div class="info-card">
            <span class="info-icon">📈</span>
            <h4>进度查询</h4>
            <p>实时跟踪登记申请审批进度</p>
          </div>
          <div class="info-card">
            <span class="info-icon">📝</span>
            <h4>证书管理</h4>
            <p>电子证书归档与下载</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useWorkStore } from '@/stores/useWorkStore'

const workStore = useWorkStore()

const tabs = [
  { key: 'overview', label: '作品概览', icon: '📋' },
  { key: 'aigc', label: 'AIGC 防护', icon: '🛡' },
  { key: 'style', label: '风格分析', icon: '🎨' },
  { key: 'copyright', label: '版权登记', icon: '📝' },
]
const activeTab = ref<string>('overview')

const fileTypeEmoji: Record<string, string> = {
  image: '🌠',
  design: '🎨',
  document: '📄',
}

const verifiedCount = computed(() =>
  workStore.works.filter(w => w.is_verified).length
)
const pendingCount = computed(() =>
  workStore.works.filter(w => !w.is_verified).length
)
const imageCount = computed(() =>
  workStore.works.filter(w => w.file_type === 'image').length
)
const designCount = computed(() =>
  workStore.works.filter(w => w.file_type === 'design').length
)

onMounted(() => {
  if (!workStore.works.length) {
    workStore.fetchWorks().catch(() => {})
  }
})
</script>

<style scoped>
.illustrator-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ── Stats bar ─────────────────────────────────────────────── */
.stats-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  background: var(--m-surface);
  border: 1px solid var(--m-border);
  border-radius: var(--m-radius-sm);
  padding: 16px;
}

.stat-item {
  display: flex;
  align-items: baseline;
  gap: 6px;
  padding: 8px 14px;
  background: var(--m-bg-subtle);
  border-radius: var(--m-radius-sm);
  flex: 1;
  min-width: 140px;
}

.stat-label {
  font-size: 0.82rem;
  color: var(--m-grey-500);
  white-space: nowrap;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--m-on-surface);
  font-family: Inter;
}

.stat-verified .stat-value { color: #16a34a; }
.stat-pending .stat-value { color: #ea580c; }
.stat-images .stat-value { color: #8b5cf6; }
.stat-designs .stat-value { color: #6366f1; }

/* ── Tab bar ───────────────────────────────────────────────── */
.tab-bar {
  display: flex;
  gap: 4px;
  background: var(--m-surface);
  border: 1px solid var(--m-border);
  border-radius: var(--m-radius-sm);
  padding: 6px;
}

.tab-btn {
  flex: 1;
  padding: 10px 16px;
  border: none;
  border-radius: calc(var(--m-radius-sm) - 6px);
  background: transparent;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--m-grey-500);
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
  font-family: inherit;
}

.tab-btn:hover {
  color: var(--m-on-surface);
  background: var(--m-bg-subtle);
}

.tab-btn.active {
  background: var(--m-primary);
  color: #fff;
}

.tab-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ── Overview grid ─────────────────────────────────────────── */
.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.work-card {
  background: var(--m-surface);
  border: 1px solid var(--m-border);
  border-radius: var(--m-radius-sm);
  overflow: hidden;
  transition: box-shadow 0.2s;
}

.work-card:hover {
  box-shadow: 0 4px 16px oklch(0 0 0 / 0.08);
}

.work-thumb {
  height: 140px;
  overflow: hidden;
  background: var(--m-bg-subtle);
}

.work-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.work-thumb-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.5rem;
  opacity: 0.5;
  background: var(--m-bg-subtle);
}

.work-info {
  padding: 12px 14px;
}

.work-title {
  display: block;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--m-on-surface);
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.work-meta {
  font-size: 0.78rem;
  color: var(--m-grey-500);
}

.work-link {
  display: block;
  padding: 8px 14px;
  border-top: 1px solid var(--m-border);
  font-size: 0.82rem;
  color: var(--m-primary);
  text-align: center;
  text-decoration: none;
}

.work-link:hover {
  background: var(--m-bg-subtle);
}

/* ── Panel content ─────────────────────────────────────────── */
.panel-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--m-on-surface);
  margin: 0;
}

.section-desc {
  font-size: 0.88rem;
  color: var(--m-grey-500);
  margin: 0;
}

.info-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.info-card {
  background: var(--m-surface);
  border: 1px solid var(--m-border);
  border-radius: var(--m-radius-sm);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.info-icon {
  font-size: 2rem;
}

.info-card h4 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--m-on-surface);
}

.info-card p {
  margin: 0;
  font-size: 0.84rem;
  color: var(--m-grey-500);
  line-height: 1.5;
}

.analysis-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 60px 20px;
  color: var(--m-grey-500);
}

.placeholder-icon {
  font-size: 3rem;
  opacity: 0.5;
}

.empty-state {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 48px;
  color: var(--m-grey-500);
  text-align: center;
}

.empty-icon {
  font-size: 3rem;
  opacity: 0.5;
}

/* ── Buttons ───────────────────────────────────────────────── */
.btn {
  padding: 8px 16px;
  border-radius: var(--m-radius-sm);
  font-size: 0.84rem;
  cursor: pointer;
  border: 1px solid var(--m-border);
  background: var(--m-surface);
  color: var(--m-on-surface);
  font-family: inherit;
  text-decoration: none;
  transition: background 0.2s;
  display: inline-block;
}

.btn:hover { background: var(--m-bg-subtle); }

.btn-primary {
  background: var(--m-primary);
  color: #fff;
  border-color: var(--m-primary);
}

.btn-primary:hover {
  opacity: 0.9;
}

.btn-secondary {
  background: var(--m-bg-subtle);
}
</style>
