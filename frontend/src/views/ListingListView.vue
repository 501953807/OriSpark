<!-- ListingListView — 商品列表页

Grid/List toggle view of all design listings.
Filters by monetization path, material, platform, status.
Pagination support.
-->
<template>
  <div class="listing-list-view">
    <!-- Header -->
    <div class="view-header">
      <h2>📦 我的商品</h2>
      <div class="header-actions">
        <button class="btn-create" @click="goToWizard">+ 新建商品</button>
        <div class="view-toggle">
          <button :class="['toggle-btn', { active: viewMode === 'grid' }]" @click="viewMode = 'grid'">⊞</button>
          <button :class="['toggle-btn', { active: viewMode === 'list' }]" @click="viewMode = 'list'">☰</button>
        </div>
      </div>
    </div>

    <!-- Filters -->
    <div class="filters-bar">
      <div class="filter-group">
        <label>变现路径</label>
        <select v-model="filters.path" class="filter-select">
          <option value="">全部</option>
          <option v-for="p in paths" :key="p.id" :value="p.id">{{ p.name_zh }}</option>
        </select>
      </div>
      <div class="filter-group">
        <label>状态</label>
        <select v-model="filters.status" class="filter-select">
          <option value="">全部</option>
          <option value="draft">草稿</option>
          <option value="active">在售</option>
          <option value="discontinued">已下架</option>
        </select>
      </div>
      <div class="filter-group">
        <label>材质</label>
        <select v-model="filters.material" class="filter-select">
          <option value="">全部</option>
          <option value="textile">纺织</option>
          <option value="paper">纸质</option>
          <option value="hard_goods">硬质</option>
          <option value="plastic_3c">塑料3C</option>
        </select>
      </div>
      <div class="filter-group">
        <label>搜索</label>
        <input v-model="filters.search" placeholder="搜索商品名称..." class="filter-input" />
      </div>
      <button class="btn-reset" @click="resetFilters">重置</button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">加载中...</div>

    <!-- Grid view -->
    <div v-else-if="listings.length && viewMode === 'grid'" class="listing-grid">
      <ListingCard
        v-for="l in listings"
        :key="l.id"
        :listing="l"
        @view="goToDetail"
        @edit="editListing"
        @duplicate="duplicateListing"
        @publish="publishListing"
      />
    </div>

    <!-- List view -->
    <div v-else-if="listings.length && viewMode === 'list'" class="listing-list">
      <div class="list-header">
        <span class="col-title">商品</span>
        <span class="col-price">价格</span>
        <span class="col-path">路径</span>
        <span class="col-status">状态</span>
        <span class="col-actions">操作</span>
      </div>
      <div
        v-for="l in listings"
        :key="l.id"
        class="list-row"
        @click="goToDetail(l.id)"
      >
        <span class="col-title">{{ l.title }}</span>
        <span class="col-price">¥{{ l.price }}</span>
        <span class="col-path">{{ pathLabel(l.monetization_path || '') }}</span>
        <span class="col-status">{{ statusLabel(l.status) }}</span>
        <span class="col-actions">
          <button class="list-action" @click.stop="goToDetail(l.id)">👁</button>
          <button class="list-action" @click.stop="editListing(l.id)">✏️</button>
        </span>
      </div>
    </div>

    <!-- Empty -->
    <div v-else class="empty-state">
      <span class="empty-icon">📦</span>
      <p>还没有商品</p>
      <button class="btn-create" @click="goToWizard">去创建一个</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { supplyApi } from '@/api/supply'
import type { DesignListing } from '@/types/supply'
import ListingCard from '@/components/monetization/ListingCard.vue'

const router = useRouter()

const listings = ref<DesignListing[]>([])
const loading = ref(false)
const viewMode = ref<'grid' | 'list'>('grid')

const paths = [
  { id: 'pod', name_zh: 'POD渠道管理' },
  { id: 'crowdfunding', name_zh: '众筹' },
  { id: 'licensing', name_zh: 'IP授权' },
  { id: 'digital', name_zh: '数字产品' },
  { id: 'custom_mfg', name_zh: '定制制造' },
]

const filters = ref({ path: '', status: '', material: '', search: '' })

