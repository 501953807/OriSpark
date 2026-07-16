<template>
  <div class="insurance-view">
    <LoadingSpinner v-if="store.loading" text="加载中..." />
    <template v-else>
      <h2>版权保险市场</h2>
      <p class="subtitle">为您的作品选择合适的版权保障方案</p>

      <!-- Tab 切换 -->
      <div class="tabs">
        <button :class="['tab', { active: tab === 'products' }]" @click="tab = 'products'">保险产品</button>
        <button :class="['tab', { active: tab === 'estimate' }]" @click="tab = 'estimate'">保费估算</button>
        <button :class="['tab', { active: tab === 'policies' }]" @click="tab = 'policies'">我的保单</button>
      </div>

      <!-- 保险产品列表 -->
      <div v-if="tab === 'products'" class="section">
        <div class="filter-bar">
          <select v-model="filterCategory" @change="filterByCategory()">
            <option value="">全部分类</option>
            <option v-for="c in categories" :key="c" :value="c">{{ categoryLabel(c) }}</option>
          </select>
          <select v-model="filterTier" @change="filterByTier()">
            <option value="">全部层级</option>
            <option value="basic">基础版</option>
            <option value="advanced">进阶版</option>
            <option value="pro">专业版</option>
          </select>
        </div>

        <div class="product-grid">
          <div v-for="p in filteredProducts" :key="p.id" class="product-card">
            <div class="product-tier" :class="'tier-' + p.tier">{{ tierLabel(p.tier) }}</div>
            <h3>{{ p.name_zh }}</h3>
            <p class="desc">{{ p.coverage_description }}</p>
            <div class="price-range">
              ¥{{ p.annual_min_yuan.toLocaleString() }} - ¥{{ p.annual_max_yuan.toLocaleString() }}/年
            </div>
            <div v-if="p.max_coverage_yuan" class="max-coverage">
              最高赔付: ¥{{ p.max_coverage_yuan.toLocaleString() }}
            </div>
            <button class="btn-primary" @click="handlePurchase(p)">立即投保</button>
          </div>
        </div>
      </div>

      <!-- 保费估算器 -->
      <div v-if="tab === 'estimate'" class="section">
        <div class="estimate-form">
          <div class="form-group">
            <label>创作者类型</label>
            <select v-model="estimateForm.creator_type">
              <option v-for="t in creatorTypes" :key="t" :value="t">{{ t }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>作品数量: {{ estimateForm.work_count }}</label>
            <input type="range" min="1" :max="estimateMax" v-model.number="estimateForm.work_count" />
          </div>
          <div class="form-group">
            <label>风险等级</label>
            <select v-model="estimateForm.risk_level">
              <option value="low">低</option>
              <option value="medium">中</option>
              <option value="high">高</option>
            </select>
          </div>
          <div class="form-group">
            <label>保险类别（多选）</label>
            <div class="checkbox-group">
              <label v-for="c in categories" :key="c">
                <input type="checkbox" :value="c" v-model="estimateForm.categories" />
                {{ categoryLabel(c) }}
              </label>
            </div>
          </div>
          <button class="btn-primary" @click="doEstimate">估算保费</button>
        </div>

        <div v-if="store.estimate" class="estimate-result">
          <h3>推荐方案</h3>
          <div class="result-cards">
            <div v-for="r in store.estimate.recommended_products" :key="r.tier"
                 class="result-card" :class="{ best: r.tier === store.estimate!.tier }">
              <div class="result-tier">{{ tierLabel(r.tier) }}</div>
              <div class="result-premium">¥{{ r.estimated_premium.toLocaleString() }}/年</div>
              <div v-if="r.products.length > 0" class="result-products">
                <div v-for="rp in r.products" :key="rp.id" class="mini-product">
                  {{ rp.name_zh }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 我的保单 -->
      <div v-if="tab === 'policies'" class="section">
        <div v-if="store.policies.length === 0" class="empty-state">
          暂无保单，请先选择保险产品
        </div>
        <div v-else class="policy-list">
          <div v-for="pol in store.policies" :key="pol.id" class="policy-card">
            <div class="policy-status" :class="'status-' + pol.status">{{ statusLabel(pol.status) }}</div>
            <h3>{{ pol.product_name }}</h3>
            <div class="policy-info">
              <span>¥{{ pol.annual_premium_yuan.toLocaleString() }}/年</span>
              <span>{{ pol.start_date }} ~ {{ pol.end_date }}</span>
            </div>
            <button class="btn-small" @click="openClaim(pol)">提交理赔</button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useInsuranceStore } from '@/stores/useInsuranceStore'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const store = useInsuranceStore()
const tab = ref('products')
const filterCategory = ref('')
const filterTier = ref('')

const categories = ['training_indemnity', 'style_copy', 'deepfake', 'unintentional_infringement', 'voice_portrait_theft']
const creatorTypes = ['illustrator', 'photographer', 'musician', 'writer', 'video_creator', 'craftsman']
const estimateMax = 1000

const estimateForm = ref({
  creator_type: 'illustrator',
  work_count: 100,
  risk_level: 'medium',
  categories: [] as string[],
})

const filteredProducts = computed(() => {
  let prods = store.products
  if (filterCategory.value) prods = prods.filter(p => p.category === filterCategory.value)
  if (filterTier.value) prods = prods.filter(p => p.tier === filterTier.value)
  return prods
})

function categoryLabel(key: string): string {
  const map: Record<string, string> = {
    training_indemnity: '训练数据赔偿险',
    style_copy: '风格模仿覆盖险',
    deepfake: '深度伪造保护险',
    unintentional_infringement: '无意侵权险',
    voice_portrait_theft: '声音肖像盗用险',
  }
  return map[key] || key
}

function tierLabel(t: string): string {
  return { basic: '基础版', advanced: '进阶版', pro: '专业版' }[t] || t
}

function statusLabel(s: string): string {
  return { pending: '待生效', active: '生效中', expired: '已过期', cancelled: '已取消', claiming: '理赔中' }[s] || s
}

function filterByCategory() { store.loadProducts(filterCategory.value, filterTier.value) }
function filterByTier() { store.loadProducts(filterCategory.value, filterTier.value) }

async function doEstimate() {
  await store.loadEstimate(estimateForm.value)
}

function handlePurchase(product: any) {
  alert(`投保功能对接外部保险公司 API: ${product.name_zh}`)
}

function openClaim(policy: any) {
  alert(`理赔申请: ${policy.product_name}`)
}

// Initial load
store.loadProducts()
</script>

<style scoped>
.insurance-view {
  max-width: 960px;
  margin: 0 auto;
}
h2 { font-size: 1.4rem; margin-bottom: 4px; }
.subtitle { color: var(--muted); font-size: 0.85rem; margin-bottom: 24px; }

.tabs { display: flex; gap: 8px; margin-bottom: 20px; }
.tab {
  padding: 8px 16px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: transparent;
  cursor: pointer;
  font-size: 0.9rem;
}
.tab.active { background: var(--accent); color: white; border-color: var(--accent); }

.section { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; }

.filter-bar { display: flex; gap: 12px; margin-bottom: 16px; }
.filter-bar select {
  padding: 6px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg);
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
.product-card {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  position: relative;
}
.product-tier {
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
}
.tier-basic { background: #e0f2fe; color: #0369a1; }
.tier-advanced { background: #fef3c7; color: #92400e; }
.tier-pro { background: #fce7f3; color: #9d174d; }
.product-card h3 { margin: 0 0 8px; font-size: 1rem; }
.desc { color: var(--muted); font-size: 0.8rem; margin: 0 0 12px; }
.price-range { font-weight: 700; font-size: 1.1rem; margin-bottom: 4px; }
.max-coverage { font-size: 0.8rem; color: var(--muted); margin-bottom: 12px; }

.btn-primary {
  background: var(--accent);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  width: 100%;
}
.btn-small {
  background: transparent;
  color: var(--accent);
  border: 1px solid var(--accent);
  padding: 4px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 0.8rem;
}

.estimate-form { max-width: 480px; }
.form-group { margin-bottom: 16px; }
.form-group label { display: block; font-size: 0.85rem; margin-bottom: 4px; font-weight: 600; }
.form-group select, .form-group input[type="range"] { width: 100%; }
.checkbox-group { display: flex; flex-wrap: wrap; gap: 8px; }
.checkbox-group label { font-size: 0.85rem; display: flex; align-items: center; gap: 4px; }

.result-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; margin-top: 16px; }
.result-card {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  text-align: center;
}
.result-card.best { border-color: var(--accent); box-shadow: 0 0 0 2px var(--accent); }
.result-tier { font-weight: 700; margin-bottom: 8px; }
.result-premium { font-size: 1.2rem; font-weight: 700; margin-bottom: 8px; }
.result-products { font-size: 0.75rem; color: var(--muted); text-align: left; }
.mini-product { padding: 2px 0; }

.policy-list { display: grid; gap: 12px; }
.policy-card {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  position: relative;
}
.policy-status {
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 700;
}
.status-active { background: #dcfce7; color: #166534; }
.status-pending { background: #fef3c7; color: #92400e; }
.policy-info { display: flex; justify-content: space-between; font-size: 0.8rem; color: var(--muted); margin-top: 8px; }

.empty-state { text-align: center; padding: 48px; color: var(--muted); }
</style>
