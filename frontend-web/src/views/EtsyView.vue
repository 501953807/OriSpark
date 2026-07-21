<template>
  <div class="etsy-view">
    <!-- Error banner -->
    <div v-if="store.errorMsg" class="error-banner">
      <span>{{ store.errorMsg }}</span>
      <button @click="store.clearError()">&times;</button>
    </div>

    <!-- Stats bar -->
    <div class="stats-bar">
      <div class="stat-item">
        <span class="stat-label">🏪 已连接店铺</span>
        <span class="stat-value">{{ store.shops.length }}</span>
      </div>
      <div class="stat-item stat-active">
        <span class="stat-label">📋 在售商品</span>
        <span class="stat-value">{{ store.listings.length }}</span>
      </div>
      <div class="stat-item stat-orders">
        <span class="stat-label">📦 订单数</span>
        <span class="stat-value">{{ store.orders.length }}</span>
      </div>
      <div class="stat-item stat-revenue">
        <span class="stat-label">💰 总营收</span>
        <span class="stat-value">${{ totalRevenue }}</span>
      </div>
    </div>

    <!-- Tab bar -->
    <div class="tab-bar">
      <button :class="['tab-btn', { active: activeTab === 'shops' }]" @click="activeTab = 'shops'">🏪 店铺管理</button>
      <button :class="['tab-btn', { active: activeTab === 'listings' }]" @click="activeTab = 'listings'">📋 商品列表</button>
      <button :class="['tab-btn', { active: activeTab === 'orders' }]" @click="activeTab = 'orders'">📦 订单管理</button>
    </div>

    <!-- Shops tab -->
    <div v-if="activeTab === 'shops'" class="tab-panel">
      <div class="panel-header">
        <h2 class="section-title">Etsy 店铺连接</h2>
        <button class="btn btn-primary btn-sm" @click="showConnectForm = !showConnectForm">
          {{ showConnectForm ? '取消' : '+ 连接新店铺' }}
        </button>
      </div>

      <div v-if="showConnectForm" class="form-card">
        <h3 class="form-title">连接 Etsy 店铺</h3>
        <div class="form-grid">
          <input v-model="connectForm.authorization_code" class="form-input" placeholder="授权码 (Authorization Code)" />
          <input v-model="connectForm.shop_id" class="form-input" placeholder="店铺 ID（可选）" />
          <input v-model="connectForm.shop_name" class="form-input" placeholder="店铺名称（可选）" />
        </div>
        <div class="form-actions">
          <button :disabled="connecting" class="btn btn-primary" @click="handleConnectShop">
            {{ connecting ? '连接中...' : '连接' }}
          </button>
          <button class="btn btn-outline" @click="showConnectForm = false">取消</button>
        </div>
      </div>

      <div v-if="store.shops.length === 0 && !store.loading" class="empty-state">
        <span class="empty-icon">🏪</span>
        <p>暂无连接的 Etsy 店铺。</p>
      </div>
      <div v-else class="shop-list">
        <div v-for="shop in store.shops" :key="shop.id" class="shop-card">
          <div class="shop-info">
            <span class="shop-name">{{ shop.shop_name }}</span>
            <span v-if="shop.shop_id" class="shop-id">ID: {{ shop.shop_id }}</span>
            <span :class="['badge', shop.is_active ? 'badge-active' : 'badge-inactive']">
              {{ shop.is_active ? '已连接' : '已断开' }}
            </span>
          </div>
          <div v-if="shop.created_at" class="shop-meta">连接时间: {{ formatDate(shop.created_at) }}</div>
          <div class="shop-actions">
            <button class="btn btn-sm btn-danger" @click="handleDisconnectShop(shop.id)">断开连接</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Listings tab -->
    <div v-if="activeTab === 'listings'" class="tab-panel">
      <div class="panel-header">
        <h2 class="section-title">Etsy 商品列表</h2>
        <button class="btn btn-primary btn-sm" @click="showListingForm = !showListingForm">
          {{ showListingForm ? '取消' : '+ 新建商品' }}
        </button>
      </div>

      <div v-if="showListingForm" class="form-card">
        <h3 class="form-title">新建 Etsy 商品</h3>
        <div class="form-grid">
          <input v-model="listingForm.title" class="form-input" placeholder="商品标题" />
          <textarea v-model="listingForm.description" class="form-input form-textarea" placeholder="描述" rows="2" />
          <input v-model.number="listingForm.price" type="number" step="0.01" class="form-input" placeholder="价格 ($)" />
          <input v-model.number="listingForm.quantity" type="number" class="form-input" placeholder="数量" />
          <select v-model="listingForm.currency" class="form-input">
            <option value="USD">USD</option>
            <option value="CNY">CNY</option>
            <option value="EUR">EUR</option>
          </select>
          <select v-model="listingForm.status" class="form-input">
            <option value="active">上架</option>
            <option value="draft">草稿</option>
            <option value="inactive">下架</option>
          </select>
        </div>
        <div class="form-actions">
          <button :disabled="creatingListing" class="btn btn-primary" @click="handleCreateListing">
            {{ creatingListing ? '创建中...' : '创建' }}
          </button>
          <button class="btn btn-outline" @click="showListingForm = false">取消</button>
        </div>
      </div>

      <div v-if="store.listings.length === 0 && !store.loading" class="empty-state">
        <span class="empty-icon">📋</span>
        <p>暂无 Etsy 商品。</p>
      </div>
      <div v-else class="product-grid">
        <div v-for="l in store.listings" :key="l.id" class="product-card">
          <div class="product-card-top">
            <span class="product-title">{{ l.title }}</span>
            <span :class="['badge', listingStatusBadge(l.status)]">{{ l.status }}</span>
          </div>
          <div v-if="l.description" class="rfq-desc">{{ l.description }}</div>
          <div class="product-meta">
            <span class="meta-item">💰 ${{ l.price }} {{ l.currency }}</span>
            <span class="meta-item">📦 库存: {{ l.quantity }}</span>
            <span v-if="l.views_count != null" class="meta-item">👁️ {{ l.views_count }}</span>
            <span v-if="l.favorites_count != null" class="meta-item">❤️ {{ l.favorites_count }}</span>
            <span v-if="l.sales_count != null" class="meta-item">🛒 {{ l.sales_count }}</span>
          </div>
          <div class="product-actions">
            <button class="btn btn-sm btn-danger" @click="handleDeleteListing(l.id)">删除</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Orders tab -->
    <div v-if="activeTab === 'orders'" class="tab-panel">
      <div class="panel-header">
        <h2 class="section-title">Etsy 订单</h2>
      </div>
      <div v-if="store.orders.length === 0 && !store.loading" class="empty-state">
        <span class="empty-icon">📦</span>
        <p>暂无 Etsy 订单。</p>
      </div>
      <div v-else class="order-list">
        <div v-for="o in store.orders" :key="o.id" class="order-card">
          <div class="order-header">
            <span class="order-id">#{{ o.etsy_order_id || o.id.slice(0, 8) }}</span>
            <span :class="['badge', orderStatusBadge(o.status)]">{{ o.status }}</span>
          </div>
          <div class="rfq-meta">
            <span class="meta-item">👤 {{ o.buyer_name }}</span>
            <span class="meta-item">💰 ${{ o.order_total }}</span>
            <span v-if="o.shipping_cost" class="meta-item">🚚 ${{ o.shipping_cost }}</span>
            <span v-if="o.tax" class="meta-item">🧾 税: ${{ o.tax }}</span>
            <span v-if="o.tracking_number" class="meta-item">📍 物流: {{ o.tracking_number }}</span>
          </div>
          <div v-if="o.order_date" class="product-meta">
            <span class="meta-item">📅 {{ formatDate(o.order_date) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading overlay -->
    <div v-if="store.loading" class="loading-overlay">
      <div class="spinner">⌛ 加载中...</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useEtsyStore } from '@/stores/useEtsyStore'

const store = useEtsyStore()
const activeTab = ref<string>('shops')
const showConnectForm = ref(false)
const showListingForm = ref(false)
const connecting = ref(false)
const creatingListing = ref(false)

// ── Connect form ──────────────────────────────────────────────
const connectForm = ref({
  authorization_code: '',
  shop_id: '',
  shop_name: '',
})

async function handleConnectShop() {
  if (!connectForm.value.authorization_code.trim()) {
    ;(window as any).$toast?.show('请填写授权码', 'error')
    return
  }
  connecting.value = true
  try {
    await store.connectShop({
      authorization_code: connectForm.value.authorization_code,
      shop_id: connectForm.value.shop_id || null,
      shop_name: connectForm.value.shop_name || null,
    })
    ;(window as any).$toast?.show('店铺连接成功', 'success')
    connectForm.value = { authorization_code: '', shop_id: '', shop_name: '' }
    showConnectForm.value = false
    await store.fetchShops()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '连接失败'
    ;(window as any).$toast?.show(msg, 'error')
  } finally {
    connecting.value = false
  }
}

async function handleDisconnectShop(shopId: string) {
  if (!confirm('确定断开此店铺连接？')) return
  try {
    await store.disconnectShop(shopId)
    ;(window as any).$toast?.show('店铺已断开', 'info')
    await store.fetchShops()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '断开失败'
    ;(window as any).$toast?.show(msg, 'error')
  }
}

// ── Listing form ──────────────────────────────────────────────
const listingForm = ref({
  title: '', description: '', price: 0, quantity: 1, currency: 'USD', status: 'active',
})

async function handleCreateListing() {
  if (!listingForm.value.title.trim()) {
    ;(window as any).$toast?.show('请填写商品标题', 'error')
    return
  }
  creatingListing.value = true
  try {
    await store.createListing({
      title: listingForm.value.title,
      description: listingForm.value.description || null,
      price: listingForm.value.price,
      quantity: listingForm.value.quantity,
      currency: listingForm.value.currency,
      status: listingForm.value.status,
    })
    ;(window as any).$toast?.show('商品创建成功', 'success')
    listingForm.value = { title: '', description: '', price: 0, quantity: 1, currency: 'USD', status: 'active' }
    showListingForm.value = false
    await store.fetchListings()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '创建失败'
    ;(window as any).$toast?.show(msg, 'error')
  } finally {
    creatingListing.value = false
  }
}

async function handleDeleteListing(listingId: string) {
  if (!confirm('确定删除此商品？')) return
  try {
    await store.deleteListing(listingId)
    ;(window as any).$toast?.show('商品已删除', 'success')
    await store.fetchListings()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '删除失败'
    ;(window as any).$toast?.show(msg, 'error')
  }
}

// ── Helpers ───────────────────────────────────────────────────
const totalRevenue = computed(() => {
  return store.listings.reduce((sum, l) => sum + (l.revenue ?? 0), 0).toFixed(2)
})

function formatDate(iso: string): string {
  if (!iso) return '-'
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

function listingStatusBadge(status: string): string {
  if (status === 'active') return 'badge-active'
  if (status === 'draft') return 'badge-open'
  return 'badge-inactive'
}

function orderStatusBadge(status: string): string {
  if (status === 'shipped' || status === 'delivered') return 'badge-active'
  if (status === 'cancelled') return 'badge-closed'
  return 'badge-open'
}

// ── Lifecycle ─────────────────────────────────────────────────
onMounted(async () => {
  try {
    await Promise.all([
      store.fetchShops(),
      store.fetchListings(),
      store.fetchOrders(),
    ])
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '加载失败'
    store.setError(msg)
  }
})
</script>

<style scoped>
.etsy-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.loading-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(2px);
  z-index: 100;
  font-size: 0.9rem;
  color: var(--muted);
  font-weight: 500;
}
.spinner { display: flex; align-items: center; gap: 8px; }
.error-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: oklch(65% 0.18 20);
  color: #fff;
  border-radius: var(--radius);
  font-size: 0.88rem;
}
.error-banner button {
  background: none;
  border: none;
  color: #fff;
  cursor: pointer;
  font-size: 1.2rem;
  opacity: 0.8;
}
.stats-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
}
.stat-item {
  display: flex;
  align-items: baseline;
  gap: 6px;
  padding: 8px 14px;
  background: var(--bg);
  border-radius: var(--radius-sm);
  flex: 1;
  min-width: 160px;
}
.stat-label { font-size: 0.82rem; color: var(--muted); white-space: nowrap; }
.stat-value { font-size: 1.25rem; font-weight: 700; color: var(--fg); font-family: var(--font-display); }
.stat-active .stat-value { color: #16a34a; }
.stat-orders .stat-value { color: #ea580c; }
.stat-revenue .stat-value { color: #9333ea; }
.tab-bar {
  display: flex;
  gap: 4px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 6px;
}
.tab-btn {
  flex: 1;
  padding: 10px 16px;
  border: none;
  border-radius: calc(var(--radius) - 6px);
  background: transparent;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--muted);
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
  font-family: inherit;
}
.tab-btn:hover { color: var(--fg); background: var(--bg); }
.tab-btn.active { background: var(--accent); color: #fff; }
.tab-panel { display: flex; flex-direction: column; gap: 16px; }
.panel-header { display: flex; align-items: center; justify-content: space-between; }
.section-title { font-size: 0.92rem; font-weight: 600; color: var(--fg); margin: 0; }
.form-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
}
.form-title { font-size: 0.9rem; font-weight: 600; color: var(--fg); margin: 0 0 16px 0; }
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}
.form-input {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.84rem;
  background: var(--bg);
  color: var(--fg);
  font-family: inherit;
}
.form-textarea { resize: vertical; min-height: 60px; }
.form-actions { display: flex; gap: 8px; }
.btn {
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  font-size: 0.84rem;
  cursor: pointer;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--fg);
  font-family: inherit;
  transition: background 0.2s;
}
.btn:hover { background: var(--bg); }
.btn-sm { padding: 6px 14px; font-size: 0.82rem; }
.btn-primary { background: var(--accent); color: #fff; border-color: var(--accent); }
.btn-primary:hover { opacity: 0.9; background: var(--accent); }
.btn-outline { background: transparent; border-color: var(--muted); }
.btn-danger { background: #ef4444; color: #fff; border-color: #ef4444; }
.btn-danger:hover { opacity: 0.9; }
.badge {
  display: inline-block;
  font-size: 0.72rem;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
}
.badge-active { background: #dcfce7; color: #166534; }
.badge-inactive { background: #f1f5f9; color: #475569; }
.badge-open { background: #dbeafe; color: #1d4ed8; }
.badge-closed { background: #f1f5f9; color: #475569; }
.product-card-top { display: flex; align-items: center; gap: 8px; }
.product-title {
  flex: 1;
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--fg);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.product-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 12px; }
.product-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 14px;
  transition: box-shadow 0.2s;
}
.product-card:hover { box-shadow: 0 4px 16px oklch(0 0 0 / 0.08); }
.product-meta, .rfq-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 4px;
  font-size: 0.8rem;
  color: var(--muted);
}
.product-actions { margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--border); }
.meta-item { white-space: nowrap; }
.shop-list { display: flex; flex-direction: column; gap: 10px; }
.shop-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 18px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}
.shop-info { flex: 1; display: flex; flex-direction: column; gap: 2px; }
.shop-name { font-size: 0.9rem; font-weight: 600; color: var(--fg); }
.shop-id { font-size: 0.78rem; color: var(--muted); }
.shop-meta { font-size: 0.8rem; color: var(--muted); }
.order-list { display: flex; flex-direction: column; gap: 12px; }
.order-card { padding: 16px 20px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); }
.order-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.order-id { font-size: 0.84rem; font-weight: 600; color: var(--muted); }
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  color: var(--muted);
  font-size: 0.9rem;
  text-align: center;
  gap: 12px;
}
.empty-icon { font-size: 2.5rem; opacity: 0.5; }
</style>
