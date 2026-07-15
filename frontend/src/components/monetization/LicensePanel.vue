<!-- LicensePanel — IP授权关联管理

Shows IP licenses linked to this listing.
Allows creating new licenses with smart pricing.
-->
<template>
  <div class="license-panel">
    <div class="panel-header">
      <h4>📜 IP 授权</h4>
      <button class="btn-add" @click="showNewLicense = true">+ 创建授权</button>
    </div>

    <div v-if="loading" class="loading-state">加载中...</div>

    <div v-else-if="!licenses.length" class="empty-state">
      <span class="empty-icon">📜</span>
      <p>暂无授权记录</p>
    </div>

    <div v-else class="license-list">
      <div v-for="lic in licenses" :key="lic.id" class="license-item">
        <div class="license-info">
          <div class="license-title">{{ lic.licenseTypeLabel || lic.license_type }}</div>
          <div class="license-participant">
            {{ lic.contract_party_name || '未填写' }}
            · {{ lic.platform || '自定义' }}
          </div>
          <div class="license-details">
            <span class="detail-chip">范围: {{ lic.scope }}</span>
            <span class="detail-chip">期限: {{ lic.duration }}</span>
            <span class="detail-chip">¥{{ lic.price }}</span>
          </div>
          <span :class="['license-status', lic.status]">{{ statusLabel(lic.status) }}</span>
        </div>
        <div class="license-actions">
          <button v-if="lic.contractUrl || lic.contract_signed" class="ext-btn" title="查看合约" @click="viewContract(lic)">📄</button>
          <button class="ext-btn" title="编辑" @click="editLicense(lic)">✏️</button>
        </div>
      </div>
    </div>

    <!-- New/Edit license dialog -->
    <div v-if="showNewLicense" class="modal-overlay" @click.self="showNewLicense = false">
      <div class="modal">
        <h4>{{ editingLic ? '编辑授权' : '创建 IP 授权' }}</h4>

        <div class="form-group">
          <label>授权类型</label>
          <select v-model="form.license_type" class="form-select">
            <option value="single_use">单次使用 (¥35-350)</option>
            <option value="multi_use">多次使用 (¥350-3,500)</option>
            <option value="commercial_extended">商业扩展 (¥700-7,000)</option>
            <option value="buyout">买断 (¥7,000+)</option>
            <option value="custom">自定义</option>
          </select>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>使用范围</label>
            <select v-model="form.usage_type" class="form-select">
              <option value="personal">个人使用</option>
              <option value="commercial">商业使用</option>
              <option value="resale">转售</option>
              <option value="modify">修改</option>
            </select>
          </div>
          <div class="form-group">
            <label>地域</label>
            <select v-model="form.geographic_scope" class="form-select">
              <option value="local">本地</option>
              <option value="national">全国</option>
              <option value="global">全球</option>
            </select>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>期限</label>
            <select v-model="form.duration" class="form-select">
              <option value="1year">1年</option>
              <option value="3years">3年</option>
              <option value="perpetual">永久</option>
            </select>
          </div>
          <div class="form-group">
            <label>媒介</label>
            <select v-model="form.medium" class="form-select">
              <option value="digital">数字</option>
              <option value="print">印刷</option>
              <option value="merchandise">商品</option>
              <option value="broadcast">广播</option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label>被授权方</label>
          <input v-model="form.party_name" class="form-input" placeholder="公司名称" />
        </div>

        <div class="form-group">
          <label>价格 (AI 建议: ¥{{ suggestedPrice }})</label>
          <input v-model.number="form.price" type="number" class="form-input" />
        </div>

        <div class="form-actions">
          <button class="btn-cancel" @click="showNewLicense = false">取消</button>
          <button class="btn-save" @click="saveLicense" :disabled="saving">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { supplyApi } from '@/api/supply'

interface Props {
  listingId: string
}
const props = defineProps<Props>()

const emit = defineEmits<{ (e: 'create-license', data: any): void }>()

interface LicRecord {
  id: string
  license_type: string
  licenseTypeLabel?: string
  platform: string
  price: number
  status: string
  contract_party_name?: string
  contract_signed?: boolean
  contractUrl?: string
  scope?: string
  duration?: string
}

const licenses = ref<LicRecord[]>([])
const loading = ref(false)
const saving = ref(false)
const showNewLicense = ref(false)
const editingLic = ref<LicRecord | null>(null)

const form = ref({
  license_type: 'single_use',
  usage_type: 'personal',
  geographic_scope: 'local',
  duration: '1year',
  medium: 'digital',
  party_name: '',
  price: 35,
})

// Smart pricing multiplier table
const priceMultipliers: Record<string, Record<string, number>> = {
  usage_type: { personal: 1, commercial: 2.5, resale: 5, buyout: 20 },
  geographic_scope: { local: 1, national: 1.5, global: 2 },
  duration: { '1year': 1, '3years': 1.5, perpetual: 2.5 },
  medium: { digital: 1, print: 1.3, merchandise: 2, broadcast: 3 },
}

// Base prices by license type
const basePrices: Record<string, number> = {
  single_use: 35,
  multi_use: 350,
  commercial_extended: 700,
  buyout: 7000,
  custom: 100,
}

