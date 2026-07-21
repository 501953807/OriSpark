<template>
  <div class="craftsman-view">
    <!-- Error banner -->
    <div v-if="store.errorMsg" class="error-banner">
      <span>{{ store.errorMsg }}</span>
      <button @click="store.clearError()">&times;</button>
    </div>

    <!-- Stats bar -->
    <div class="stats-bar">
      <div class="stat-item">
        <span class="stat-label">🏭 总作品</span>
        <span class="stat-value">{{ statsDisplay.total_products }}</span>
      </div>
      <div class="stat-item stat-active">
        <span class="stat-label">📦 在售</span>
        <span class="stat-value">{{ statsDisplay.active_listings }}</span>
      </div>
      <div class="stat-item stat-factory">
        <span class="stat-label">🏢 合作工厂</span>
        <span class="stat-value">{{ statsDisplay.factory_count }}</span>
      </div>
      <div class="stat-item stat-rfq">
        <span class="stat-label">📋 询价单</span>
        <span class="stat-value">{{ statsDisplay.rfq_count }}</span>
      </div>
      <div class="stat-item stat-revenue">
        <span class="stat-label">💰 本月营收</span>
        <span class="stat-value">¥{{ statsDisplay.monthly_revenue.toLocaleString() }}</span>
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

    <!-- ============================================ -->
    <!-- ── Products tab ──────────────────────────── -->
    <!-- ============================================ -->
    <div v-if="activeTab === 'products'" class="tab-panel">
      <div class="panel-header">
        <h2 class="section-title">我的作品</h2>
        <button class="btn btn-primary btn-sm" @click="showProductForm = !showProductForm">
          {{ showProductForm ? '取消' : '+ 新建作品' }}
        </button>
      </div>
      <div v-if="showProductForm" class="form-card">
        <h3 class="form-title">新建作品</h3>
        <div class="form-grid">
          <input v-model="productForm.title" class="form-input" placeholder="作品标题" />
          <select v-model="productForm.craft_type" class="form-input">
            <option disabled value="">选择工艺类型</option>
            <option v-for="ct in craftTypes" :key="ct" :value="ct">{{ craftLabels[ct] }}</option>
          </select>
          <input v-model="productForm.material" class="form-input" placeholder="材质" />
          <input v-model.number="productForm.moq" type="number" class="form-input" placeholder="MOQ" />
          <input v-model.number="productForm.unit_price" type="number" class="form-input" placeholder="单价 (¥)" />
          <input v-model.number="productForm.production_time_days" type="number" class="form-input" placeholder="生产周期 (天)" />
        </div>
        <div class="form-actions">
          <button class="btn btn-primary" @click="handleCreateProduct">创建</button>
          <button class="btn btn-outline" @click="showProductForm = false">取消</button>
        </div>
      </div>
      <div v-if="store.products.length === 0 && !store.loading" class="empty-state">
        <span class="empty-icon">🏭</span>
        <p>暂无作品，点击上方按钮创建第一个作品。</p>
      </div>
      <div v-else class="product-grid">
        <div v-for="p in store.products" :key="p.id" class="product-card">
          <div class="product-card-top">
            <span class="product-title">{{ p.title || '未命名作品' }}</span>
            <span :class="['badge', 'badge-type', badgeClass(p.craft_type)]">
              {{ craftLabels[p.craft_type] || p.craft_type }}
            </span>
          </div>
          <div class="product-meta">
            <span v-if="p.material" class="meta-item">🔭 {{ p.material }}</span>
          </div>
          <div class="product-meta">
            <span class="meta-item">📦 MOQ: {{ p.moq }}</span>
            <span v-if="p.unit_price" class="meta-item">💰 ¥{{ p.unit_price }}</span>
          </div>
          <div v-if="p.production_time_days" class="product-meta">
            <span class="meta-item">📅 {{ p.production_time_days }} 天</span>
          </div>
          <div class="product-actions">
            <button class="btn btn-sm btn-outline" @click="handleDeleteProduct(p.id)">删除</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ============================================ -->
    <!-- ── Factories tab ─────────────────────────── -->
    <!-- ============================================ -->
    <div v-if="activeTab === 'factories'" class="tab-panel">
      <div class="panel-header">
        <h2 class="section-title">合作工厂</h2>
        <button class="btn btn-primary btn-sm" @click="showFactoryForm = !showFactoryForm">
          {{ showFactoryForm ? '取消' : '+ 添加工厂' }}
        </button>
      </div>
      <div v-if="showFactoryForm" class="form-card">
        <h3 class="form-title">添加工厂</h3>
        <div class="form-grid">
          <input v-model="factoryForm.name" class="form-input" placeholder="工厂名称" />
          <input v-model="factoryForm.location" class="form-input" placeholder="所在地" />
          <input v-model="factoryForm.contact" class="form-input" placeholder="联系人" />
          <input v-model.number="factoryForm.rating" type="number" step="0.1" min="0" max="5" class="form-input" placeholder="评分 (0-5)" />
        </div>
        <div class="form-actions">
          <button class="btn btn-primary" @click="handleCreateFactory">添加</button>
          <button class="btn btn-outline" @click="showFactoryForm = false">取消</button>
        </div>
      </div>
      <div v-if="store.factories.length === 0 && !store.loading" class="empty-state">
        <span class="empty-icon">🏢</span>
        <p>暂无合作工厂。</p>
      </div>
      <div v-else class="factory-list">
        <div v-for="f in store.factories" :key="f.id" class="factory-card">
          <div class="factory-info">
            <span class="factory-name">{{ f.name }}</span>
            <span v-if="f.location" class="factory-location">📍 {{ f.location }}</span>
          </div>
          <div v-if="f.rating != null" class="factory-rating">★ {{ f.rating.toFixed(1) }}</div>
          <div class="factory-tags">
            <span v-for="cap in (f.capabilities ?? [])" :key="cap" class="tag">{{ cap }}</span>
            <span v-if="!f.capabilities?.length" class="tag tag-muted">无能力标签</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ============================================ -->
    <!-- ── RFQs tab ──────────────────────────────── -->
    <!-- ============================================ -->
    <div v-if="activeTab === 'rfqs'" class="tab-panel">
      <div class="panel-header">
        <h2 class="section-title">询价单</h2>
        <button class="btn btn-primary btn-sm" @click="showRfqForm = !showRfqForm">
          {{ showRfqForm ? '取消' : '+ 新建询价' }}
        </button>
      </div>
      <div v-if="showRfqForm" class="form-card">
        <h3 class="form-title">新建询价单</h3>
        <div class="form-grid">
          <input v-model="rfqForm.title" class="form-input" placeholder="询价标题" />
          <textarea v-model="rfqForm.description" class="form-input form-textarea" placeholder="描述" rows="3" />
          <input v-model.number="rfqForm.quantity_needed" type="number" class="form-input" placeholder="需求数量" />
          <input v-model.number="rfqForm.target_price" type="number" class="form-input" placeholder="目标单价 (¥)" />
          <select v-model="rfqForm.status" class="form-input">
            <option value="open">开放</option>
            <option value="quoted">已报价</option>
            <option value="awarded">已授予</option>
            <option value="closed">已关闭</option>
          </select>
        </div>
        <div class="form-actions">
          <button class="btn btn-primary" @click="handleCreateRFQ">创建</button>
          <button class="btn btn-outline" @click="showRfqForm = false">取消</button>
        </div>
      </div>
      <div v-if="store.rfqs.length === 0 && !store.loading" class="empty-state">
        <span class="empty-icon">📋</span>
        <p>暂无询价单。</p>
      </div>
      <div v-else class="rfq-list">
        <div v-for="r in store.rfqs" :key="r.id" class="rfq-card">
          <div class="rfq-header">
            <span class="rfq-title">{{ r.title }}</span>
            <span :class="['badge', statusBadgeClass(r.status)]">{{ statusLabel(r.status) }}</span>
          </div>
          <div v-if="r.description" class="rfq-desc">{{ r.description }}</div>
          <div class="rfq-meta">
            <span v-if="r.quantity_needed" class="meta-item">📦 {{ r.quantity_needed }}</span>
            <span v-if="r.target_price" class="meta-item">💰 ¥{{ r.target_price }}</span>
            <span v-if="r.quoted_factories?.length" class="meta-item">🏢 {{ r.quoted_factories.length }} 家报价</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ============================================ -->
    <!-- ── Orders tab ────────────────────────────── -->
    <!-- ============================================ -->
    <div v-if="activeTab === 'orders'" class="tab-panel">
      <h2 class="section-title">订单跟踪</h2>
      <div v-if="store.orders.length === 0 && !store.loading" class="empty-state">
        <span class="empty-icon">📊</span>
        <p>暂无订单，创建询价单并授予工厂后将自动生成订单。</p>
      </div>
      <div v-else class="order-list">
        <div v-for="o in store.orders" :key="o.id" class="order-card">
          <div class="order-header">
            <span class="order-id">#{{ o.id.slice(0, 8) }}</span>
            <span class="badge badge-order">{{ orderPhaseLabel(o.sample_status) }}</span>
          </div>
          <div class="order-steps">
            <span class="step-group">
              <span :class="['step-dot', { done: orderStepDone(0, o) }]"/>
              <span class="step-label">打样</span>
            </span>
            <span :class="['step-line', { done: orderStepDone(0, o) }]"/>
            <span class="step-group">
              <span :class="['step-dot', { done: orderStepDone(1, o) }]"/>
              <span class="step-label">质检</span>
            </span>
            <span :class="['step-line', { done: orderStepDone(1, o) }]"/>
            <span class="step-group">
              <span :class="['step-dot', { done: orderStepDone(2, o) }]"/>
              <span class="step-label">发货</span>
            </span>
            <span :class="['step-line', { done: orderStepDone(2, o) }]"/>
            <span class="step-group">
              <span :class="['step-dot', { done: orderStepDone(3, o) }]"/>
              <span class="step-label">同步</span>
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- ============================================ -->
    <!-- ── Physical Products tab ─────────────────── -->
    <!-- ============================================ -->
    <div v-if="activeTab === 'physical'" class="tab-panel">
      <div class="panel-header">
        <h2 class="section-title">实物产品管理</h2>
        <button class="btn btn-primary btn-sm" @click="showPhysicalForm = !showPhysicalForm">
          {{ showPhysicalForm ? '取消' : '+ 新建实物产品' }}
        </button>
      </div>
      <div v-if="showPhysicalForm" class="form-card">
        <h3 class="form-title">新建实物产品</h3>
        <div class="form-grid">
          <input v-model="physicalProductForm.title" class="form-input" placeholder="产品名称" />
          <textarea v-model="physicalProductForm.description" class="form-input form-textarea" placeholder="描述" rows="2" />
          <select v-model="physicalProductForm.category" class="form-input">
            <option disabled value="">选择分类</option>
            <option v-for="c in physicalCategories" :key="c" :value="c">{{ c }}</option>
          </select>
          <input v-model.number="physicalProductForm.price" type="number" step="0.01" class="form-input" placeholder="价格 (¥)" />
          <input v-model.number="physicalProductForm.stock_quantity" type="number" class="form-input" placeholder="库存数量" />
          <label class="checkbox-label">
            <input v-model="physicalProductForm.is_active" type="checkbox" />
            激活上架
          </label>
        </div>
        <div class="form-actions">
          <button class="btn btn-primary" @click="handleCreatePhysicalProduct">创建</button>
          <button class="btn btn-outline" @click="showPhysicalForm = false">取消</button>
        </div>
      </div>
      <div v-if="store.physicalProducts.length === 0 && !store.loading" class="empty-state">
        <span class="empty-icon">📦</span>
        <p>暂无实物产品。</p>
      </div>
      <div v-else class="product-grid">
        <div v-for="p in store.physicalProducts" :key="p.id" class="product-card">
          <div class="product-card-top">
            <span class="product-title">{{ p.title }}</span>
            <span :class="['badge', p.is_active ? 'badge-active' : 'badge-inactive']">
              {{ p.is_active ? '在售' : '下架' }}
            </span>
          </div>
          <div v-if="p.description" class="rfq-desc">{{ p.description }}</div>
          <div class="product-meta">
            <span v-if="p.category" class="meta-item">📂 {{ p.category }}</span>
            <span class="meta-item">💰 ¥{{ p.price }}</span>
            <span class="meta-item">📦 库存: {{ p.stock_quantity }}</span>
          </div>
          <div class="product-actions">
            <button class="btn btn-sm btn-danger" @click="handleDeletePhysicalProduct(p.id)">删除</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ============================================ -->
    <!-- ── Materials tab ──────────────────────────── -->
    <!-- ============================================ -->
    <div v-if="activeTab === 'materials'" class="tab-panel">
      <MaterialInventoryPanel :materials="store.materials" />
    </div>

    <!-- ============================================ -->
    <!-- ── Batches tab ────────────────────────────── -->
    <!-- ============================================ -->
    <div v-if="activeTab === 'batches'" class="tab-panel">
      <ProductionBatchPanel :batches="store.productionBatches" />
    </div>

    <!-- Loading overlay -->
    <div v-if="store.loading" class="loading-overlay">
      <div class="spinner">⌛ 加载中...</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useCraftsmanStore } from '@/stores/useCraftsmanStore'
