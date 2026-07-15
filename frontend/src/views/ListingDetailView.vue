<!-- ListingDetailView — 商品详情页

Central hub for a single listing. Shows:
1. Design preview + basic info
2. Monetization sub-tabs (POD/Crowdfunding/IP/Revenue/Orders)
3. Actions: Edit / Delete / Duplicate / Export
-->
<template>
  <div class="listing-detail-view">
    <!-- Back button -->
    <button class="back-btn" @click="goBack">← 返回</button>

    <!-- Header -->
    <div class="detail-header">
      <div>
        <h2>{{ listing?.title || '加载中...' }}</h2>
        <div class="header-meta">
          <span v-if="listing?.product_template_id">模板: {{ templateName }}</span>
          <span>创建于 {{ listing?.created_at ? formatDate(listing!.created_at) : '-' }}</span>
        </div>
      </div>
      <div class="header-actions">
        <button class="btn-edit" @click="toggleEditMode">✏️ 编辑</button>
        <button class="btn-duplicate" @click="duplicateListing">📋 复制</button>
        <button class="btn-delete" @click="deleteListing">🗑️ 删除</button>
      </div>
    </div>

    <!-- Main content -->
    <div v-if="listing" class="detail-main">
      <!-- Left: Design preview -->
      <div class="detail-preview">
        <div class="preview-card">
          <img
            v-if="listing.mockup_image_path"
            :src="listing.mockup_image_path"
            alt="商品预览"
            class="preview-img"
          />
          <div v-else class="preview-placeholder">
            <span>🎨</span>
            <p>暂无预览图</p>
          </div>
        </div>
      </div>

      <!-- Right: Basic info -->
      <div class="detail-info">
        <div class="info-card">
          <h4>基本信息</h4>
          <dl>
            <dt>价格</dt><dd>¥{{ listing.price }}</dd>
            <dt>成本</dt><dd>¥{{ listing.cost }}</dd>
            <dt>利润</dt><dd class="profit">¥{{ calcProfit }} ({{ calcMargin }}%)</dd>
            <dt>币种</dt><dd>{{ listing.currency }}</dd>
            <dt>状态</dt><dd><span :class="['status-dot', listing.status]">{{ statusLabel(listing.status) }}</span></dd>
            <dt>变现路径</dt><dd>{{ pathLabel(listing.monetization_path || '') }}</dd>
            <dt v-if="listing.variant_sku">SKU</dt><dd v-if="listing.variant_sku">{{ listing.variant_sku }}</dd>
          </dl>
        </div>

        <div class="info-card" v-if="listing.spec_validation">
          <h4>规格校验</h4>
          <div class="spec-result" :class="specResultClass">
            {{ specResultLabel }}
          </div>
        </div>
      </div>
    </div>

    <!-- Monetization sub-tabs -->
    <MonetizationTabs
      v-if="listingId"
      :listing-id="listingId"
      :active="activeTab"
      :counts="tabCounts"
      @update:active="activeTab = $event"
      @publish="handlePublish"
      @create-campaign="handleCreateCampaign"
      @create-license="handleCreateLicense"
    />

    <!-- Edit modal -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
      <div class="modal">
        <h4>编辑商品</h4>
        <div class="form-group">
          <label>标题</label>
          <input v-model="editForm.title" class="form-input" />
        </div>
        <div class="form-group">
          <label>描述</label>
          <textarea v-model="editForm.description" rows="3" class="form-input" />
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>价格</label>
            <input v-model.number="editForm.price" type="number" class="form-input" />
          </div>
          <div class="form-group">
            <label>成本</label>
            <input v-model.number="editForm.cost" type="number" class="form-input" />
          </div>
        </div>
        <div class="form-group">
          <label>状态</label>
          <select v-model="editForm.status" class="form-select">
            <option value="draft">草稿</option>
            <option value="active">在售</option>
            <option value="discontinued">已下架</option>
          </select>
        </div>
        <div class="form-actions">
          <button class="btn-cancel" @click="showEditModal = false">取消</button>
          <button class="btn-save" @click="saveEdit" :disabled="saving">保存</button>
        </div>
      </div>
    </div>

    <div v-else-if="!loading" class="detail-empty">
      <p>商品不存在或已被删除</p>
      <router-link to="/app/supply" class="btn btn-primary btn-sm">返回商业转化</router-link>
    </div>

    <div v-else-if="loading" class="detail-empty">
      <p>加载中...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { supplyApi } from '@/api/supply'