const suggestedPrice = computed(() => {
  const base = basePrices[form.value.license_type] || 100
  const mult = priceMultipliers[form.value.usage_type]?.[form.value.usage_type] || 1
  // Simplified: multiply by all factors
  const u = priceMultipliers.usage_type[form.value.usage_type] || 1
  const g = priceMultipliers.geographic_scope[form.value.geographic_scope] || 1
  const d = priceMultipliers.duration[form.value.duration] || 1
  const m = priceMultipliers.medium[form.value.medium] || 1
  return Math.round(base * u * g * d * m)
})

function statusLabel(s: string): string {
  const map: Record<string, string> = {
    active: '有效', expired: '已过期', revoked: '已撤销', pending: '待签署',
  }
  return map[s] || s
}

async function loadLicenses() {
  loading.value = true
  try {
    const { data } = await supplyApi.licenses()
    licenses.value = (data as LicRecord[]).filter((l: any) => l.listing_id === props.listingId)
  } catch {
    licenses.value = []
  } finally {
    loading.value = false
  }
}

function editLicense(lic: LicRecord) {
  editingLic.value = lic
  form.value = {
    license_type: lic.license_type,
    usage_type: 'personal',
    geographic_scope: 'local',
    duration: '1year',
    medium: 'digital',
    party_name: lic.contract_party_name || '',
    price: lic.price,
  }
  showNewLicense.value = true
}

function viewContract(lic: LicRecord) {
  if (lic.contractUrl) {
    window.open(lic.contractUrl, '_blank')
  } else {
    ;(window as any).$toast?.show('合约文件尚未生成', 'info')
  }
}

async function saveLicense() {
  saving.value = true
  try {
    const payload = {
      ...form.value,
      listing_id: props.listingId,
      status: editingLic.value?.status || 'pending',
    }
    if (editingLic.value) {
      await supplyApi.updateLicense(editingLic.value.id, payload)
    } else {
      await supplyApi.createLicense(payload)
    }
    showNewLicense.value = false
    editingLic.value = null
    await loadLicenses()
  } catch {
    // Error toast
  } finally {
    saving.value = false
  }
}

onMounted(loadLicenses)
</script>

<style scoped>
.license-panel { padding: 0 4px; }

.panel-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 12px;
}
.panel-header h4 { margin: 0; font-size: .9rem; }

.btn-add {
  background: var(--accent); color: #fff; border: none;
  padding: 4px 12px; border-radius: var(--radius-sm); font-size: .78rem; cursor: pointer;
}

.loading-state, .empty-state {
  text-align: center; padding: 32px 0; color: var(--muted);
}
.empty-icon { font-size: 2rem; display: block; margin-bottom: 8px; }

.license-list { display: flex; flex-direction: column; gap: 8px; }

.license-item {
  display: flex; justify-content: space-between; align-items: flex-start;
  padding: 10px 14px; border: 1px solid var(--border);
  border-radius: var(--radius-sm); background: var(--surface);
}

.license-title { font-weight: 700; font-size: .88rem; }
.license-participant { font-size: .72rem; color: var(--muted); margin-top: 2px; }

.license-details { display: flex; gap: 6px; margin-top: 6px; flex-wrap: wrap; }

.detail-chip {
  font-size: .65rem; padding: 1px 6px;
  background: var(--muted-bg); border-radius: 100px;
}

.license-status {
  display: inline-block; margin-top: 6px;
  font-size: .68rem; font-weight: 600; padding: 1px 8px;
  border-radius: 100px;
}

.license-status.active { background: oklch(56% 0.12 140 / .15); color: oklch(56% 0.12 140); }
.license-status.expired { background: oklch(56% 0.12 20 / .15); color: oklch(56% 0.12 20); }
.license-status.pending { background: oklch(75% 0.08 80 / .15); color: oklch(65% 0.1 80); }

.license-actions { display: flex; gap: 4px; flex-shrink: 0; }
.ext-btn {
  background: none; border: 1px solid var(--border); border-radius: var(--radius-sm);
  padding: 4px 8px; cursor: pointer; font-size: .82rem;
}

/* Modal */
.modal-overlay {
  position: fixed; inset: 0;
  background: oklch(20% 0.02 180 / .5);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}

.modal {
  background: var(--bg); border: 1px solid var(--border);
  border-radius: var(--radius-md); padding: 24px;
  width: 480px; max-width: 90vw; max-height: 80vh; overflow-y: auto;
}

.modal h4 { margin: 0 0 16px; }
.form-group { margin-bottom: 12px; }
.form-group label { display: block; font-size: .78rem; margin-bottom: 4px; color: var(--muted); }

.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

.form-select, .form-input {
  width: 100%; padding: 6px 10px; border: 1px solid var(--border);
  border-radius: var(--radius-sm); font-size: .85rem; background: var(--surface);
}

.form-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px; }
.btn-cancel {
  padding: 6px 16px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  background: none; cursor: pointer; font-size: .82rem;
}
.btn-save {
  padding: 6px 16px; border: none; border-radius: var(--radius-sm);
  background: var(--accent); color: #fff; cursor: pointer; font-size: .82rem;
}
.btn-save:disabled { opacity: .5; cursor: not-allowed; }
</style>