import type { CraftType, RFQStatus, SampleStatus, QualityStatus, ETSyncStatus } from '@/types/craftsman'
import MaterialInventoryPanel from '@/components/craftsman/MaterialInventoryPanel.vue'
import ProductionBatchPanel from '@/components/craftsman/ProductionBatchPanel.vue'

const store = useCraftsmanStore()

// ── Tabs ──────────────────────────────────────────────────────
const tabs = [
  { key: 'products', label: '作品', icon: '🏭' },
  { key: 'factories', label: '工厂', icon: '🏢' },
  { key: 'rfqs', label: '询价', icon: '📋' },
  { key: 'orders', label: '订单', icon: '📊' },
  { key: 'physical', label: '实物产品', icon: '📦' },
  { key: 'materials', label: '原料库存', icon: '🧱' },
  { key: 'batches', label: '生产批次', icon: '🔢' },
]
const activeTab = ref<string>('products')

// ── Stats ─────────────────────────────────────────────────────
const statsDisplay = computed(() => store.stats ?? {
  total_products: 0,
  active_listings: 0,
  factory_count: 0,
  rfq_count: 0,
  monthly_revenue: 0,
})

// ── Product form ──────────────────────────────────────────────
const showProductForm = ref(false)
const productForm = reactive({
  title: '',
  craft_type: 'embroidery' as CraftType,
  material: '',
  moq: 1,
  unit_price: undefined as number | undefined,
  production_time_days: undefined as number | undefined,
})
const craftTypes: CraftType[] = ['embroidery', 'ceramics', 'woodcarving', 'weaving', 'pottery', 'other']
const craftLabels: Record<CraftType, string> = {
  embroidery: '刺绣', ceramics: '陶瓷', woodcarving: '木雕', weaving: '编织', pottery: '陶艺', other: '其他',
}
function badgeClass(ct: CraftType): string { return ct || 'other' }

