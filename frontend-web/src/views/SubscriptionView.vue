<template>
  <div class="view-page">
    <div class="tabs-header">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-btn"
        :class="{ active: activeTab === tab.key }"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab 1: Subscription Tiers -->
    <div v-if="activeTab === 'tiers'" class="tab-content">
      <div class="page-header">
        <h2>订阅等级</h2>
        <button class="btn btn-primary btn-sm" @click="showTierModal = true; editingTier = null; resetTierForm()">+ 新建等级</button>
      </div>

      <div class="tier-cards">
        <div v-for="tier in tiers" :key="tier.id" class="tier-card" :class="{ inactive: !tier.is_active }">
          <div class="tier-header">
            <div>
              <div class="tier-name">{{ tier.name }}</div>
              <div v-if="tier.description" class="tier-desc">{{ tier.description }}</div>
            </div>
            <span class="tier-price">{{ tier.currency === 'CNY' ? '¥' : '$' }}{{ tier.price }}/{{ tier.billing_period }}</span>
          </div>
          <div class="tier-meta">
            <span :class="['badge', tier.is_active ? 'badge-active' : 'badge-inactive']">
              {{ tier.is_active ? '启用中' : '已停用' }}
            </span>
            <span class="count-badge">{{ tier.subscriber_count || 0 }} 订阅者</span>
          </div>
          <div v-if="tier.features" class="tier-features">
            <span v-for="(f, i) in parseFeatures(tier.features)" :key="i" class="feature-tag">{{ f }}</span>
          </div>
          <div class="tier-actions">
            <button class="btn btn-ghost btn-xs" @click="editTier(tier)">编辑</button>
            <button class="btn btn-ghost btn-xs" @click="toggleTierActive(tier)">
              {{ tier.is_active ? '停用' : '启用' }}
            </button>
            <button class="btn btn-ghost btn-xs btn-danger-sm" @click="confirmDeleteTier(tier)">删除</button>
          </div>
        </div>
      </div>
      <div v-if="tiers.length === 0" class="empty-hint">暂无订阅等级</div>
    </div>

    <!-- Tab 2: Subscribers -->
    <div v-if="activeTab === 'subscribers'" class="tab-content">
      <div class="page-header">
        <h2>订阅用户</h2>
      </div>
      <div class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>用户 ID</th>
              <th>等级</th>
              <th>状态</th>
              <th>订阅时间</th>
              <th>到期时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="sub in subscribers" :key="sub.id">
              <td class="mono-cell">{{ sub.user_id }}</td>
              <td>{{ sub.tier_name || '-' }}</td>
              <td><span :class="['badge', sub.status === 'active' ? 'badge-active' : 'badge-inactive']">{{ statusLabel(sub.status) }}</span></td>
              <td>{{ formatDate(sub.subscribed_at) }}</td>
              <td>{{ formatDate(sub.expires_at) }}</td>
              <td>
                <button v-if="sub.status === 'active'" class="btn btn-ghost btn-xs btn-danger-sm" @click="cancelSub(sub)">取消订阅</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="subscribers.length === 0" class="empty-hint">暂无订阅用户</div>
    </div>

    <!-- Tier Modal -->
    <div v-if="showTierModal" class="modal-overlay" @click.self="showTierModal = false">
      <div class="modal-card animate-scale-in" style="max-width:500px">
        <div class="modal-header">
          <h3>{{ editingTier ? '编辑等级' : '新建等级' }}</h3>
          <button class="modal-close-btn" @click="showTierModal = false">&times;</button>
        </div>
        <div class="form-group">
          <label>名称</label>
          <input v-model="tierForm.name" class="form-input" placeholder="专业版" />
        </div>
        <div class="form-group">
          <label>描述</label>
          <textarea v-model="tierForm.description" class="form-textarea" rows="2" placeholder="等级描述"></textarea>
        </div>
        <div class="form-row-2">
          <div class="form-group">
            <label>价格</label>
            <input v-model.number="tierForm.price" type="number" class="form-input" placeholder="99" />
          </div>
          <div class="form-group">
            <label>货币</label>
            <select v-model="tierForm.currency" class="form-select">
              <option>CNY</option>
              <option>USD</option>
            </select>
          </div>
        </div>
        <div class="form-group">
          <label>计费周期</label>
          <select v-model="tierForm.billing_period" class="form-select">
            <option value="monthly">按月</option>
            <option value="yearly">按年</option>
            <option value="one_time">一次性</option>
          </select>
        </div>
        <div class="form-group">
          <label>功能列表 (每行一个)</label>
          <textarea v-model="tierForm.features_str" class="form-textarea" rows="3" placeholder="无限存储