import type { ListingDetail } from '@/types/supply'
import MonetizationTabs from '@/components/monetization/MonetizationTabs.vue'

const router = useRouter()
const route = useRoute()
const listingId = computed(() => route.params.id as string)

const listing = ref<ListingDetail | null>(null)
const loading = ref(true)
const activeTab = ref('publication')
const showEditModal = ref(false)
const saving = ref(false)
const templateName = ref('')

const editForm = ref({ title: '', description: '', price: 0, cost: 0, status: 'draft' })

const calcProfit = computed(() => listing.value ? Math.max(0, +(listing.value.price - listing.value.cost).toFixed(2)) : 0)
const calcMargin = computed(() => listing.value && listing.value.price ? Math.round((calcProfit.value / listing.value.price) * 100) : 0)

const specResultClass = computed(() => {
  const sv = listing.value?.spec_validation as any
  if (!sv) return ''
  if (sv.error_count > 0) return 'spec-error'
  if (sv.warning_count > 0) return 'spec-warn'
  return 'spec-pass'
})

const specResultLabel = computed(() => {
  const sv = listing.value?.spec_validation as any
  if (!sv) return '未校验'
  if (sv.error_count > 0) return `❌ ${sv.error_count} 项错误`
  if (sv.warning_count > 0) return `⚠️ ${sv.warning_count} 项警告`
  return '✅ 规格校验通过'
})

const tabCounts = computed(() => ({
  publication: listing.value?.publications?.length || 0,
  campaign: 0, // Would need separate fetch
  license: 0,
  revenue: listing.value?.revenues?.length || 0,
  order: listing.value?.orders?.length || 0,
}))

function statusLabel(s: string): string {
  const map: Record<string, string> = { draft: '草稿', active: '在售', discontinued: '已下架' }
  return map[s] || s
}

function pathLabel(p?: string): string {
  const map: Record<string, string> = {
    pod: 'POD', crowdfunding: '众筹', licensing: 'IP授权',
    digital: '数字产品', custom_mfg: '定制制造',
  }
  return map[p || ''] || '-'
}

function formatDate(d: string): string {
  return new Date(d).toLocaleDateString('zh-CN')
}

async function loadDetail() {
  loading.value = true
  try {
    const { data } = await supplyApi.getListing(listingId.value)
    listing.value = data as ListingDetail
  } catch {
    listing.value = null
  } finally {
    loading.value = false
  }
}

function goBack() { router.push({ name: 'listings' }) }

function toggleEditMode() {
  if (!listing.value) return
  editForm.value = {
    title: listing.value.title,
    description: listing.value.description || '',
    price: listing.value.price,
    cost: listing.value.cost,
    status: listing.value.status,
  }
  showEditModal.value = true
}

async function saveEdit() {
  saving.value = true
  try {
    await supplyApi.updateListing(listingId.value, editForm.value)
    showEditModal.value = false
    await loadDetail()
  } catch {
    // Error toast
  } finally {
    saving.value = false
  }
}

function duplicateListing() {
  if (!listing.value) return
  ;(window as any).$toast?.show('复制商品功能将在后续版本中实现', 'info')
}

async function deleteListing() {
  if (!confirm('确定下架此商品？')) return
  try {
    await supplyApi.deleteListing(listingId.value)
    goBack()
  } catch {
    // Error toast
  }
}

function handlePublish(id: string) {
  router.push({ name: 'listing-detail', params: { id }, hash: '#publication' })
}

function handleCreateCampaign(_data: any) {
  ;(window as any).$toast?.show('创建众筹功能将在后续版本中实现', 'info')
}

function handleCreateLicense(_data: any) {
  ;(window as any).$toast?.show('创建授权功能将在后续版本中实现', 'info')
}