async function handleCreateProduct() {
  if (!productForm.title.trim()) {
    ;(window as any).$toast?.show('请填写作品标题', 'error')
    return
  }
  try {
    await store.createProduct({
      title: productForm.title,
      craft_type: productForm.craft_type,
      material: productForm.material,
      moq: productForm.moq,
      unit_price: productForm.unit_price,
      production_time_days: productForm.production_time_days,
    })
    ;(window as any).$toast?.show('作品创建成功', 'success')
    Object.assign(productForm, { title: '', material: '', moq: 1, unit_price: undefined, production_time_days: undefined })
    showProductForm.value = false
    await store.fetchProducts()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '创建失败'
    ;(window as any).$toast?.show(msg, 'error')
  }
}

async function handleDeleteProduct(id: string) {
  try {
    await store.deleteProduct(id)
    ;(window as any).$toast?.show('作品已删除', 'success')
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '删除失败'
    ;(window as any).$toast?.show(msg, 'error')
  }
}

// ── Factory form ──────────────────────────────────────────────
const showFactoryForm = ref(false)
const factoryForm = reactive({
  name: '', location: '', contact: '', rating: undefined as number | undefined,
})

async function handleCreateFactory() {
  if (!factoryForm.name.trim()) {
    ;(window as any).$toast?.show('请填写工厂名称', 'error')
    return
  }
  try {
    await store.createFactory({
      name: factoryForm.name,
      location: factoryForm.location,
      contact: factoryForm.contact,
      rating: factoryForm.rating,
    })
    ;(window as any).$toast?.show('工厂添加成功', 'success')
    Object.assign(factoryForm, { name: '', location: '', contact: '', rating: undefined })
    showFactoryForm.value = false
    await store.fetchFactories()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '添加失败'
    ;(window as any).$toast?.show(msg, 'error')
  }
}