高清下载
API 访问"></textarea>
        </div>
        <div class="form-group">
          <label class="checkbox-label">
            <input type="checkbox" v-model="tierForm.is_active" />
            启用
          </label>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showTierModal = false">取消</button>
          <button class="btn btn-primary" @click="saveTier" :disabled="saving">保存</button>
        </div>
      </div>
    </div>

    <!-- Delete Tier Confirmation -->
    <div v-if="deleteTierTarget" class="modal-overlay" @click.self="deleteTierTarget = null">
      <div class="modal-card animate-scale-in" style="max-width:400px">
        <div class="modal-header">
          <h3 style="color:#ef4444">确认删除</h3>
          <button class="modal-close-btn" @click="deleteTierTarget = null">&times;</button>
        </div>
        <p style="color:var(--muted);font-size:0.9rem">确定要删除等级「{{ deleteTierTarget?.name }}」吗？</p>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="deleteTierTarget = null">取消</button>
          <button class="btn btn-danger" @click="doDeleteTier" :disabled="deleting">确认删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { systemApi } from '@/api/system'

interface SubscriptionTier {
  id: string
  name: string
  description: string
  price: number
  currency: string
  billing_period: string
  features: string | Record<string, unknown> | null
  features_str: string
  subscriber_count: number
  is_active: boolean
}

interface Subscriber {
  id: string
  user_id: string
  tier_name: string
  status: string
  subscribed_at: string
  expires_at: string
}

const tabs = [
  { key: 'tiers', label: '订阅等级' },
  { key: 'subscribers', label: '订阅用户' },
]
const activeTab = ref('tiers')

const tiers = ref<SubscriptionTier[]>([])
const subscribers = ref<Subscriber[]>([])
const loading = ref(false)
const saving = ref(false)
const deleting = ref(false)

const showTierModal = ref(false)
const editingTier = ref<SubscriptionTier | null>(null)
const deleteTierTarget = ref<SubscriptionTier | null>(null)

const tierForm = ref({
  name: '', description: '', price: 0, currency: 'CNY',
  billing_period: 'monthly', features_str: '', is_active: true,
})

function parseFeatures(raw: string | Record<string, unknown> | null): string[] {
  if (!raw) return []
  if (typeof raw === 'string') {
    try { return JSON.parse(raw) } catch { return [] }
  }
  if (Array.isArray(raw)) return raw.map(String)
  return Object.values(raw).map(String)
}

function statusLabel(s: string): string {
  const map: Record<string, string> = { active: '有效', expired: '已过期', canceled: '已取消' }
  return map[s] || s
}

function formatDate(d?: string): string {
  if (!d) return '-'
  return d.slice(0, 10)
}

function resetTierForm() {
  tierForm.value = { name: '', description: '', price: 0, currency: 'CNY', billing_period: 'monthly', features_str: '', is_active: true }
}

async function loadTiers() {
  loading.value = true
  try {
    const res = await systemApi.subscriptionTiers()
    const items = res.data.data || []
    tiers.value = items.map((t: any) => ({
      ...t,
      features: Array.isArray(t.features) ? (t.features as unknown as Record<string, unknown>) : t.features,
      features_str: typeof t.features === 'string' ? t.features : JSON.stringify(t.features, null, 2),
    }))
  } catch {
    tiers.value = []
  }
  loading.value = false
}

