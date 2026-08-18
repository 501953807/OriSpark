<template>
  <div v-if="activeTab === 'calculator'" class="calculator animate-fade-in">
    <div class="disclaimer-bar">
      ⚠️ 本工具仅提供信息指引，不构成法律建议。费用为官方参考价，实际以各官方机构最新公告为准。汇率以实时汇率为准。
    </div>

    <div class="wizard-card card">
      <h3>💰 IP 官方费用计算器</h3>
      <p class="calc-desc">选择知识产权类型、辖区和类别，计算预估官方费用</p>

      <!-- IP Type -->
      <div class="form-group">
        <label>知识产权类型</label>
        <div class="calc-type-row">
          <button v-for="t in ipTypes" :key="t.key" :class="['btn', 'btn-sm', calcData.ip_type === t.key ? 'btn-primary' : 'btn-secondary']" @click="$emit('update:calcData', { ...calcData, ip_type: t.key })">
            {{ t.icon }} {{ t.label }}
          </button>
        </div>
      </div>

      <!-- Jurisdictions -->
      <div class="form-group">
        <label>选择辖区 (可多选)</label>
        <div class="calc-jur-grid">
          <button
            v-for="j in feeJurisdictions"
            :key="j.code"
            :class="['btn', 'btn-sm', calcData.jurisdictions.includes(j.code) ? 'btn-primary' : 'btn-secondary']"
            @click="$emit('toggle-jurisdiction', j.code)"
          >
            {{ j.flag }} {{ j.label }}
          </button>
        </div>
      </div>

      <!-- Trademark: class picker -->
      <div v-if="calcData.ip_type === 'trademark'" class="form-group">
        <label>选择尼斯分类 (可多选, 留空默认1类)</label>
        <div class="calc-class-grid">
          <button
            v-for="c in classShortList"
            :key="c.class_no"
            :class="['class-chip', { active: calcData.classes.includes(c.class_no) }]"
            @click="$emit('toggle-class', c.class_no)"
            :title="c.class_name_zh"
          >
            {{ c.class_no }}
          </button>
        </div>
        <div class="calc-selected-classes" v-if="calcData.classes.length">
          已选: <span v-for="cl in calcData.classes" :key="cl" class="selected-class-tag">{{ cl }}类</span>
        </div>
      </div>

      <!-- Design count -->
      <div v-if="calcData.ip_type === 'design_patent'" class="form-group">
        <label>外观设计数量</label>
        <input v-model.number="calcData.design_count" type="number" min="1" max="100" class="form-input" style="max-width:120px" />
      </div>

      <!-- WIPO specific options -->
      <div v-if="calcData.jurisdictions.includes('wipo') && calcData.ip_type === 'trademark'" class="form-group">
        <label>WIPO 颜色选项</label>
        <div class="calc-toggle">
          <button :class="['btn', 'btn-sm', calcData.is_color ? 'btn-primary' : 'btn-secondary']" @click="$emit('update:calcData', { ...calcData, is_color: !calcData.is_color })">
            {{ calcData.is_color ? '🎨 彩色商标 (CHF 903)' : '⬛ 黑白商标 (CHF 653)' }}
          </button>
        </div>
      </div>

      <!-- WIPO designations -->
      <div v-if="calcData.jurisdictions.includes('wipo')" class="form-group">
        <label>WIPO 指定国家/区域 (可多选)</label>
        <div class="calc-desig-grid">
          <button
            v-for="d in wipoDesignationOptions"
            :key="d.code"
            :class="['btn', 'btn-sm', calcData.wipo_designations.includes(d.code) ? 'btn-primary' : 'btn-secondary']"
            @click="$emit('toggle-designation', d.code)"
          >
            {{ d.label }}
          </button>
        </div>
      </div>

      <!-- Calculate button -->
      <div style="margin-top:16px">
        <button class="btn btn-primary" @click="$emit('calculate')" :disabled="!calcData.jurisdictions.length">
          🔢 计算费用
        </button>
      </div>

      <!-- Results -->
      <div v-if="feeCalcResult" class="calc-result">
        <h4>📊 费用计算结果</h4>

        <!-- Summary -->
        <div class="calc-summary card" style="padding:20px;background:rgba(124, 124, 129, 0.05);margin-bottom:16px">
          <div class="calc-summary-row">
            <div class="calc-summary-item">
              <span class="calc-summary-label">IP 类型</span>
              <strong>{{ feeCalcResult.summary.ip_type_label }}</strong>
            </div>
            <div class="calc-summary-item">
              <span class="calc-summary-label">辖区数</span>
              <strong>{{ feeCalcResult.summary.jurisdictions_count }}</strong>
            </div>
            <div class="calc-summary-item">
              <span class="calc-summary-label">预估总费用 (CNY)</span>
              <strong class="calc-total-fee">¥{{ feeCalcResult.summary.total_fee_cny.toLocaleString() }}</strong>
            </div>
          </div>
          <div class="calc-currency-row" style="margin-top:12px">
            <span v-for="(amount, cur) in feeCalcResult.summary.currency_breakdown" :key="cur" class="currency-chip">
              {{ cur }} {{ amount.toLocaleString() }}
            </span>
          </div>
        </div>

        <!-- Breakdown per jurisdiction -->
        <div class="calc-breakdown">
          <div v-for="item in feeCalcResult.breakdown" :key="item.jurisdiction" class="calc-bd-item">
            <div class="calc-bd-header">
              <span class="calc-bd-jur">{{ jurisdictionFlags[item.jurisdiction] }} {{ item.jurisdiction_label }}</span>
              <strong class="calc-bd-fee">{{ item.currency }} {{ item.fee.toLocaleString() }}</strong>
            </div>
            <div class="calc-bd-detail">
              <span>≈ ¥{{ item.fee_cny.toLocaleString() }}</span>
              <span v-if="item.classes_count">× {{ item.classes_count }} 类</span>
              <span v-if="item.design_count">× {{ item.design_count }} 项</span>
            </div>
            <div v-if="item.detail" class="calc-bd-breakdown">
              <small v-for="(val, key) in item.detail" :key="key" class="calc-bd-sub">{{ key }}: {{ val }}</small>
            </div>
            <div v-if="item.notes" class="calc-bd-notes">{{ item.notes }}</div>
            <div v-if="item.error" class="calc-bd-error">⚠️ {{ item.error }}</div>
          </div>
        </div>

        <!-- FX rates -->
        <div class="calc-fx-note">
          <p>💱 参考汇率: USD={{ feeCalcResult.fx_rates_used.USD }}, EUR={{ feeCalcResult.fx_rates_used.EUR }}, CHF={{ feeCalcResult.fx_rates_used.CHF }}, JPY={{ feeCalcResult.fx_rates_used.JPY }}</p>
          <p class="calc-fx-disclaimer">{{ feeCalcResult.fx_rates_note }}</p>
        </div>

        <div class="disclaimer-bar" style="margin-top:12px">
          {{ feeCalcResult.summary.disclaimer }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  activeTab: string
  calcData: any
  feeCalcResult: any
  feeJurisdictions: Array<{ code: string; flag: string; label: string }>
  classShortList: Array<{ class_no: number; class_name_zh: string }>
  wipoDesignationOptions: Array<{ code: string; label: string }>
  ipTypes: any[]
  jurisdictionFlags: Record<string, string>
}>()