// ── RFQ form ──────────────────────────────────────────────────
const showRfqForm = ref(false)
const rfqForm = reactive({
  title: '', description: '', quantity_needed: undefined as number | undefined,
  target_price: undefined as number | undefined, status: 'open' as RFQStatus,
})
const statusLabels: Record<RFQStatus, string> = { open: '开放', quoted: '已报价', awarded: '已授予', closed: '已关闭' }
function statusLabel(s: RFQStatus): string { return statusLabels[s] ?? s }
function statusBadgeClass(s: RFQStatus): string {
  const map: Record<RFQStatus, string> = { open: 'badge-open', quoted: 'badge-quoted', awarded: 'badge-awarded', closed: 'badge-closed' }
  return map[s] ?? 'badge-open'
}

async function handleCreateRFQ() {
  if (!rfqForm.title.trim()) {
    ;(window as any).$toast?.show('请填写询价标题', 'error')
    return
  }
  try {
    await store.createRFQ({
      craft_product_id: '', title: rfqForm.title, description: rfqForm.description,
      quantity_needed: rfqForm.quantity_needed, target_price: rfqForm.target_price, status: rfqForm.status,
    })
    ;(window as any).$toast?.show('询价单创建成功', 'success')
    Object.assign(rfqForm, { title: '', description: '', quantity_needed: undefined, target_price: undefined, status: 'open' as RFQStatus })
    showRfqForm.value = false
    await store.fetchRFQs()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '创建失败'
    ;(window as any).$toast?.show(msg, 'error')
  }
}