async function loadSubscribers() {
  try {
    const res = await systemApi.subscriptionSubscribers()
    const items = res.data.data || []
    subscribers.value = items.map((s: any) => ({ ...s, status: s.status || 'active' }))
  } catch {
    subscribers.value = []
  }
}

function editTier(t: SubscriptionTier) {
  editingTier.value = t
  tierForm.value = {
    name: t.name,
    description: t.description || '',
    price: t.price,
    currency: t.currency,
    billing_period: t.billing_period,
    features_str: t.features_str || '',
    is_active: t.is_active,
  }
  showTierModal.value = true
}

async function saveTier() {
  if (!tierForm.value.name.trim()) {
    ;(window as any).$toast?.show('请输入等级名称', 'error')
    return
  }
  if ((tierForm.value.price ?? 0) <= 0) {
    ;(window as any).$toast?.show('价格必须大于零', 'error')
    return
  }
  saving.value = true
  try {
    const features = tierForm.value.features_str
      .split('\n')
      .map((f: string) => f.trim())
      .filter(Boolean)
    const data = {
      name: tierForm.value.name,
      description: tierForm.value.description,
      price: tierForm.value.price,
      currency: tierForm.value.currency,
      billing_period: tierForm.value.billing_period,
      features,
      is_active: tierForm.value.is_active,
    }
    if (editingTier.value) {
      await systemApi.updateSubscriptionTier(editingTier.value.id, data)
      ;(window as any).$toast?.show('等级已更新', 'success')
    } else {
      await systemApi.createSubscriptionTier(data)
      ;(window as any).$toast?.show('等级已创建', 'success')
    }
    showTierModal.value = false
    editingTier.value = null
    resetTierForm()
    loadTiers()
  } catch (e: any) {
    ;(window as any).$toast?.show(e.response?.data?.detail || '保存失败', 'error')
  } finally {
    saving.value = false
  }
}

async function toggleTierActive(t: SubscriptionTier) {
  try {
    await systemApi.updateSubscriptionTier(t.id, { is_active: !t.is_active })
    t.is_active = !t.is_active
    ;(window as any).$toast?.show(t.is_active ? '等级已启用' : '等级已停用', 'success')
  } catch (e: any) {
    ;(window as any).$toast?.show(e.response?.data?.detail || '操作失败', 'error')
  }
}

function confirmDeleteTier(t: SubscriptionTier) {
  deleteTierTarget.value = t
}

async function doDeleteTier() {
  if (!deleteTierTarget.value) return
  deleting.value = true
  try {
    await systemApi.deleteSubscriptionTier(deleteTierTarget.value.id)
    ;(window as any).$toast?.show('等级已删除', 'success')
    deleteTierTarget.value = null
    loadTiers()
  } catch (e: any) {
    ;(window as any).$toast?.show(e.response?.data?.detail || '删除失败', 'error')
  } finally {
    deleting.value = false
  }
}

async function cancelSub(sub: Subscriber) {
  try {
    await systemApi.cancelSubscription({ user_id: sub.user_id })
    ;(window as any).$toast?.show('订阅已取消', 'success')
    sub.status = 'canceled'
  } catch (e: any) {
    ;(window as any).$toast?.show(e.response?.data?.detail || '取消失败', 'error')
  }
}

onMounted(() => {
  loadTiers()
  loadSubscribers()
})
</script>

<style scoped>
.view-page { display: flex; flex-direction: column; gap: 16px; }

/* Tabs */
.tabs-header { display: flex; gap: 4px; border-bottom: 2px solid var(--border); }
.tab-btn {
  padding: 10px 24px; background: none; border: none; border-bottom: 2px solid transparent;
  font-size: 0.95rem; font-weight: 600; color: var(--muted); cursor: pointer;
  transition: all 0.2s; margin-bottom: -2px;
}
.tab-btn:hover { color: var(--fg); }
.tab-btn.active { color: var(--accent); border-bottom-color: var(--accent); }

.page-header { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; }