onMounted(loadDetail)
</script>

<style scoped>
.listing-detail-view { padding: 20px; max-width: 1200px; margin: 0 auto; }

.back-btn {
  background: none; border: 1px solid var(--border); border-radius: var(--radius-sm);
  padding: 4px 12px; cursor: pointer; font-size: .82rem; margin-bottom: 16px;
}

.detail-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  margin-bottom: 20px;
}

.detail-header h2 { margin: 0; font-size: 1.4rem; }

.header-meta { display: flex; gap: 16px; font-size: .78rem; color: var(--muted); margin-top: 4px; }

.header-actions { display: flex; gap: 8px; }

.btn-edit, .btn-duplicate, .btn-delete {
  padding: 6px 14px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  background: none; cursor: pointer; font-size: .82rem;
}

.btn-edit:hover { border-color: var(--accent); }
.btn-duplicate:hover { border-color: oklch(65% 0.1 270); }
.btn-delete:hover { border-color: oklch(56% 0.18 20); }

.detail-main { display: grid; grid-template-columns: 280px 1fr; gap: 24px; margin-bottom: 24px; }

.preview-card {
  border: 1px solid var(--border); border-radius: var(--radius-md);
  overflow: hidden; background: var(--surface);
}

.preview-img { width: 100%; aspect-ratio: 1; object-fit: cover; }

.preview-placeholder {
  aspect-ratio: 1; display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  color: var(--muted); font-size: 2rem;
}
.preview-placeholder p { font-size: .82rem; margin-top: 8px; }

.info-card {
  border: 1px solid var(--border); border-radius: var(--radius-md);
  padding: 16px; background: var(--surface); margin-bottom: 12px;
}

.info-card h4 { margin: 0 0 12px; font-size: .92rem; }

.info-card dl { display: grid; grid-template-columns: auto 1fr; gap: 4px 12px; font-size: .82rem; }
.info-card dt { color: var(--muted); }
.info-card dd { font-weight: 600; }

.profit { color: var(--accent); }

.status-dot {
  display: inline-block; width: 8px; height: 8px;
  border-radius: 50%; margin-right: 4px;
}

.status-dot.active { background: oklch(56% 0.12 140); }
.status-dot.draft { background: oklch(65% 0.1 80); }
.status-dot.discontinued { background: oklch(56% 0.12 20); }

.spec-result {
  padding: 8px 12px; border-radius: var(--radius-sm); font-size: .82rem; font-weight: 600;
}

.spec-result.spec-pass { background: oklch(56% 0.12 140 / .1); color: oklch(56% 0.12 140); }
.spec-result.spec-warn { background: oklch(75% 0.12 80 / .1); color: oklch(65% 0.12 80); }
.spec-result.spec-error { background: oklch(56% 0.18 20 / .1); color: oklch(56% 0.18 20); }

/* Modal */
.modal-overlay {
  position: fixed; inset: 0;
  background: oklch(20% 0.02 180 / .5);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}

.modal {
  background: var(--bg); border: 1px solid var(--border);
  border-radius: var(--radius-md); padding: 24px; width: 440px; max-width: 90vw;
}

.modal h4 { margin: 0 0 16px; }
.form-group { margin-bottom: 12px; }
.form-group label { display: block; font-size: .78rem; margin-bottom: 4px; color: var(--muted); }

.form-input, .form-select {
  width: 100%; padding: 6px 10px; border: 1px solid var(--border);
  border-radius: var(--radius-sm); font-size: .85rem; background: var(--surface);
}

.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

.form-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px; }
.btn-cancel {
  padding: 6px 16px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  background: none; cursor: pointer; font-size: .82rem;
}
.btn-save {
  padding: 6px 16px; border: none; border-radius: var(--radius-sm);
  background: var(--accent); color: #fff; cursor: pointer; font-size: .82rem;
}

.detail-empty {
  text-align: center;
  padding: 80px 20px;
  color: var(--muted);
}
.detail-empty p {
  margin: 0 0 16px;
  font-size: 0.95rem;
}
</style>