// ── Order phase labels ────────────────────────────────────────
const phaseLabels = ['打样', '质检', '发货', '同步']
function orderPhaseLabel(ss: SampleStatus): string {
  if (ss === 'pending') return '待打样'
  if (ss === 'approved') return '质检中'
  if (ss === 'rejected') return '打样驳回'
  return ss
}
function orderStepDone(step: number, o: { sample_status: SampleStatus; quality_inspection: QualityStatus; delivery_date?: string; etasync_status: ETSyncStatus }): boolean {
  if (step === 0) return o.sample_status !== 'pending'
  if (step === 1) return o.quality_inspection === 'pass'
  if (step === 2) return !!o.delivery_date
  if (step === 3) return o.etasync_status === 'synced'
  return false
}

// ── Physical Products ─────────────────────────────────────────
const showPhysicalForm = ref(false)
const physicalProductForm = reactive({
  title: '', description: '', category: '' as string, price: 0, stock_quantity: 0, is_active: true,
})
const physicalCategories = ['刺绣', '陶瓷', '木雕', '编织', '陶艺', '珠宝', '家居', '服饰', '其他']

async function handleCreatePhysicalProduct() {
  if (!physicalProductForm.title.trim()) {
    ;(window as any).$toast?.show('请填写产品名称', 'error')
    return
  }
  try {
    await store.createPhysicalProduct({
      title: physicalProductForm.title,
      description: physicalProductForm.description || null,
      category: physicalProductForm.category || null,
      price: physicalProductForm.price,
      stock_quantity: physicalProductForm.stock_quantity,
      is_active: physicalProductForm.is_active,
      work_id: null,
      dimensions: null,
      weight_g: null,
      currency: 'CNY',
      shipping_regions: null,
    })
    ;(window as any).$toast?.show('实物产品创建成功', 'success')
    Object.assign(physicalProductForm, { title: '', description: '', category: '', price: 0, stock_quantity: 0, is_active: true })
    showPhysicalForm.value = false
    await store.fetchPhysicalProducts()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '创建失败'
    ;(window as any).$toast?.show(msg, 'error')
  }
}