defineEmits<{
  'update:calcData': [data: any]
  'toggle-jurisdiction': [code: string]
  'toggle-class': [classNo: number]
  'toggle-designation': [code: string]
  'calculate': []
}>()
</script>

<style scoped>
/* ── P2.4: Fee Calculator ──────────────────────── */
.calc-desc { color:var(--muted); font-size:.85rem; margin:0 0 16px; }
.calc-type-row { display:flex; gap:8px; flex-wrap:wrap; }
.calc-jur-grid { display:flex; gap:8px; flex-wrap:wrap; }
.calc-class-grid { display:flex; gap:6px; flex-wrap:wrap; }
.class-chip { width:38px; height:38px; display:flex; align-items:center; justify-content:center; border-radius:var(--m-radius-md, 12px); border:2px solid var(--border); background:var(--surface); font-size:.78rem; font-weight:700; cursor:pointer; transition:all .15s; font-family:Inter; color:var(--muted); }
.class-chip:hover { border-color:var(--accent); }
.class-chip.active { background:var(--accent); color:#fff; border-color:var(--accent); }
.calc-selected-classes { margin-top:8px; font-size:.82rem; color:var(--muted); display:flex; gap:6px; flex-wrap:wrap; align-items:center; }
.selected-class-tag { padding:2px 10px; background:rgba(86,202,0,0.1); color:var(--accent); border-radius:100px; font-size:.78rem; font-weight:600; }
.calc-toggle { display:flex; gap:8px; }
.calc-desig-grid { display:flex; gap:8px; flex-wrap:wrap; }
.calc-result { margin-top:24px; }
.calc-result h4 { font-size:1rem; margin:0 0 12px; }
.calc-summary-row { display:flex; gap:24px; flex-wrap:wrap; }
.calc-summary-item { display:flex; flex-direction:column; gap:4px; }
.calc-summary-label { font-size:.76rem; color:var(--muted); }
.calc-summary-item strong { font-size:1.05rem; }
.calc-total-fee { color:var(--accent); font-size:1.3rem !important; }
.currency-chip { padding:4px 12px; background:rgba(86,202,0,0.08); border-radius:100px; font-size:.8rem; font-weight:600; color:var(--accent); }
.calc-breakdown { display:flex; flex-direction:column; gap:10px; margin-bottom:12px; }
.calc-bd-item { padding:14px 16px; border:1px solid var(--border); border-radius:var(--m-radius-sm); background:var(--surface); }
.calc-bd-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:4px; }
.calc-bd-jur { font-size:.85rem; font-weight:600; }
.calc-bd-fee { font-size:.9rem; color:var(--accent); }
.calc-bd-detail { font-size:.78rem; color:var(--muted); display:flex; gap:12px; }
.calc-bd-breakdown { display:flex; flex-wrap:wrap; gap:4px 12px; margin-top:6px; }
.calc-bd-sub { font-size:.74rem; color:var(--muted); padding:1px 6px; background:var(--m-bg-subtle); border-radius:var(--m-radius-xs, 6px); }
.calc-bd-notes { font-size:.76rem; color:var(--muted); margin-top:6px; font-style:italic; }
.calc-bd-error { font-size:.78rem; color:var(--orange); margin-top:4px; }
.calc-fx-note { margin-top:10px; padding:10px 14px; background:rgba(129, 129, 133, 0.06); border-radius:var(--m-radius-sm); }
.calc-fx-note p { font-size:.78rem; color:var(--muted); margin:0; }
.calc-fx-disclaimer { font-size:.72rem !important; color:var(--orange) !important; margin-top:4px !important; }
</style>
