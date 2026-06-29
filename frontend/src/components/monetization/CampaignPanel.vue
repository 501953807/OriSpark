<!-- CampaignPanel — 众筹关联管理

Shows crowdfunding campaigns linked to this listing.
Allows creating new campaigns from template.
-->
<template>
  <div class="campaign-panel">
    <div class="panel-header">
      <h4>🚀 众筹关联</h4>
      <button class="btn-add" @click="showNewCampaign = true">+ 创建众筹</button>
    </div>

    <div v-if="loading" class="loading-state">加载中...</div>

    <div v-else-if="!campaigns.length" class="empty-state">
      <span class="empty-icon">🚀</span>
      <p>暂无关联众筹项目</p>
    </div>

    <div v-else class="campaign-list">
      <div v-for="c in campaigns" :key="c.id" class="campaign-item">
        <div class="campaign-info">
          <div class="campaign-title">{{ c.title }}</div>
          <div class="campaign-platform">{{ platformLabel(c.platform) }} · {{ statusLabel(c.status) }}</div>
          <div class="campaign-progress">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: c.progress + '%' }"></div>
            </div>
            <span class="progress-text">¥{{ c.raised }} / ¥{{ c.goal }} ({{ c.progress }}%)</span>
          </div>

          <!-- Reward tiers -->
          <div v-if="c.tiers?.length" class="tiers">
            <div v-for="t in c.tiers" :key="t.name" class="tier-item">
              <span class="tier-name">{{ t.name }}</span>
              <span class="tier-price">¥{{ t.price }}</span>
              <span class="tier-sold">{{ t.sold }}/{{ t.limit || '∞' }}</span>
            </div>
          </div>
        </div>
        <div class="campaign-actions">
          <a :href="c.url" v-if="c.url" target="_blank" rel="noopener" class="ext-link" title="查看项目">🔗</a>
          <button class="ext-btn" @click="editCampaign(c)" title="编辑">✏️</button>
        </div>
      </div>
    </div>

    <!-- New campaign dialog -->
    <div v-if="showNewCampaign" class="modal-overlay" @click.self="showNewCampaign = false">
      <div class="modal">
        <h4>创建众筹项目</h4>

        <div class="form-group">
          <label>选择平台</label>
          <select v-model="form.platform" class="form-select">
            <option value="modian">摩点</option>
            <option value="kickstarter">Kickstarter</option>
            <option value="indiegogo">Indiegogo</option>
            <option value="patreon">Patreon</option>
          </select>
        </div>

        <div class="form-group">
          <label>项目名称</label>
          <input v-model="form.title" class="form-input" placeholder="《山海经》系列限定版画众筹" />
        </div>

        <div class="form-group">
          <label>目标金额</label>
          <input v-model.number="form.goal" type="number" class="form-input" placeholder="80000" />
        </div>

        <!-- Reward tier templates -->
        <div class="form-group">
          <label>奖励档位模板</label>
          <div class="template-grid">
            <button
              v-for="tpl in rewardTemplates"
              :key="tpl.id"
              :class="['tpl-btn', { active: form.template === tpl.id }]"
              @click="form.template = tpl.id"
            >
              {{ tpl.name_zh }}
            </button>
          </div>
        </div>

        <!-- Tier editor -->
        <div class="tiers-editor">
          <div v-for="(tier, i) in form.tiers" :key="i" class="tier-editor-row">
            <input v-model="tier.name" placeholder="档位名" class="tier-input short" />
            <input v-model.number="tier.price" type="number" placeholder="价格" class="tier-input" />
            <input v-model.number="tier.limit" type="number" placeholder="限量" class="tier-input short" />
            <button class="tier-remove" @click="removeTier(i)">✕</button>
          </div>
          <button class="tier-add" @click="addTier">+ 添加档位</button>
        </div>

        <div class="form-actions">
          <button class="btn-cancel" @click="showNewCampaign = false">取消</button>
          <button class="btn-save" @click="createCampaign" :disabled="creating">
            {{ creating ? '创建中...' : '创建' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { supplyApi } from '@/api/supply'

interface Props {
  listingId: string
}
const props = defineProps<Props>()

const emit = defineEmits<{ (e: 'create-campaign', data: any): void }>()

interface Camp {
  id: string
  title: string
  platform: string
  status: string
  goal: number
  raised: number
  progress: number
  url?: string
  tiers?: Array<{ name: string; price: number; sold: number; limit: number }>
}

const campaigns = ref<Camp[]>([])
const loading = ref(false)
const creating = ref(false)
const showNewCampaign = ref(false)

const rewardTemplates = [
  { id: 'rt_basic_3', name_zh: '基础三档' },
  { id: 'rt_pod', name_zh: 'POD预定' },
  { id: 'rt_digital', name_zh: '数字产品' },
  { id: 'rt_fan_builder', name_zh: '粉丝建设' },
]

const form = ref({
  platform: 'modian',
  title: '',
  goal: 0,
  template: 'rt_basic_3',
  tiers: [
    { name: '早鸟支持', price: 99, sold: 0, limit: 100 },
    { name: '标准档', price: 199, sold: 0, limit: 0 },
    { name: '豪华档', price: 399, sold: 0, limit: 20 },
  ],
})

function platformLabel(p: string): string {
  const map: Record<string, string> = {
    modian: '摩点', kickstarter: 'Kickstarter', indiegogo: 'Indiegogo', patreon: 'Patreon',
  }
  return map[p] || p
}

function statusLabel(s: string): string {
  const map: Record<string, string> = {
    draft: '草稿', launching: '进行中', funded: '已达标', successful: '成功',
    failed: '失败', fulfilling: '履约中', completed: '已完成',
  }
  return map[s] || s
}

function addTier() {
  form.value.tiers.push({ name: '', price: 0, sold: 0, limit: 0 })
}

function removeTier(i: number) {
  form.value.tiers.splice(i, 1)
}

async function loadCampaigns() {
  loading.value = true
  try {
    const { data } = await supplyApi.listings({ listing_id: props.listingId })
    // Fetch campaigns and filter by listing_id
    const { data: camps } = await supplyApi.campaigns()
    campaigns.value = (camps as Camp[]).filter((c: any) => c.listing_id === props.listingId)
  } catch {
    campaigns.value = []
  } finally {
    loading.value = false
  }
}

function editCampaign(c: Camp) {
  // Placeholder — expand in future iteration
  alert('编辑功能待实现: ' + c.title)
}

async function createCampaign() {
  creating.value = true
  try {
    await supplyApi.createCampaign({
      ...form.value,
      listing_id: props.listingId,
      status: 'draft',
    })
    showNewCampaign.value = false
    await loadCampaigns()
  } catch {
    // Error toast
  } finally {
    creating.value = false
  }
}

onMounted(loadCampaigns)
</script>

<style scoped>
.campaign-panel { padding: 0 4px; }

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

.campaign-list { display: flex; flex-direction: column; gap: 8px; }

.campaign-item {
  display: flex; justify-content: space-between; align-items: flex-start;
  padding: 12px 14px; border: 1px solid var(--border);
  border-radius: var(--radius-sm); background: var(--surface);
}

.campaign-title { font-weight: 700; font-size: .88rem; }
.campaign-platform { font-size: .72rem; color: var(--muted); margin-top: 2px; }

.campaign-progress { margin-top: 8px; }

.progress-bar {
  height: 6px; background: var(--muted-bg); border-radius: 3px; overflow: hidden;
}

.progress-fill {
  height: 100%; background: var(--accent); border-radius: 3px;
  transition: width 0.3s;
}

.progress-text {
  display: block; font-size: .7rem; color: var(--muted); margin-top: 2px;
}

.tiers { margin-top: 8px; display: flex; flex-direction: column; gap: 4px; }

.tier-item {
  display: flex; gap: 8px; font-size: .72rem;
  padding: 2px 0; border-bottom: 1px solid var(--border);
}

.tier-name { flex: 1; font-weight: 600; }
.tier-price { color: var(--accent); font-weight: 700; }
.tier-sold { color: var(--muted); }

.campaign-actions { display: flex; gap: 4px; flex-shrink: 0; }
.ext-link, .ext-btn {
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
  width: 520px; max-width: 90vw; max-height: 80vh; overflow-y: auto;
}

.modal h4 { margin: 0 0 16px; }
.form-group { margin-bottom: 12px; }
.form-group label { display: block; font-size: .78rem; margin-bottom: 4px; color: var(--muted); }

.form-select, .form-input {
  width: 100%; padding: 6px 10px; border: 1px solid var(--border);
  border-radius: var(--radius-sm); font-size: .85rem; background: var(--surface);
}

.template-grid { display: flex; gap: 6px; flex-wrap: wrap; }
.tpl-btn {
  padding: 4px 10px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  background: var(--surface); cursor: pointer; font-size: .75rem;
}
.tpl-btn.active { border-color: var(--accent); background: oklch(56% 0.12 170 / .08); }

.tiers-editor { margin-top: 8px; display: flex; flex-direction: column; gap: 6px; }

.tier-editor-row {
  display: flex; gap: 6px; align-items: center;
}

.tier-input {
  flex: 1; padding: 4px 8px; border: 1px solid var(--border);
  border-radius: var(--radius-sm); font-size: .78rem; background: var(--surface);
}
.tier-input.short { flex: 0.6; }

.tier-remove {
  background: none; border: 1px solid var(--border); border-radius: var(--radius-sm);
  cursor: pointer; font-size: .72rem; padding: 4px 6px;
}

.tier-add {
  background: none; border: 1px dashed var(--border); border-radius: var(--radius-sm);
  cursor: pointer; font-size: .75rem; color: var(--accent); padding: 4px;
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