function pathLabel(p?: string): string {
  const map: Record<string, string> = {
    pod: 'POD', crowdfunding: '众筹', licensing: 'IP授权',
    digital: '数字产品', custom_mfg: '定制制造',
  }
  return map[p || ''] || '-'
}

function statusLabel(s: string): string {
  const map: Record<string, string> = {
    draft: '草稿', active: '在售', discontinued: '已下架',
  }
  return map[s] || s
}

async function loadListings() {
  loading.value = true
  try {
    const params: Record<string, any> = {}
    if (filters.value.path) params.monetization_path = filters.value.path
    if (filters.value.status) params.status = filters.value.status
    if (filters.value.search) params.search = filters.value.search

    const { data } = await supplyApi.listings(params)
    listings.value = data as DesignListing[]
  } catch {
    listings.value = []
  } finally {
    loading.value = false
  }
}

function goToDetail(id: string) {
  router.push({ name: 'listing-detail', params: { id } })
}

function goToWizard() {
  router.push({ name: 'supply' })
}

function editListing(id: string) {
  router.push({ name: 'listing-detail', params: { id }, hash: '#edit'})
}

function duplicateListing(id: string) {
  // Clone listing with new ID
  const orig = listings.value.find(l => l.id === id)
  if (!orig) return
  alert(`复制商品: ${orig.title} (功能待实现)`)
}

function publishListing(id: string) {
  goToDetail(id)
}

function resetFilters() {
  filters.value = { path: '', status: '', material: '', search: '' }
}

onMounted(loadListings)
</script>

<style scoped>
.listing-list-view { padding: 20px; }

.view-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 16px;
}

.view-header h2 { margin: 0; font-size: 1.3rem; }

.header-actions { display: flex; gap: 12px; align-items: center; }

.btn-create {
  background: var(--accent); color: #fff; border: none;
  padding: 8px 18px; border-radius: var(--radius-sm);
  font-size: .88rem; font-weight: 600; cursor: pointer;
}

.view-toggle { display: flex; gap: 2px; }
.toggle-btn {
  background: none; border: 1px solid var(--border); border-radius: var(--radius-sm);
  padding: 4px 8px; cursor: pointer; font-size: 1rem;
}
.toggle-btn.active { border-color: var(--accent); background: oklch(56% 0.12 170 / .08); }

/* Filters */
.filters-bar {
  display: flex; gap: 12px; align-items: flex-end;
  padding: 12px 16px; border: 1px solid var(--border);
  border-radius: var(--radius-sm); background: var(--surface);
  margin-bottom: 16px; flex-wrap: wrap;
}

.filter-group { display: flex; flex-direction: column; gap: 4px; }
.filter-group label { font-size: .68rem; color: var(--muted); font-weight: 600; }

.filter-select, .filter-input {
  padding: 4px 8px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  font-size: .82rem; background: var(--bg); min-width: 120px;
}

.btn-reset {
  padding: 4px 12px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  background: none; cursor: pointer; font-size: .78rem;
}

/* Grid */
.listing-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}

/* List */
.listing-list { display: flex; flex-direction: column; gap: 0; }

.list-header {
  display: grid;
  grid-template-columns: 2fr 80px 80px 80px 100px;
  gap: 12px; padding: 8px 16px;
  border-bottom: 2px solid var(--border);
  font-size: .72rem; font-weight: 700; color: var(--muted);
}

.list-row {
  display: grid;
  grid-template-columns: 2fr 80px 80px 80px 100px;
  gap: 12px; padding: 10px 16px;
  border-bottom: 1px solid var(--border);
  font-size: .82rem; cursor: pointer; align-items: center;
}

.list-row:hover { background: oklch(56% 0.12 170 / .03); }

.col-actions { display: flex; gap: 4px; }
.list-action {
  background: none; border: 1px solid var(--border); border-radius: var(--radius-sm);
  padding: 2px 6px; cursor: pointer; font-size: .78rem;
}

/* States */
.loading-state, .empty-state {
  text-align: center; padding: 64px 0; color: var(--muted);
}
.empty-icon { font-size: 3rem; display: block; margin-bottom: 12px; }
</style>