async function handleDeletePhysicalProduct(id: string) {
  try {
    await store.deletePhysicalProduct(id)
    ;(window as any).$toast?.show('实物产品已删除', 'success')
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '删除失败'
    ;(window as any).$toast?.show(msg, 'error')
  }
}

// ── Lifecycle ─────────────────────────────────────────────────
onMounted(async () => {
  try {
    await store.fetchAll()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '加载失败'
    store.setError(msg)
  }
})
</script>

<style scoped>
.craftsman-view {
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
.stat-factory .stat-value { color: #ea580c; }
.stat-rfq .stat-value { color: #2563eb; }
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
.badge-type { background: oklch(85% 0.05 150); color: oklch(35% 0.05 150); }
.badge-open { background: #dbeafe; color: #1d4ed8; }
.badge-quoted { background: #fef3c7; color: #92400e; }
.badge-awarded { background: #dcfce7; color: #166534; }
.badge-closed { background: #f1f5f9; color: #475569; }
.badge-order { background: var(--bg); color: var(--muted); }
.badge-active { background: #dcfce7; color: #166534; }
.badge-inactive { background: #f1f5f9; color: #475569; }
.product-card-top, .rfq-header { display: flex; align-items: center; gap: 8px; }
.product-title, .rfq-title {
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
.product-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 4px;
  font-size: 0.8rem;
  color: var(--muted);
}
.product-actions { margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--border); }
.meta-item { white-space: nowrap; }
.factory-list { display: flex; flex-direction: column; gap: 10px; }
.factory-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 18px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}
.factory-info { flex: 1; display: flex; flex-direction: column; gap: 2px; }
.factory-name { font-size: 0.9rem; font-weight: 600; color: var(--fg); }
.factory-location { font-size: 0.8rem; color: var(--muted); }
.factory-rating { font-size: 0.9rem; font-weight: 700; color: #eab308; font-family: var(--font-display); }
.factory-tags { display: flex; flex-wrap: wrap; gap: 4px; }
.tag {
  font-size: 0.72rem;
  padding: 2px 8px;
  border-radius: 8px;
  background: var(--bg);
  color: var(--muted);
  border: 1px solid var(--border);
}
.tag-muted { opacity: 0.5; }
.rfq-list { display: flex; flex-direction: column; gap: 10px; }
.rfq-card { padding: 14px 18px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); }
.rfq-desc { font-size: 0.84rem; color: var(--muted); margin-top: 4px; }
.order-list { display: flex; flex-direction: column; gap: 12px; }
.order-card { padding: 16px 20px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); }
.order-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.order-id { font-size: 0.84rem; font-weight: 600; color: var(--muted); }
.order-steps { display: flex; align-items: center; gap: 0; }
.step-dot { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.step-dot::before {
  content: '';
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid var(--border);
  background: var(--bg);
  transition: background 0.2s, border-color 0.2s;
}
.step-dot.done::before { background: var(--accent); border-color: var(--accent); }
.step-group { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.step-label { font-size: 0.7rem; color: var(--muted); white-space: nowrap; }
.step-line { width: 40px; height: 2px; background: var(--border); margin: 0 4px; transition: background 0.2s; }
.step-line.done { background: var(--accent); }
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
.checkbox-label {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  font-size: 0.84rem;
  color: var(--fg);
}
</style>
