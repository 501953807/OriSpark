<template>
  <div class="guidelines animate-fade-in">
    <DisclaimerBanner
      mode="banner"
      title="信息参考声明"
      :messages="['本工具仅提供信息指引，不构成法律建议（声明 #2）。IP登记指引覆盖中国/美国/欧盟/WIPO主要辖区，不包括所有国家/地区（声明 #7）。所有申请须由您自行向官方机构提交。']"
    />

    <!-- P2.4: 辖区选择器 -->
    <div class="jurisdiction-bar">
      <button
        v-for="j in globalJurisdictions"
        :key="j.code"
        :class="['jur-btn', { active: modelValue === j.code }]"
        @click="$emit('update:modelValue', j.code)"
      >
        <span class="jur-flag">{{ j.flag }}</span>
        <span class="jur-label">{{ j.label }}</span>
      </button>
    </div>

    <!-- 加载当前辖区指引 -->
    <template v-if="currentGuidelines">
      <!-- Copyright guideline card -->
      <div v-if="currentGuidelines.copyright" class="guideline-card card">
        <div class="gl-header" @click="$emit('toggle-collapse')" style="cursor:pointer">
          <span class="gl-icon">©️</span>
          <div>
            <h3>{{ currentGuidelines.copyright?.title || '著作权登记指引' }}</h3>
            <p class="gl-subtitle">{{ currentGuidelines.copyright?.description || '' }}</p>
          </div>
          <span class="gl-toggle">{{ guidelineCollapsed ? '▶' : '▼' }}</span>
        </div>
        <div v-show="!guidelineCollapsed" class="gl-body">
          <div v-if="currentGuidelines.copyright?.forms" class="gl-section">
            <h4>📝 申请表格类型</h4>
            <div class="fee-grid">
              <div v-for="(desc, code) in currentGuidelines.copyright.forms" :key="code" class="fee-chip">
                <strong>{{ code }}</strong>
                <span>{{ desc }}</span>
              </div>
            </div>
          </div>
          <div class="gl-section">
            <h4>📋 所需材料</h4>
            <div class="materials-list">
              <div v-for="m in currentGuidelines.copyright?.materials || []" :key="m.name" class="material-item" :class="{ required: m.required }">
                <span class="material-check">{{ m.required ? '✓' : '○' }}</span>
                <div>
                  <span class="material-name">{{ m.name }}</span>
                  <span class="material-desc">{{ m.description }}</span>
                  <span v-if="m.can_prefill" class="material-tag">🪄 可自动预填</span>
                </div>
              </div>
            </div>
          </div>
          <div class="gl-section">
            <h4>📝 办理流程</h4>
            <div class="process-flow">
              <div v-for="p in currentGuidelines.copyright?.process || []" :key="p.step" class="process-step">
                <span class="step-num">{{ p.step }}</span>
                <div>
                  <strong>{{ p.name }}</strong>
                  <p>{{ p.description }}</p>
                  <small>⏱ {{ p.duration }}</small>
                </div>
              </div>
            </div>
          </div>
          <div class="gl-meta">
            <span v-if="currentGuidelines.copyright?.platform_url">🏛️ <a :href="currentGuidelines.copyright.platform_url" target="_blank">{{ currentGuidelines.copyright.institution }}</a></span>
            <span v-else>🏛️ {{ currentGuidelines.copyright.institution }}</span>
            <span v-if="currentGuidelines.copyright?.legal_basis">📜 {{ currentGuidelines.copyright.legal_basis }}</span>
            <span v-if="currentGuidelines.copyright?.estimated_duration">⏱️ {{ currentGuidelines.copyright.estimated_duration }}</span>
            <span v-if="currentGuidelines.copyright?.validity">🔄 {{ currentGuidelines.copyright.validity }}</span>
          </div>
          <div v-if="currentGuidelines.copyright?.fee" class="gl-fees">
            <h4>💰 费用参考</h4>
            <div class="fee-grid">
              <div class="fee-chip" v-for="(fee, key) in currentGuidelines.copyright.fee" :key="key">
                <strong>{{ keyLabels[key] || key }}</strong>
                <span>{{ fee }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Trademark guideline card -->
      <div v-if="currentGuidelines.trademark" class="guideline-card card">
        <div class="gl-header">
          <span class="gl-icon">™️</span>
          <div>
            <h3>{{ currentGuidelines.trademark?.title || '商标注册指引' }}</h3>
            <p class="gl-subtitle">{{ currentGuidelines.trademark?.description || '' }}</p>
          </div>
        </div>
        <div class="gl-body">
          <div class="gl-warning">⚠️ {{ currentGuidelines.trademark.disclaimer }}</div>
          <div v-if="currentGuidelines.trademark?.note_personal" class="gl-warning" style="background:rgba(129, 129, 133, 0.08);color:var(--red);">
            {{ currentGuidelines.trademark.note_personal }}
          </div>
          <div v-if="currentGuidelines.trademark?.note_agent" class="gl-warning" style="background:rgba(129, 129, 133, 0.08);color:var(--red);">
            {{ currentGuidelines.trademark.note_agent }}
          </div>
          <div v-if="currentGuidelines.trademark?.note_language" class="gl-section">
            <h4>🌐 语言要求</h4>
            <p style="font-size:.85rem;color:var(--muted);margin:0">{{ currentGuidelines.trademark.note_language }}</p>
          </div>
          <div v-if="currentGuidelines.trademark?.central_attack_risk" class="gl-warning" style="background:rgba(129, 129, 133, 0.08);color:var(--red);">
            {{ currentGuidelines.trademark.central_attack_risk }}
          </div>
          <div v-if="currentGuidelines.trademark?.prerequisites" class="gl-section">
            <h4>⚠️ 前提条件</h4>
            <p style="font-size:.85rem;color:var(--muted);margin:0">{{ currentGuidelines.trademark.prerequisites }}</p>
          </div>
          <div v-if="currentGuidelines.trademark?.member_countries" class="gl-section">
            <h4>🇪🇺 覆盖国家 ({{ currentGuidelines.trademark.member_countries.length }}个)</h4>
            <div class="country-grid">
              <span v-for="c in currentGuidelines.trademark.member_countries" :key="c" class="country-chip">{{ c }}</span>
            </div>
          </div>
          <div v-if="currentGuidelines.trademark?.member_count" class="gl-section">
            <h4>🌐 覆盖范围</h4>
            <p style="font-size:.85rem;color:var(--muted);margin:0">覆盖 {{ currentGuidelines.trademark.member_count }} 个缔约方</p>
          </div>
          <div v-if="currentGuidelines.categories || globalCategories" class="gl-section">
            <h4>📂 文创常用类别</h4>
            <div class="category-grid">
              <div v-for="(desc, code) in (currentGuidelines.categories || globalCategories)" :key="code" class="category-chip" @click="$emit('select-class', Number(code))">
                <strong>第{{ code }}类</strong>
                <span>{{ desc }}</span>
              </div>
            </div>
          </div>
          <div v-if="currentGuidelines.trademark?.fee_examples" class="gl-section">
            <h4>💰 费用示例</h4>
            <div class="fee-example-list">
              <div v-for="(ex, idx) in currentGuidelines.trademark.fee_examples" :key="idx" class="fee-example-item">
                <div class="fee-example-header">
                  <strong>{{ ex.scenario }}</strong>
                  <span class="fee-total">{{ ex.total }}</span>
                </div>
                <p class="fee-example-breakdown">{{ ex.breakdown }}</p>
              </div>
            </div>
          </div>
          <div v-if="typeof currentGuidelines.trademark?.fee === 'string'" class="gl-section">
            <h4>💰 费用</h4>
            <p style="font-size:.85rem;margin:0">{{ currentGuidelines.trademark.fee }}</p>
          </div>
          <div v-else-if="currentGuidelines.trademark?.fee && typeof currentGuidelines.trademark.fee === 'object'" class="gl-fees">
            <h4>💰 费用参考</h4>
            <div class="fee-grid">
              <div class="fee-chip" v-for="(fee, key) in currentGuidelines.trademark.fee" :key="key">
                <strong>{{ trademarkFeeLabels[key] || keyLabels[key] || key }}</strong>
                <span>{{ fee }}</span>
              </div>
            </div>
          </div>
          <div class="gl-section">
            <h4>📋 所需材料</h4>
            <div class="materials-list">
              <div v-for="m in currentGuidelines.trademark?.materials || []" :key="m.name" class="material-item" :class="{ required: m.required }">
                <span class="material-check">{{ m.required ? '✓' : '○' }}</span>
                <div>
                  <span class="material-name">{{ m.name }}</span>
                  <span class="material-desc">{{ m.description }}</span>
                  <span v-if="m.can_prefill" class="material-tag">🪄 可自动预填</span>
                </div>
              </div>
            </div>
          </div>
          <div class="gl-section">
            <h4>📝 办理流程</h4>
            <div class="process-flow">
              <div v-for="p in currentGuidelines.trademark?.process || []" :key="p.step" class="process-step">
                <span class="step-num">{{ p.step }}</span>
                <div>
                  <strong>{{ p.name }}</strong>
                  <p>{{ p.description }}</p>
                  <small>⏱ {{ p.duration }}</small>
                </div>
              </div>
            </div>
          </div>
          <div class="gl-meta">
            <span v-if="currentGuidelines.trademark?.platform_url">🏛️ <a :href="currentGuidelines.trademark.platform_url" target="_blank">{{ currentGuidelines.trademark.institution }}</a></span>
            <span v-else>🏛️ {{ currentGuidelines.trademark.institution }}</span>
            <span v-if="currentGuidelines.trademark?.legal_basis">📜 {{ currentGuidelines.trademark.legal_basis }}</span>
            <span v-if="currentGuidelines.trademark?.estimated_duration">⏱️ {{ currentGuidelines.trademark.estimated_duration }}</span>
            <span v-if="currentGuidelines.trademark?.validity">🔄 {{ currentGuidelines.trademark.validity }}</span>
          </div>
          <!-- 商标近似检索入口 -->
          <div class="gl-section" style="margin-top:16px">
            <h4>🔍 商标近似检索</h4>
            <p style="font-size:.82rem;color:var(--muted);margin:0 0 12px">申请前建议检索商标数据库，排查近似商标风险</p>
            <div class="trademark-search-box">
              <input v-model="similarityQuery" class="form-input" placeholder="输入商标名称或图样描述..." style="max-width:300px" />
              <select v-model="similarityClass" class="form-input" style="max-width:120px">
                <option value="">全类别</option>
                <option v-for="c in trademarkClasses" :key="c" :value="c">第{{ c }}类</option>
              </select>
              <button class="btn btn-primary btn-sm" @click="doTrademarkSearch" :disabled="!similarityQuery.trim()">
                🔍 检索
              </button>
              <button class="btn btn-secondary btn-sm" @click="similarityQuery = ''; similarityResult = null">清除</button>
            </div>
            <div v-if="similarityResult" class="similarity-result card" style="margin-top:12px;padding:16px">
              <div class="similarity-summary">
                <span class="sim-count">找到 <strong>{{ similarityResult.total }}</strong> 条近似结果</span>
                <span class="sim-risk" :class="similarityResult.risk_level">{{ similarityResult.risk_label }}</span>
              </div>
              <div v-if="similarityResult.results?.length" class="sim-list">
                <div v-for="r in similarityResult.results.slice(0, 5)" :key="r.id" class="sim-item">
                  <span class="sim-name">{{ r.trademark_name }}</span>
                  <span class="sim-class">第{{ r.class_no }}类</span>
                  <span :class="['sim-score', r.score >= 80 ? 'high' : r.score >= 50 ? 'medium' : 'low']">相似度 {{ r.score }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Design patent guideline card -->
      <div v-if="currentGuidelines.design_patent" class="guideline-card card">
        <div class="gl-header">
          <span class="gl-icon">🎨</span>
          <div>
            <h3>{{ currentGuidelines.design_patent?.title || '外观设计指引' }}</h3>
            <p class="gl-subtitle">{{ currentGuidelines.design_patent?.description || '' }}</p>
          </div>
        </div>
        <div class="gl-body">
          <div class="gl-warning">⚠️ {{ currentGuidelines.design_patent.disclaimer }}</div>
          <div v-if="currentGuidelines.design_patent?.member_count" class="gl-section">
            <h4>🌐 覆盖范围</h4>
            <p style="font-size:.85rem;color:var(--muted);margin:0">覆盖 {{ currentGuidelines.design_patent.member_count }} 个缔约方</p>
          </div>
          <div v-if="currentGuidelines.design_patent?.fee_examples" class="gl-section">
            <h4>💰 费用示例</h4>
            <div class="fee-example-list">
              <div v-for="(ex, idx) in currentGuidelines.design_patent.fee_examples" :key="idx" class="fee-example-item">
                <div class="fee-example-header">
                  <strong>{{ ex.scenario }}</strong>
                  <span class="fee-total">{{ ex.total }}</span>
                </div>
                <p class="fee-example-breakdown">{{ ex.breakdown }}</p>
              </div>
            </div>
          </div>
          <div v-if="typeof currentGuidelines.design_patent?.fee === 'string'" class="gl-section">
            <h4>💰 费用</h4>
            <p style="font-size:.85rem;margin:0">{{ currentGuidelines.design_patent.fee }}</p>
          </div>
          <div v-else-if="currentGuidelines.design_patent?.fee && typeof currentGuidelines.design_patent.fee === 'object'" class="gl-fees">
            <h4>💰 费用参考</h4>
            <div class="fee-grid">
              <div class="fee-chip" v-for="(fee, key) in currentGuidelines.design_patent.fee" :key="key">
                <strong>{{ designPatentFeeLabels[key] || keyLabels[key] || key }}</strong>
                <span>{{ fee }}</span>
              </div>
            </div>
          </div>
          <div v-if="currentGuidelines.design_patent?.materials" class="gl-section">
            <h4>📋 所需材料</h4>
            <div class="materials-list">
              <div v-for="m in currentGuidelines.design_patent.materials" :key="m.name" class="material-item" :class="{ required: m.required }">
                <span class="material-check">{{ m.required ? '✓' : '○' }}</span>
                <div>
                  <span class="material-name">{{ m.name }}</span>
                  <span class="material-desc">{{ m.description }}</span>
                  <span v-if="m.can_prefill" class="material-tag">🪄 可自动预填</span>
                </div>
              </div>
            </div>
          </div>
          <div v-if="currentGuidelines.design_patent?.process" class="gl-section">
            <h4>📝 办理流程</h4>
            <div class="process-flow">
              <div v-for="p in currentGuidelines.design_patent.process" :key="p.step" class="process-step">
                <span class="step-num">{{ p.step }}</span>
                <div>
                  <strong>{{ p.name }}</strong>
                  <p>{{ p.description }}</p>
                  <small>⏱ {{ p.duration }}</small>
                </div>
              </div>
            </div>
          </div>
          <div class="gl-meta">
            <span v-if="currentGuidelines.design_patent?.platform_url">🏛️ <a :href="currentGuidelines.design_patent.platform_url" target="_blank">{{ currentGuidelines.design_patent.institution }}</a></span>
          </div>
        </div>
      </div>

      <!-- EUIPO SME Fund card -->
      <div v-if="currentGuidelines.sme_fund" class="guideline-card card" style="border-left:4px solid rgba(99,102,241, 0.06)">
        <div class="gl-header">
          <span class="gl-icon">💶</span>
          <div>
            <h3>{{ currentGuidelines.sme_fund.title }}</h3>
            <p class="gl-subtitle">{{ currentGuidelines.sme_fund.description }}</p>
          </div>
        </div>
        <div class="gl-body">
          <div class="gl-warning">⚠️ {{ currentGuidelines.sme_fund.disclaimer }}</div>
          <div class="gl-section">
            <h4>✅ 资格条件</h4>
            <p style="font-size:.85rem;color:var(--muted);margin:0 0 8px"><strong>定义：</strong>{{ currentGuidelines.sme_fund.eligibility.definition }}</p>
            <ul style="padding-left:20px;font-size:.82rem;color:var(--muted);margin:0">
              <li v-for="(req, i) in currentGuidelines.sme_fund.eligibility.requirements" :key="i">{{ req }}</li>
            </ul>
          </div>
          <div class="gl-section">
            <h4>❌ 不适用对象</h4>
            <ul style="padding-left:20px;font-size:.82rem;color:var(--red);margin:0">
              <li v-for="(item, i) in currentGuidelines.sme_fund.eligibility.not_eligible" :key="i">{{ item }}</li>
            </ul>
          </div>
          <div class="gl-section">
            <h4>💰 资助范围</h4>
            <div class="sme-coverage">
              <div class="sme-cov-item">
                <strong>商标 {{ currentGuidelines.sme_fund.coverage.trademark.reimbursement_rate }}</strong>
                <span>报销率, 资助券{{ currentGuidelines.sme_fund.coverage.trademark.voucher_1 }}</span>
              </div>
              <div class="sme-cov-item">
                <strong>外观设计 {{ currentGuidelines.sme_fund.coverage.design.reimbursement_rate }}</strong>
                <span>报销率, 资助券{{ currentGuidelines.sme_fund.coverage.design.voucher }}</span>
              </div>
            </div>
          </div>
          <div class="gl-section">
            <h4>📝 申请流程</h4>
            <div class="process-flow">
              <div v-for="p in currentGuidelines.sme_fund.application_process" :key="p.step" class="process-step">
                <span class="step-num">{{ p.step }}</span>
                <div>
                  <strong>{{ p.name }}</strong>
                  <p>{{ p.description }}</p>
                  <small>⏱ {{ p.duration }}</small>
                </div>
              </div>
            </div>
          </div>
          <div class="gl-section">
            <h4>💡 案例参考</h4>
            <div class="sme-example card" style="padding:16px;background:var(--m-bg-subtle)">
              <p style="margin:0 0 8px"><strong>{{ currentGuidelines.sme_fund.example.scenario }}</strong></p>
              <div class="fee-grid">
                <div class="fee-chip"><strong>总费用</strong><span>{{ currentGuidelines.sme_fund.example.total_fee }}</span></div>
                <div class="fee-chip"><strong>SME Fund 承担</strong><span style="color:var(--accent)">{{ currentGuidelines.sme_fund.example.sme_fund_covers }}</span></div>
                <div class="fee-chip"><strong>您仅需支付</strong><span style="color:var(--red)">{{ currentGuidelines.sme_fund.example.your_cost }}</span></div>
              </div>
            </div>
          </div>
          <div v-if="currentGuidelines.sme_fund.tips" class="gl-section">
            <h4>💡 小贴士</h4>
            <ul style="padding-left:20px;font-size:.82rem;color:var(--muted);margin:0">
              <li v-for="(tip, i) in currentGuidelines.sme_fund.tips" :key="i">{{ tip }}</li>
            </ul>
          </div>
          <p class="sme-key-dates" style="font-size:.82rem;color:var(--orange);margin:8px 0 0">
            ⏰ {{ currentGuidelines.sme_fund.key_dates }}
          </p>
          <a v-if="currentGuidelines.sme_fund.official_url" :href="currentGuidelines.sme_fund.official_url" target="_blank" class="btn btn-secondary" style="margin-top:8px">🔗 访问 SME Fund 官网</a>
        </div>
      </div>

      <!-- Fallback -->
      <div v-if="!hasGuidelinesContent" class="card" style="padding:32px;text-align:center;color:var(--muted)">
        📖 该辖区指引数据正在建设中...
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import DisclaimerBanner from '@/components/common/DisclaimerBanner.vue'

const props = defineProps<{
  modelValue: string
  currentGuidelines: any
  hasGuidelinesContent: boolean
  globalCategories: any
  globalJurisdictions: Array<{ code: string; flag: string; label: string }>
  guidelineCollapsed: boolean
  keyLabels: Record<string, string>
  trademarkFeeLabels: Record<string, string>
  designPatentFeeLabels: Record<string, string>
}>()

defineEmits<{
  'update:modelValue': [jurisdiction: string]
  'toggle-collapse': []
  'select-class': [classNo: number]
}>()

const similarityQuery = ref('')
const similarityClass = ref('')
const similarityResult = ref<any>(null)
const trademarkClasses = Array.from({ length: 45 }, (_, i) => String(i + 1))

async function doTrademarkSearch() {
  if (!similarityQuery.value.trim()) return
  try {
    const { iprApi } = await import('@/api/ipr')
    const params: any = { query: similarityQuery.value.trim() }
    if (similarityClass.value) params.class_no = similarityClass.value
    const res = await iprApi.similaritySearch(params)
    similarityResult.value = res.data.data
  } catch {
    similarityResult.value = { total: 0, risk_level: 'none', risk_label: '查询失败', results: [] }
  }
}
</script>

<style scoped>
/* ── Guidelines ──────────────────────────────── */
.guidelines { display:flex; flex-direction:column; gap:16px; }
.guideline-card { padding:24px; }
.gl-header { display:flex; align-items:center; gap:12px; margin-bottom:16px; }
.gl-icon { font-size:2rem; }
.gl-header h3 { margin:0; font-size:1.1rem; }
.gl-subtitle { color:var(--muted); font-size:.85rem; margin:4px 0 0; }
.gl-toggle { font-size:.75rem; color:var(--muted); transition:transform .15s; margin-left:auto; }
.gl-body { display:flex; flex-direction:column; gap:16px; }
.gl-section h4 { font-size:.9rem; margin:0 0 8px; }
.gl-section ul { padding-left:20px; font-size:.85rem; color:var(--muted); line-height:1.8; }
.gl-meta { display:flex; gap:16px; font-size:.82rem; color:var(--muted); flex-wrap:wrap; align-items:center; }
.gl-meta a { color:var(--accent); }
.gl-warning { padding:12px; background:rgba(129, 129, 133, 0.08); border-radius:var(--m-radius-sm); font-size:.82rem; color:var(--orange); }
.gl-fees { margin-top:4px; }
.gl-fees h4 { font-size:.9rem; margin:0 0 8px; }
.fee-grid { display:flex; gap:8px; flex-wrap:wrap; }
.fee-chip { padding:6px 12px; background:var(--surface); border:1px solid var(--border); border-radius:var(--m-radius-sm); font-size:.8rem; display:flex; gap:6px; align-items:center; }
.fee-chip strong { color:var(--accent); white-space:nowrap; }
.category-grid { display:grid; grid-template-columns:1fr 1fr; gap:8px; }
.category-chip { padding:8px 12px; background:var(--m-bg-subtle); border-radius:var(--m-radius-sm); font-size:.8rem; cursor:pointer; transition:all .15s; }
.category-chip:hover { background:rgba(2,132,199, 0.06); }
.category-chip strong { color:var(--accent); }

.materials-list { display:flex; flex-direction:column; gap:8px; }
.material-item { display:flex; gap:10px; padding:8px; border-radius:var(--m-radius-sm); background:var(--surface); border:1px solid var(--border); }
.material-item.required { border-left:3px solid var(--red); }
.material-check { font-size:.9rem; font-weight:700; color:var(--red); min-width:20px; }
.material-name { font-weight:600; font-size:.84rem; display:block; }
.material-desc { font-size:.78rem; color:var(--muted); display:block; margin-top:2px; }
.material-tag { font-size:.72rem; background:rgba(86,202,0,0.1); color:var(--accent); padding:1px 6px; border-radius:var(--m-radius-xs, 6px); margin-left:6px; }

.process-flow { display:flex; flex-direction:column; gap:10px; }
.process-step { display:flex; gap:12px; padding:10px; border-radius:var(--m-radius-sm); background:var(--surface); border:1px solid var(--border); }
.step-num { width:28px; height:28px; display:flex; align-items:center; justify-content:center; background:var(--accent); color:#fff; border-radius:50%; font-size:.78rem; font-weight:700; flex-shrink:0; }
.process-step strong { font-size:.85rem; display:block; }
.process-step p { font-size:.78rem; color:var(--muted); margin:4px 0 2px; }
.process-step small { font-size:.72rem; color:var(--muted); }

/* ── P2.4: Jurisdiction Bar ───────────────────── */
.jurisdiction-bar { display:flex; gap:6px; flex-wrap:wrap; margin-bottom:4px; }
.jur-btn { padding:8px 18px; border-radius:100px; font-size:.82rem; font-weight:600; cursor:pointer; border:2px solid var(--border); background:var(--surface); color:var(--muted); font-family:Inter; transition:all .2s; display:flex; align-items:center; gap:6px; }
.jur-btn:hover { border-color:var(--accent); color:var(--accent); }
.jur-btn.active { background:var(--accent); color:#fff; border-color:var(--accent); }
.jur-flag { font-size:1rem; }
.jur-label { font-size:.82rem; }

/* ── Country grid (EU) ──────────────────── */
.country-grid { display:flex; flex-wrap:wrap; gap:6px; }
.country-chip { padding:3px 10px; background:rgba(124, 124, 129, 0.08); border:1px solid rgba(124, 124, 129, 0.2); border-radius:100px; font-size:.75rem; color:var(--blue); }

/* ── Fee examples ──────────────────────── */
.fee-example-list { display:flex; flex-direction:column; gap:8px; }
.fee-example-item { padding:10px 14px; background:var(--surface); border:1px solid var(--border); border-radius:var(--m-radius-sm); }
.fee-example-header { display:flex; justify-content:space-between; align-items:center; font-size:.84rem; }
.fee-total { font-weight:800; color:var(--accent); }
.fee-example-breakdown { font-size:.76rem; color:var(--muted); margin:4px 0 0; }

/* ── SME Fund ──────────────────────────────── */
.sme-coverage { display:flex; gap:10px; flex-direction:column; }
.sme-cov-item { padding:10px 14px; background:rgba(124, 124, 129, 0.05); border:1px solid rgba(124, 124, 129, 0.15); border-radius:var(--m-radius-sm); display:flex; flex-direction:column; gap:2px; }
.sme-cov-item strong { color:var(--blue); font-size:.9rem; }
.sme-cov-item span { font-size:.8rem; color:var(--muted); }

/* ── Trademark Similarity Search ───────────── */
.trademark-search-box { display:flex; gap:8px; flex-wrap:wrap; align-items:center; }
.trademark-search-box .form-input { max-width:300px; }
.similarity-summary { display:flex; gap:12px; align-items:center; margin-bottom:10px; }
.sim-count { font-size:.85rem; color:var(--muted); }
.sim-risk { font-size:.78rem; padding:2px 10px; border-radius:100px; font-weight:600; }
.sim-risk.high { background:rgba(129, 129, 133, 0.1); color:var(--red); }
.sim-risk.warning { background:rgba(129, 129, 133, 0.1); color:var(--orange); }
.sim-risk.low { background:rgba(124, 124, 129, 0.1); color:var(--accent); }
.sim-list { display:flex; flex-direction:column; gap:6px; }
.sim-item { display:flex; gap:12px; font-size:.82rem; align-items:center; padding:6px 10px; background:var(--surface); border-radius:var(--m-radius-sm); border:1px solid var(--border); }
.sim-name { flex:1; font-weight:600; }
.sim-class { font-size:.75rem; color:var(--muted); }
.sim-score { font-size:.75rem; font-weight:600; }
.sim-score.high { color:var(--red); }
.sim-score.medium { color:var(--orange); }
.sim-score.low { color:var(--accent); }
</style>