/* Tier cards */
.tier-cards { display: flex; flex-direction: column; gap: 12px; }
.tier-card {
  border: 1px solid var(--border); border-radius: var(--radius); padding: 20px;
  transition: all 0.2s;
}
.tier-card:hover { box-shadow: 0 4px 16px oklch(0 0 0 / 0.05); }
.tier-card.inactive { opacity: 0.5; }
.tier-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.tier-name { font-weight: 700; font-size: 1.1rem; }
.tier-desc { font-size: 0.84rem; color: var(--muted); margin-top: 2px; }
.tier-price { font-weight: 700; font-size: 1.1rem; color: var(--accent); white-space: nowrap; }
.tier-meta { display: flex; align-items: center; gap: 10px; margin-top: 10px; }
.tier-features { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; }
.feature-tag {
  font-size: 0.75rem; padding: 3px 10px; border-radius: 12px;
  background: oklch(56% 0.12 170 / 0.08); color: var(--accent); font-weight: 500;
}
.tier-actions { display: flex; gap: 6px; margin-top: 14px; padding-top: 14px; border-top: 1px solid var(--border); }

/* Badge */
.badge { font-size: 0.75rem; padding: 3px 10px; border-radius: 10px; font-weight: 600; }
.badge-active { background: oklch(56% 0.12 170 / 0.12); color: #16a34a; }
.badge-inactive { background: var(--border); color: var(--muted); }
.count-badge { font-size: 0.8rem; color: var(--muted); }

/* Table */
.table-wrapper { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
.data-table th {
  text-align: left; padding: 10px 14px; border-bottom: 2px solid var(--border);
  font-weight: 600; color: var(--muted); font-size: 0.8rem;
}
.data-table td { padding: 10px 14px; border-bottom: 1px solid var(--border); }
.mono-cell { font-family: monospace; font-size: 0.82rem; }

/* Forms */
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group label { font-size: 0.82rem; font-weight: 600; color: var(--muted); }
.form-input, .form-textarea, .form-select {
  padding: 10px 14px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  font-size: 0.88rem; font-family: var(--font-body); color: var(--fg);
  background: var(--surface); outline: none; max-width: 400px;
}
.form-textarea { resize: vertical; width: 100%; max-width: 100%; }
.form-select { width: 100%; max-width: 100%; }
.form-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.checkbox-label { display: flex; align-items: center; gap: 8px; font-weight: 400; font-size: 0.88rem; cursor: pointer; }
.checkbox-label input[type="checkbox"] { width: 16px; height: 16px; }

/* Modal */
.modal-overlay { position:fixed; inset:0; background:oklch(0 0 0 / .4); backdrop-filter:blur(4px); z-index:9998; display:flex; align-items:center; justify-content:center; }
.modal-card { background:var(--surface); border-radius:var(--radius-xl); padding:28px; max-width:560px; width:90%; box-shadow:0 16px 64px oklch(0 0 0 / .16); display:flex; flex-direction:column; gap:14px; max-height:90vh; overflow-y:auto; }
.modal-header { display:flex; align-items:center; justify-content:space-between; }
.modal-header h3 { margin:0; }
.modal-close-btn { background:none; border:none; cursor:pointer; font-size:1.4rem; color:var(--muted); }
.modal-footer { display:flex; justify-content:flex-end; gap:10px; margin-top:4px; }
.btn-danger { background:#e53e3e; color:#fff; }
.btn-danger:hover { background:#c53030; }

.btn-sm { padding: 6px 14px; font-size: 0.82rem; }
.btn-xs { padding: 3px 10px; font-size: 0.78rem; }
.btn-ghost { background:transparent; color:var(--muted); }
.btn-ghost:hover { background:oklch(0 0 0 / 0.04); color:var(--fg); }
.btn-danger-sm { color: #ef4444; }

.empty-hint { text-align: center; padding: 48px 24px; color: var(--muted); font-size: 0.9rem; }

@media (max-width: 768px) {
  .form-input, .form-textarea, .form-select { max-width: 100%; width: 100%; }
  .form-row-2 { grid-template-columns: 1fr; }
}
</style>
