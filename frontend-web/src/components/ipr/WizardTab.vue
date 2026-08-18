<template>
  <div v-if="activeTab === 'assistant'" class="assistant animate-fade-in">
    <div class="disclaimer-bar">
      ⚠️ 本工具仅提供信息指引，不构成法律建议。所有申请须由您自行向官方机构提交。
    </div>

    <!-- Step Navigator -->
    <div class="wizard-steps">
      <div v-for="(s, i) in wizardSteps" :key="i" class="wiz-step" :class="{ active: wizardStep === i, done: wizardStep > i }">
        <span class="wiz-num">{{ wizardStep > i ? '✓' : i + 1 }}</span>
        <span class="wiz-label">{{ s }}</span>
      </div>
    </div>

    <!-- Step 0: 选择IP类型 -->
    <div v-if="wizardStep === 0" class="wizard-card card">
      <h3>选择知识产权类型</h3>
      <div class="ip-type-grid">
        <div v-for="t in ipTypes" :key="t.key" class="ip-type-card" :class="{ selected: wizardData.ip_type === t.key }" @click="$emit('update:wizardData', { ...wizardData, ip_type: t.key })">
          <span class="ip-type-icon">{{ t.icon }}</span>
          <strong>{{ t.label }}</strong>
          <p>{{ t.desc }}</p>
        </div>
      </div>
    </div>

    <!-- Step 1: 选择辖区 -->
    <div v-if="wizardStep === 1" class="wizard-card card">
      <h3>选择提交司法管辖区</h3>
      <div class="jurisdiction-grid">
        <div v-for="j in jurisdictions" :key="j.code" class="jur-card" :class="{ selected: wizardData.jurisdiction === j.code }" @click="$emit('update:wizardData', { ...wizardData, jurisdiction: j.code })">
          <strong>{{ j.flag }} {{ j.label }}</strong>
          <span>{{ j.fee }}</span>
          <small>{{ j.duration }}</small>
        </div>
      </div>
    </div>

    <!-- Step 2: 关联作品 & 预填 -->
    <div v-if="wizardStep === 2" class="wizard-card card">
      <h3>关联作品，自动预填申请信息</h3>
      <div class="prefill-area">
        <div class="works-selector">
          <label>选择已有作品</label>
          <select v-model="wizardData.work_id" class="form-input" @change="$emit('prefill')">
            <option value="">— 选择作品 —</option>
            <option v-for="w in worksList" :key="w.id" :value="w.id">{{ w.title }}</option>
          </select>
          <button class="btn btn-primary btn-sm" :disabled="!wizardData.work_id" @click="$emit('prefill')">🪄 自动预填</button>
        </div>
        <div v-if="prefillResult" class="prefill-result">
          <div class="completeness-bar">
            <span class="comp-label">完整性</span>
            <div class="comp-track">
              <div class="comp-fill" :style="{ width: prefillResult.completeness + '%' }"></div>
            </div>
            <span class="comp-pct">{{ prefillResult.completeness }}%</span>
          </div>
          <div class="prefill-fields">
            <div v-for="f in prefillResult.fields" :key="f.official_field" class="prefill-field">
              <label>
                {{ f.label_zh }}
                <span v-if="f.required" class="req-mark">*</span>
                <span class="source-tag" :class="'src-' + f.source">{{ sourceLabels[f.source] || f.source }}</span>
              </label>
              <input v-if="f.editable" v-model="f.value" class="form-input" />
              <span v-else class="readonly-val">{{ f.value || '(无)' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Step 3: 校验 -->
    <div v-if="wizardStep === 3" class="wizard-card card">
      <h3>表单校验</h3>
      <button class="btn btn-primary" @click="$emit('validate')">🔍 开始校验</button>
      <div v-if="validateResult" class="validate-result">
        <div class="completeness-bar">
          <span class="comp-label">完整性</span>
          <div class="comp-track">
            <div class="comp-fill" :style="{ width: validateResult.completeness + '%' }" :class="validateResult.valid ? 'fill-green' : 'fill-red'"></div>
          </div>
          <span class="comp-pct">{{ validateResult.completeness }}%</span>
        </div>
        <div v-if="validateResult.valid" class="valid-ok">✅ 表单校验通过，可以导出申请材料</div>
        <div v-else class="issues-list">
          <div v-for="issue in validateResult.issues" :key="issue.field" class="issue-item" :class="'issue-' + issue.level">
            <span>{{ issue.level === 'error' ? '❌' : '⚠️' }}</span>
            <strong>{{ issue.field }}</strong>: {{ issue.message }}
          </div>
        </div>
      </div>
    </div>

    <!-- Step 4: 律师审核确认 -->
    <div v-if="wizardStep === 4" class="wizard-card card">
      <h3>律师审核确认</h3>
      <p class="lawyer-audit-intro">根据中国法律法规要求，提交 IP 登记材料前需完成律师审核确认：</p>
      <div class="audit-options">
        <label class="audit-option" :class="{ selected: wizardData.lawyer_consulted === 'A' }">
          <input type="radio" :value="'A'" @change="$emit('update:wizardData', { ...wizardData, lawyer_consulted: 'A' })" />
          <span class="audit-radio-circle" :class="{ checked: wizardData.lawyer_consulted === 'A' }"></span>
          <div class="audit-option-content">
            <strong>A. 已咨询律师</strong>
            <span>我已咨询执业律师，理解登记风险</span>
          </div>
        </label>
        <label class="audit-option" :class="{ selected: wizardData.lawyer_consulted === 'B' }">
          <input type="radio" :value="'B'" @change="$emit('update:wizardData', { ...wizardData, lawyer_consulted: 'B' })" />
          <span class="audit-radio-circle" :class="{ checked: wizardData.lawyer_consulted === 'B' }"></span>
          <div class="audit-option-content">
            <strong>B. 自行承担风险</strong>
            <span>我理解系统仅提供参考信息，注册结果取决于官方审查</span>
          </div>
        </label>
        <label class="audit-option" :class="{ selected: wizardData.lawyer_consulted === 'C' }">
          <input type="radio" :value="'C'" @change="$emit('update:wizardData', { ...wizardData, lawyer_consulted: 'C' })" />
          <span class="audit-radio-circle" :class="{ checked: wizardData.lawyer_consulted === 'C' }"></span>
          <div class="audit-option-content">
            <strong>C. 暂不提交</strong>
            <span>我选择先了解更多信息，稍后再来</span>
          </div>
        </label>
      </div>

      <!-- 5 risk confirmation checkboxes (option B only) -->
      <div v-if="wizardData.lawyer_consulted === 'B'" class="risk-confirmations">
        <div v-for="(cb, key) in riskConfirmationLabels" :key="key" class="risk-confirm-item">
          <input type="checkbox" :id="key" v-model="riskConfirmations[key]" />
          <label :for="key">{{ cb }}</label>
        </div>
        <p v-if="!allRiskConfirmed" class="risk-confirm-hint">⚠️ 请勾选全部 5 项以继续</p>
      </div>

      <div class="lawyer-audit-footer">
        <p class="lawyer-audit-note">您的选择已记录：<strong>{{ wizardData.lawyer_consulted === 'A' ? '已咨询执业律师' : wizardData.lawyer_consulted === 'B' ? '自行承担风险' : '暂不提交' }}</strong></p>
      </div>
    </div>

    <!-- Step 5: 导出 -->
    <div v-if="wizardStep === 5" class="wizard-card card">
      <h3>导出申请材料</h3>
      <div class="export-actions">
        <button class="btn btn-primary" @click="$emit('generate')">📄 生成申请表预览</button>
        <button class="btn btn-secondary" @click="$emit('export')">📦 查看材料清单</button>
      </div>
      <div v-if="generateResult" class="export-result">
        <h4>{{ generateResult.form_title }}</h4>
        <div class="export-disclaimer">⚠️ {{ generateResult.disclaimer }}</div>
        <h5>预填字段值:</h5>
        <table class="preview-table">
          <tr v-for="(val, key) in generateResult.fields" :key="key">
            <td>{{ key }}</td>
            <td>{{ val }}</td>
          </tr>
        </table>
        <a v-if="generateResult.official_url" :href="generateResult.official_url" target="_blank" class="btn btn-secondary">🔗 前往官方平台提交</a>
      </div>
      <div v-if="exportResult" class="export-result">
        <h4>📦 申请材料清单</h4>
        <div class="export-disclaimer">⚠️ {{ exportResult.disclaimer }}</div>
        <div v-for="item in exportResult.checklist" :key="item.name" class="checklist-item">
          <span>{{ item.required ? '✓' : '○' }}</span>
          <strong>{{ item.name }}</strong>
          <span class="item-status" :class="'status-' + item.status">{{ item.status === 'prepared' ? '已准备' : '需手动准备' }}</span>
          <p class="item-desc">{{ item.description }}</p>
        </div>
      </div>
    </div>

    <!-- Wizard navigation -->
    <div class="wizard-nav">
      <button v-if="wizardStep > 0" class="btn btn-secondary" @click="$emit('prev-step')">← 上一步</button>
      <div class="spacer"></div>
      <button v-if="wizardStep < 5" :class="['btn', 'btn-primary', { disabled: !canProceedWithLawyerConfirm && wizardStep === 4 }]" :disabled="!canProceedWithLawyerConfirm && wizardStep === 4" @click="$emit('next-step')">下一步 →</button>
      <button v-else class="btn btn-accent" @click="$emit('reset')">🔄 重新开始</button>
    </div>

    <!-- 类别推荐 -->
    <div class="wizard-card card" style="margin-top:16px">
      <h4>💡 商标类别推荐</h4>
      <div class="category-recommender">
        <div class="recommend-input">
          <input :value="localRecommendTags" class="form-input" placeholder="输入标签, 逗号分隔 (如: 插画,文创,角色)" @input="localRecommendTags = ($event.target as HTMLInputElement).value; $emit('update:recommendTags', localRecommendTags)" @keyup.enter="$emit('recommend', localRecommendTags, localRecommendCreatorType)" />
          <select :value="localRecommendCreatorType" class="form-input" @change="$emit('update:recommendCreatorType', ($event.target as HTMLSelectElement).value)">
            <option value="">— 创作者类型(可选) —</option>
            <option value="illustrator_flat">插画师(平面)</option>
            <option value="illustrator_product">插画师(产品化)</option>
            <option value="gamedev">独立游戏开发者</option>
            <option value="aigc_creator">AIGC创作者</option>
            <option value="vtuber">Vtuber/虚拟偶像</option>
            <option value="musician">音乐人</option>
            <option value="photographer">摄影师</option>
          </select>
          <button class="btn btn-primary btn-sm" @click="$emit('recommend', localRecommendTags, localRecommendCreatorType)">推荐类别</button>
        </div>
        <div v-if="recommendResult" class="recommend-result">
          <div v-for="r in recommendResult.recommendations" :key="r.class_no" class="rec-class-item">
            <span class="rec-stars">{{ '★'.repeat(r.priority) }}{{ '☆'.repeat(5 - r.priority) }}</span>
            <strong>第{{ r.class_no }}类</strong>
            <span>{{ r.class_name_zh }}</span>
            <span class="rec-reason">{{ r.reason }}</span>
            <span class="rec-fee">¥{{ r.fee_estimate }}</span>
          </div>
          <div class="rec-summary">
            <strong>预估总费用: ¥{{ recommendResult.estimated_total_fee }}</strong>
            <p>{{ recommendResult.strategy_note }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, watch, ref } from 'vue'

const props = defineProps<{
  activeTab: string
  wizardStep: number
  wizardData: any
  riskConfirmations: Record<string, boolean>
  allRiskConfirmed: boolean
  canProceedWithLawyerConfirm: boolean
  worksList: any[]
  prefillResult: any
  validateResult: any
  generateResult: any
  exportResult: any
  recommendTags: string
  recommendCreatorType: string
  recommendResult: any
  riskConfirmationLabels: Record<string, string>
  ipTypes: any[]
  jurisdictions: any[]
  wizardSteps: string[]
  sourceLabels: Record<string, string>
}>()

const emit = defineEmits<{
  'update:wizardStep': [step: number]
  'update:wizardData': [data: any]
  'update:riskConfirmations': [confs: Record<string, boolean>]
  'update:recommendTags': [tags: string]
  'update:recommendCreatorType': [type: string]
  'prev-step': []
  'next-step': []
  'prefill': []
  'validate': []
  'generate': []
  'export': []
  'recommend': [tags: string, creatorType: string]
  'reset': []
}>()

const localRecommendTags = ref(props.recommendTags)
const localRecommendCreatorType = ref(props.recommendCreatorType)

watch(() => props.recommendTags, (v) => { localRecommendTags.value = v })
watch(() => props.recommendCreatorType, (v) => { localRecommendCreatorType.value = v })

const allRiskConfirmed = computed(() =>
  Object.values(props.riskConfirmations).every(Boolean),
)

const canProceedWithLawyerConfirm = computed(() => {
  if (!props.wizardData.lawyer_consulted) return false
  if (props.wizardData.lawyer_consulted === 'B') return allRiskConfirmed.value
  return true
})
</script>

<style scoped>
/* ── Wizard ──────────────────────────────────── */
.wizard-steps { display:flex; gap:0; align-items:center; margin-bottom:4px; }
.wiz-step { display:flex; align-items:center; gap:8px; padding:8px 16px 8px 8px; font-size:.82rem; color:var(--muted); }
.wiz-step.active { color:var(--accent); font-weight:700; }
.wiz-step.done { color:var(--accent); }
.wiz-num { width:28px; height:28px; display:flex; align-items:center; justify-content:center; border-radius:50%; border:2px solid var(--border); font-size:.78rem; font-weight:700; }
.wiz-step.active .wiz-num { background:var(--accent); color:#fff; border-color:var(--accent); }
.wiz-step.done .wiz-num { background:rgba(86,202,0,0.2); color:var(--accent); border-color:var(--accent); }

.wizard-card { padding:24px; }
.wizard-card h3 { margin:0 0 16px; font-size:1.05rem; }
.wizard-card h4 { margin:0 0 12px; font-size:.95rem; }

.ip-type-grid { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
.ip-type-card { padding:16px; border:2px solid var(--border); border-radius:var(--m-radius-lg); cursor:pointer; transition:all .15s; }
.ip-type-card:hover { border-color:var(--accent); }
.ip-type-card.selected { border-color:var(--accent); background:rgba(124, 124, 129, 0.05); }
.ip-type-icon { font-size:1.5rem; display:block; margin-bottom:6px; }
.ip-type-card strong { font-size:.9rem; display:block; }
.ip-type-card p { font-size:.78rem; color:var(--muted); margin:4px 0 0; }

.jurisdiction-grid { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
.jur-card { padding:12px 16px; border:2px solid var(--border); border-radius:var(--m-radius-lg); cursor:pointer; transition:all .15s; display:flex; flex-direction:column; gap:4px; }
.jur-card:hover { border-color:var(--accent); }
.jur-card.selected { border-color:var(--accent); background:rgba(124, 124, 129, 0.05); }
.jur-card strong { font-size:.9rem; }
.jur-card span { font-size:.8rem; }
.jur-card small { font-size:.72rem; color:var(--muted); }

.works-selector { display:flex; gap:10px; align-items:center; margin-bottom:16px; }
.works-selector label { font-size:.84rem; font-weight:600; white-space:nowrap; }
.works-selector select { min-width:200px; }

.prefill-result { margin-top:12px; }
.completeness-bar { display:flex; align-items:center; gap:10px; margin:12px 0; }
.comp-label { font-size:.82rem; font-weight:600; min-width:50px; }
.comp-track { flex:1; height:8px; background:var(--border); border-radius:var(--m-radius-md, 12px); overflow:hidden; }
.comp-fill { height:100%; background:var(--accent); border-radius:var(--m-radius-md, 12px); transition:width .3s; }
.comp-fill.fill-green { background:var(--green); }
.comp-fill.fill-red { background:var(--red); }
.comp-pct { font-size:.82rem; font-weight:700; min-width:40px; }

.prefill-fields { display:grid; grid-template-columns:1fr 1fr; gap:10px; max-height:400px; overflow-y:auto; }
.prefill-field { display:flex; flex-direction:column; gap:4px; }
.prefill-field label { font-size:.78rem; font-weight:600; color:var(--muted); display:flex; align-items:center; gap:4px; }
.req-mark { color:var(--red); }
.source-tag { font-size:.65rem; padding:0 4px; border-radius:3px; font-weight:400; }
.src-work { background:rgba(86,202,0,0.1); color:var(--accent); }
.src-notary { background:rgba(124, 124, 129, 0.1); color:var(--blue); }
.src-manual { background:rgba(129, 129, 133, 0.1); color:var(--orange); }
.src-user { background:rgba(129, 129, 133, 0.1); color:var(--purple); }
.readonly-val { font-size:.84rem; padding:8px 12px; background:var(--surface); border:1px solid var(--border); border-radius:var(--m-radius-sm); color:var(--muted); }

.validate-result { margin-top:16px; }
.valid-ok { padding:12px; background:rgba(86,202,0,0.08); border-radius:var(--m-radius-sm); font-weight:600; color:var(--accent); }
.issues-list { display:flex; flex-direction:column; gap:8px; margin-top:12px; }
.issue-item { padding:8px 12px; border-radius:var(--m-radius-sm); font-size:.82rem; }
.issue-error { background:rgba(129, 129, 133, 0.06); color:var(--red); }
.issue-warning { background:rgba(129, 129, 133, 0.06); color:var(--orange); }
.issue-item strong { margin:0 4px; }

.export-actions { display:flex; gap:10px; margin-bottom:16px; }
.export-result { margin-top:16px; }
.export-disclaimer { padding:8px 12px; background:rgba(129, 129, 133, 0.06); border-radius:var(--m-radius-sm); font-size:.8rem; color:var(--orange); margin:10px 0; }
.preview-table { width:100%; border-collapse:collapse; font-size:.82rem; margin:10px 0; }
.preview-table td { padding:6px 10px; border-bottom:1px solid var(--border); }
.preview-table td:first-child { font-weight:600; color:var(--muted); width:30%; }
.checklist-item { display:flex; flex-wrap:wrap; gap:6px; align-items:baseline; padding:6px 0; border-bottom:1px solid var(--border); font-size:.84rem; }
.item-status { font-size:.72rem; padding:1px 6px; border-radius:var(--m-radius-xs, 6px); }
.status-prepared { background:rgba(86,202,0,0.1); color:var(--accent); }
.status-requires_manual { background:rgba(129, 129, 133, 0.1); color:var(--orange); }
.item-desc { font-size:.76rem; color:var(--muted); width:100%; margin:0; }

.wizard-nav { display:flex; gap:10px; align-items:center; margin-top:8px; }
.spacer { flex:1; }

/* ── Category Recommender ────────────────────── */
.category-recommender { margin-top:8px; }
.recommend-input { display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
.recommend-input .form-input { flex:1; min-width:120px; }
.recommend-result { margin-top:12px; }
.rec-class-item { display:flex; align-items:center; gap:8px; padding:8px 0; border-bottom:1px solid var(--border); font-size:.84rem; }
.rec-stars { color:rgba(22,163,74, 0.06); font-size:.82rem; min-width:70px; }
.rec-class-item strong { min-width:60px; }
.rec-reason { color:var(--muted); font-size:.78rem; flex:1; }
.rec-fee { font-weight:600; color:var(--accent); }
.rec-summary { margin-top:12px; padding:12px; background:rgba(124, 124, 129, 0.05); border-radius:var(--m-radius-sm); }
.rec-summary strong { font-size:.9rem; color:var(--accent); }
.rec-summary p { font-size:.78rem; color:var(--muted); margin:4px 0 0; }

/* ── Lawyer audit step ─────────────────────────── */
.lawyer-audit-intro { font-size: .84rem; color: var(--muted); margin: 0 0 16px; }
.audit-options { display: flex; flex-direction: column; gap: 10px; margin-bottom: 16px; }
.audit-option {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 16px; border: 2px solid var(--border);
  border-radius: var(--m-radius-lg); cursor: pointer;
  transition: all .15s; background: var(--surface);
}
.audit-option:hover { border-color: var(--accent); }
.audit-option.selected { border-color: var(--accent); background: rgba(124, 124, 129, 0.05); }
.audit-option input[type="radio"] { display: none; }
.audit-radio-circle {
  width: 20px; height: 20px; border-radius: 50%;
  border: 2px solid var(--border); flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  transition: all .15s;
}
.audit-radio-circle.checked { border-color: var(--accent); }
.audit-radio-circle.checked::after {
  content: ''; width: 10px; height: 10px;
  background: var(--accent); border-radius: 50%;
}
.audit-option-content { display: flex; flex-direction: column; gap: 2px; }
.audit-option-content strong { font-size: .9rem; }
.audit-option-content span { font-size: .8rem; color: var(--muted); }
.risk-confirmations {
  padding: 16px; background: rgba(129, 129, 133, 0.06);
  border-radius: var(--m-radius-sm); margin-bottom: 12px;
}
.risk-confirm-item {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 0; font-size: .84rem;
}
.risk-confirm-item input[type="checkbox"] { width: 16px; height: 16px; flex-shrink: 0; }
.risk-confirm-hint { font-size: .8rem; color: var(--orange); margin: 8px 0 0; }
.lawyer-audit-footer { margin-top: 8px; }
.lawyer-audit-note { font-size: .82rem; color: var(--muted); margin: 0; }
</style>
