# IprView.vue 拆分实施计划

**Goal:** 将 2071 行的 IprView.vue 拆分为 5 个独立 Tab 组件 + 1 个共享 composable，使每个文件 <400 行。

**Architecture:** Extract shared state/API into a composable, then split each tab's template + script into its own component. The main view becomes a thin router/tab dispatcher.

**Tech Stack:** Vue 3 Composition API, TypeScript, Pinia-style refs (no external store needed)

## Global Constraints

- Files: 200-400 lines typical, 800 max
- Immutability: Use spread/refs, never mutate existing objects directly
- No comments unless non-obvious
- Match existing code style (Chinese labels, oklch colors, CSS variables)
- Preserve all existing functionality — no behavior changes

---

### Task 1: Create `composables/useIprData.ts`

**Files:**
- Create: `frontend-web/src/composables/useIprData.ts`

**Interfaces:**
- Returns a composable object with: shared state (refs), shared functions, label maps, API instance
- All refs exported as `{ get(): ref, set(val) }` pattern or direct ref access

**Steps:**

- [ ] **Step 1: Create the composable with shared state**

Create `src/composables/useIprData.ts`:

```typescript
import { ref, computed, onMounted } from 'vue'
import { iprApi } from '@/api/ipr'
import client from '@/api/client'

// ─── Label Maps ────────────────────────────────
export const statusLabels: Record<string, string> = {
  draft: '草稿', filed: '已提交', under_review: '审查中',
  registered: '已注册', rejected: '已驳回', expired: '已过期',
  withdrawn: '已撤回', supplemented: '已补充',
}
export const statusVariants: Record<string, string> = {
  draft: 'info', filed: 'info', under_review: 'warning',
  registered: 'success', rejected: 'error', expired: 'error',
  withdrawn: 'neutral', supplemented: 'info',
}
export const typeLabels: Record<string, string> = {
  copyright: '著作权', trademark: '商标',
  design_patent: '外观设计', utility_patent: '专利',
}
export const jurisdictionLabels: Record<string, string> = {
  cn: '中国', us: '美国', eu: '欧盟',
  jp: '日本', kr: '韩国', wipo: 'WIPO',
}
export const jurisdictionFlags: Record<string, string> = {
  cn: '🇨🇳', us: '🇺🇸', eu: '🇪🇺',
  jp: '🇯🇵', kr: '🇰🇷', wipo: '🌐',
}
export const ipTypeIcons: Record<string, string> = {
  copyright: '©️', trademark: '®️',
  design_patent: '🎨', utility_patent: '💡',
}
export const sourceLabels: Record<string, string> = {
  work: '作品', user: '用户', notary: '存证', manual: '手动',
}
export const nextActionTypeLabels: Record<string, string> = {
  renewal: '续展', annuity: '年费', declaration_of_use: '使用声明',
}
export const keyLabels: Record<string, string> = {
  artwork: '美术作品', text: '文字作品', music: '音乐作品', software: '计算机软件',
  application_1class: '申请费(1类)', application_example_1class: '申请示例(1类)',
  application_example_3class: '申请示例(3类)', registration: '注册费',
  renewal: '续展费', renewal_5year: '5年分期续展',
  application_fee_per_class: '申请费/类', registration_fee_per_class: '注册费/类',
  annual_fee: '年费', second_class_fee: '第2类费', third_plus_class_fee: '第3类起费',
  additional_design_fee: '额外设计费', publication_fee: '公告费',
  deferred_publication_fee: '延迟公告费', color_surcharge: '彩色附加费',
  currency: '货币单位', notes: '备注',
}
export const trademarkFeeLabels: Record<string, string> = {
  application_1class: '申请费(1类)', application_example_1class: '申请示例(1类)',
  application_example_3class: '申请示例(3类)', registration: '注册费',
  renewal: '续展费', renewal_5year: '5年分期续展',
}
export const designPatentFeeLabels: Record<string, string> = {
  application_fee_per_class: '申请费/类', registration_fee_per_class: '注册费/类',
  annual_fee: '年费', second_class_fee: '第2类费', third_plus_class_fee: '第3类起费',
  additional_design_fee: '额外设计费', publication_fee: '公告费',
  deferred_publication_fee: '延迟公告费', color_surcharge: '彩色附加费',
  currency: '货币单位', notes: '备注',
  application_1class: '申请费(1类)', application_example_1class: '申请示例(1类)',
  registration: '注册费', renewal: '续展费',
}

// ─── Shared State ──────────────────────────────
const disclaimersAccepted = ref(localStorage.getItem('ipr_disclaimer_accepted') === 'true')
const dismissDisclaimers = ref(false)
const showDisclaimerDetails = ref(true)

const guidelineJurisdiction = ref('cn')
const guidelineCollapsed = ref(false)
const guidelinesData = ref<Record<string, any>>({})
const records = ref<any[]>([])
const portfolio = ref<any>(null)
const dashFilterType = ref('')
const filterType = ref('')
const filterStatus = ref('')

// ─── Shared Functions ──────────────────────────
function acceptDisclaimers() {
  disclaimersAccepted.value = true
  localStorage.setItem('ipr_disclaimer_accepted', 'true')
  dismissDisclaimers.value = false
  try {
    fetch('/api/system/disclaimers/accept', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ disclaimer_key: 'no_legal_advice', context: 'ipr_first_entry' }),
    })
  } catch {}
}

async function loadGuidelines() {
  const res = await iprApi.guidelines(guidelineJurisdiction.value)
  const data = res.data.data
  if (data.jurisdiction) {
    guidelinesData.value[data.jurisdiction] = data.guidelines
  } else {
    guidelinesData.value = data.guidelines || data
  }
}

const currentGuidelines = computed(() => guidelinesData.value[guidelineJurisdiction.value] || null)
const hasGuidelinesContent = computed(() => {
  const cg = currentGuidelines.value
  return cg && (cg.copyright || cg.trademark || cg.design_patent || cg.sme_fund)
})
const globalCategories = computed(() => guidelinesData.value['categories'] || null)

async function loadRecords() {
  const params: any = {}
  if (filterType.value) params.ip_type = filterType.value
  if (filterStatus.value) params.status = filterStatus.value
  const res = await iprApi.registrations(params)
  records.value = res.data.data
}

async function loadPortfolio() {
  try {
    const res = await iprApi.portfolio()
    portfolio.value = res.data.data
  } catch { portfolio.value = null }
}

function switchJurisdiction(jur: string) {
  guidelineJurisdiction.value = jur
  loadGuidelines()
}

// ─── Disclaimer Messages ───────────────────────
const disclaimerMessages = [
  '1. 不构成律师-客户关系：OriStudio 是软件工具，不是律师事务所。使用本软件不建立律师-客户特权关系。',
  '2. 不构成法律建议：系统提供的IP登记指引、分类推荐、费用估算仅供参考，不构成正式法律意见。做法律决策前应咨询持证律师。',
  '3. 不保证注册成功：系统辅助准备申请材料，不保证商标/版权/专利注册一定成功。注册结果取决于官方审查。',
  '7. 司法管辖区限制：IP登记指引覆盖中国/美国/欧盟/WIPO主要辖区，不包括所有国家/地区。',
]

// ─── Global Jurisdictions ──────────────────────
const globalJurisdictions = [
  { code: 'cn', flag: '🇨🇳', label: '中国' },
  { code: 'us', flag: '🇺🇸', label: '美国' },
  { code: 'eu', flag: '🇪🇺', label: '欧盟' },
  { code: 'wipo', flag: '🌐', label: 'WIPO' },
  { code: 'jp', flag: '🇯🇵', label: '日本' },
  { code: 'kr', flag: '🇰🇷', label: '韩国' },
]

export function useIprData() {
  return {
    // State
    disclaimersAccepted, dismissDisclaimers, showDisclaimerDetails,
    guidelineJurisdiction, guidelineCollapsed, guidelinesData,
    records, portfolio, dashFilterType, filterType, filterStatus,
    // Computed
    currentGuidelines, hasGuidelinesContent, globalCategories,
    // Functions
    acceptDisclaimers, loadGuidelines, loadRecords, loadPortfolio, switchJurisdiction,
    // Labels
    statusLabels, statusVariants, typeLabels, jurisdictionLabels, jurisdictionFlags,
    ipTypeIcons, sourceLabels, nextActionTypeLabels, keyLabels,
    trademarkFeeLabels, designPatentFeeLabels,
    // Static data
    disclaimerMessages, globalJurisdictions,
    // API
    iprApi,
  }
}
```

- [ ] **Step 2: Verify the composable compiles**

Run: `npx vue-tsc --noEmit --pretty 2>&1 | head -20`
Expected: No errors related to useIprData.ts

- [ ] **Step 3: Commit**

```bash
git add frontend-web/src/composables/useIprData.ts
git commit -m "refactor(ipr): extract shared state and labels into useIprData composable"
```

---

### Task 2: Create GuidelinesTab.vue

**Files:**
- Create: `frontend-web/src/components/ipr/GuidelinesTab.vue`

**Interfaces:**
- Consumes: `currentGuidelines`, `hasGuidelinesContent`, `globalJurisdictions`, `guidelineJurisdiction`, `guidelineCollapsed`, `globalCategories`, `switchJurisdiction`, `selectClassHint`, `keyLabels`, `trademarkFeeLabels`, `designPatentFeeLabels`, `iprApi`, `similarityQuery`, `similarityClass`, `similarityResult`, `doTrademarkSearch`
- Produces: None (pure tab component)

**Steps:**

- [ ] **Step 1: Create GuidelinesTab.vue with Tab 1 template**

Extract lines 33-414 from IprView.vue (the guidelines tab content) into a new component:

```vue
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
        :class="['jur-btn', { active: localJurisdiction === j.code }]"
        @click="localJurisdiction = j.code"
      >
        <span class="jur-flag">{{ j.flag }}</span>
        <span class="jur-label">{{ j.label }}</span>
      </button>
    </div>

    <!-- 加载当前辖区指引 -->
    <template v-if="currentGuidelines">
      <!-- Copyright guideline card (lines 56-119) -->
      <!-- Trademark guideline card (lines 122-262) -->
      <!-- Design patent guideline card (lines 265-334) -->
      <!-- EUIPO SME Fund card (lines 337-408) -->
      <!-- Fallback (lines 411-413) -->
    </template>
  </div>
</template>
```

The component receives props for all shared state and emits events for user actions. Key props:
- `modelValue: string` — current jurisdiction (v-model)
- `currentGuidelines: object | null`
- `hasGuidelinesContent: boolean`
- `globalCategories: object | null`
- `globalJurisdictions: array`
- `guidelineCollapsed: boolean`
- `keyLabels, trademarkFeeLabels, designPatentFeeLabels: objects`

Key emits:
- `update:modelValue(jurisdiction: string)` — jurisdiction change
- `select-class(classNo: number)` — category chip click

Script setup imports:
- Keep all the guideline display logic (collapsible sections, fee grids, material lists, process flows)
- Keep similarity search inputs and results display
- Import `DisclaimerBanner`, `EmptyState` locally if needed

- [ ] **Step 2: Verify the component compiles**

Run: `npx vue-tsc --noEmit --pretty 2>&1 | grep GuidelinesTab | head -10`

- [ ] **Step 3: Commit**

```bash
git add frontend-web/src/components/ipr/GuidelinesTab.vue
git commit -m "feat(ipr): extract GuidelinesTab component (~380 lines)"
```

---

### Task 3: Create WizardTab.vue

**Files:**
- Create: `frontend-web/src/components/ipr/WizardTab.vue`

**Interfaces:**
- Consumes: `wizardStep`, `wizardData`, `riskConfirmations`, `allRiskConfirmed`, `canProceedWithLawyerConfirm`, `worksList`, `prefillResult`, `validateResult`, `generateResult`, `exportResult`, `recommendTags`, `recommendCreatorType`, `recommendResult`, `riskConfirmationLabels`, `ipTypes`, `jurisdictions`
- Produces: Updates wizard state via emit, calls API functions

**Steps:**

- [ ] **Step 1: Create WizardTab.vue with Tab 2 template**

Extract lines 418-629 (wizard steps + category recommender) into a new component.

Props:
- `wizardStep: number`
- `wizardData: object` (ip_type, jurisdiction, work_id, lawyer_consulted)
- `riskConfirmations: object`
- `allRiskConfirmed: boolean`
- `canProceedWithLawyerConfirm: boolean`
- `worksList: array`
- `prefillResult, validateResult, generateResult, exportResult: objects`
- `recommendTags: string`
- `recommendCreatorType: string`
- `recommendResult: object`
- `riskConfirmationLabels: object`
- `ipTypes: array`
- `jurisdictions: array`

Emits:
- `update:wizardStep(step: number)`
- `update:wizardData(data: object)`
- `update:riskConfirmations(confs: object)`
- `update:recommendTags(tags: string)`
- `update:recommendCreatorType(type: string)`
- `prefill(workId: string)`
- `validate()`
- `generate()`
- `export()`
- `recommend(tags: string[], creatorType: string)`
- `reset()`

Script setup:
- Keep all wizard step logic (steps 0-5)
- Keep prefill/validate/generate/export API calls
- Keep category recommender logic
- Keep auto-load creator_type from localStorage

- [ ] **Step 2: Verify the component compiles**

Run: `npx vue-tsc --noEmit --pretty 2>&1 | grep WizardTab | head -10`

- [ ] **Step 3: Commit**

```bash
git add frontend-web/src/components/ipr/WizardTab.vue
git commit -m "feat(ipr): extract WizardTab component (~400 lines)"
```

---

### Task 4: Create RegistrationsTab.vue

**Files:**
- Create: `frontend-web/src/components/ipr/RegistrationsTab.vue`

**Interfaces:**
- Consumes: `records`, `showAddModal`, `editingRecord`, `form`, `filterType`, `filterStatus`, `typeLabels`, `jurisdictionLabels`, `statusLabels`, `statusVariants`
- Produces: CRUD operations via emits

**Steps:**

- [ ] **Step 1: Create RegistrationsTab.vue with Tab 3 template**

Extract lines 632-676 (registrations list) + modal content (lines 910-1028) into a component.

Props:
- `records: array`
- `showAddModal: boolean`
- `editingRecord: object | null`
- `form: object`
- `filterType: string`
- `filterStatus: string`
- `typeLabels, jurisdictionLabels, statusLabels, statusVariants: objects`

Emits:
- `update:showAddModal(show: boolean)`
- `update:editingRecord(rec: object | null)`
- `update:form(form: object)`
- `update:filterType(type: string)`
- `update:filterStatus(status: string)`
- `load-records()`
- `open-add-modal()`
- `edit-record(record: object)`
- `save-record()`
- `delete-record(id: string)`
- `view-record-detail(record: object)`
- `withdraw-record(id: string)`
- `open-supplement(record: object)`
- `submit-supplement()`

Script setup:
- Keep all CRUD functions (openAddModal, editRecord, saveRecord, deleteRecord)
- Keep record detail/supplement modal logic (viewRecordDetail, withdrawRecord, openSupplement, submitSupplement)
- Keep canWithdraw/canSupplement helpers

- [ ] **Step 2: Verify the component compiles**

Run: `npx vue-tsc --noEmit --pretty 2>&1 | grep RegistrationsTab | head -10`

- [ ] **Step 3: Commit**

```bash
git add frontend-web/src/components/ipr/RegistrationsTab.vue
git commit -m "feat(ipr): extract RegistrationsTab component (~130 lines)"
```

---

### Task 5: Create DashboardTab.vue

**Files:**
- Create: `frontend-web/src/components/ipr/DashboardTab.vue`

**Interfaces:**
- Consumes: `portfolio`, `dashFilterType`, `typeLabels`, `statusLabels`, `statusVariants`, `jurisdictionLabels`, `jurisdictionFlags`, `ipTypeIcons`
- Produces: filter change, CSV export

**Steps:**

- [ ] **Step 1: Create DashboardTab.vue with Tab 4 template**

Extract lines 679-755 (dashboard stats, summary, jurisdiction distribution, renewals).

Props:
- `portfolio: object | null`
- `dashFilterType: string`

Emits:
- `update:dashFilterType(type: string)`
- `export-csv()`

Script setup:
- Keep exportPortfolio function (CSV generation + blob download)
- All template is pure display — no logic needed

- [ ] **Step 2: Verify the component compiles**

Run: `npx vue-tsc --noEmit --pretty 2>&1 | grep DashboardTab | head -10`

- [ ] **Step 3: Commit**

```bash
git add frontend-web/src/components/ipr/DashboardTab.vue
git commit -m "feat(ipr): extract DashboardTab component (~80 lines)"
```

---

### Task 6: Create CalculatorTab.vue

**Files:**
- Create: `frontend-web/src/components/ipr/CalculatorTab.vue`

**Interfaces:**
- Consumes: `calcData`, `feeCalcResult`, `feeJurisdictions`, `classShortList`, `wipoDesignationOptions`, `keyLabels`, `trademarkFeeLabels`, `designPatentFeeLabels`
- Produces: calc state updates, calculation results

**Steps:**

- [ ] **Step 1: Create CalculatorTab.vue with Tab 5 template**

Extract lines 758-907 (fee calculator) + helper functions (toggleFeeJurisdiction, toggleClass, toggleDesignation, doFeeCalc, loadClassShortList).

Props:
- `calcData: object` (ip_type, jurisdictions, classes, design_count, wipo_designations, is_color)
- `feeCalcResult: object | null`
- `feeJurisdictions: array`
- `classShortList: array`
- `wipoDesignationOptions: array`
- `keyLabels, trademarkFeeLabels, designPatentFeeLabels: objects`

Emits:
- `update:calcData(data: object)`
- `toggle-jurisdiction(code: string)`
- `toggle-class(classNo: number)`
- `toggle-designation(code: string)`
- `calculate()`

Script setup:
- Keep toggleFeeJurisdiction, toggleClass, toggleDesignation (emit events)
- Keep doFeeCalc (call API, emit result update)
- Keep loadClassShortList (call API on mount)

- [ ] **Step 2: Verify the component compiles**

Run: `npx vue-tsc --noEmit --pretty 2>&1 | grep CalculatorTab | head -10`

- [ ] **Step 3: Commit**

```bash
git add frontend-web/src/components/ipr/CalculatorTab.vue
git commit -m "feat(ipr): extract CalculatorTab component (~150 lines)"
```

---

### Task 7: Refactor IprView.vue to thin container

**Files:**
- Modify: `frontend-web/src/views/IprView.vue`

**Interfaces:**
- Consumes: `useIprData()` composable
- Produces: renders 5 tab components based on `activeTab`

**Steps:**

- [ ] **Step 1: Rewrite IprView.vue as a thin tab dispatcher**

Replace the entire file with:

```vue
<template>
  <div class="ipr-view">
    <!-- Disclaimer banner (top of page) -->
    <div v-if="!disclaimersAccepted" class="disclaimer-banner card">
      <div class="disclaimer-banner-header">
        <strong>⚖️ 法律声明与免责条款</strong>
        <button class="btn btn-sm btn-secondary" @click="showDisclaimerDetails = !showDisclaimerDetails">
          {{ showDisclaimerDetails ? '收起' : '详情' }}
        </button>
      </div>
      <div v-if="showDisclaimerDetails" class="disclaimer-list">
        <div v-for="(msg, i) in disclaimerMessages" :key="i" class="disclaimer-item">
          <span class="disclaimer-num">#{{ i + 1 }}</span>
          <span>{{ msg }}</span>
        </div>
      </div>
      <div class="disclaimer-footer">
        <label class="disclaimer-checkbox-label">
          <input type="checkbox" v-model="dismissDisclaimers" />
          <span>本次登录不再提示</span>
        </label>
        <button class="btn btn-primary" @click="acceptDisclaimers">我已阅读并同意</button>
      </div>
    </div>

    <!-- Category tabs -->
    <div class="cat-tabs">
      <button v-for="tab in tabs" :key="tab.key" :class="['cat-tab', { active: activeTab === tab.key }]" @click="activeTab = tab.key">
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab content -->
    <GuidelinesTab
      v-if="activeTab === 'guidelines'"
      v-model="guidelineJurisdiction"
      :current-guidelines="currentGuidelines"
      :has-guidelines-content="hasGuidelinesContent"
      :global-categories="globalCategories"
      :global-jurisdictions="globalJurisdictions"
      :guideline-collapsed="guidelineCollapsed"
      :key-labels="keyLabels"
      :trademark-fee-labels="trademarkFeeLabels"
      :design-patent-fee-labels="designPatentFeeLabels"
      @select-class="handleSelectClass"
      @switch-jurisdiction="switchJurisdiction"
    />

    <WizardTab
      v-if="activeTab === 'assistant'"
      v-model:wizard-step="wizardStep"
      v-model:wizard-data="wizardData"
      v-model:risk-confirmations="riskConfirmations"
      :all-risk-confirmed="allRiskConfirmed"
      :can-proceed-with-lawyer-confirm="canProceedWithLawyerConfirm"
      :works-list="worksList"
      :prefill-result="prefillResult"
      :validate-result="validateResult"
      :generate-result="generateResult"
      :export-result="exportResult"
      :recommend-tags="recommendTags"
      :recommend-creator-type="recommendCreatorType"
      :recommend-result="recommendResult"
      :risk-confirmation-labels="riskConfirmationLabels"
      :ip-types="ipTypes"
      :jurisdictions="jurisdictions"
      @prefill="handlePrefill"
      @validate="handleValidate"
      @generate="handleGenerate"
      @export="handleExport"
      @recommend="handleRecommend"
      @reset="handleReset"
    />

    <RegistrationsTab
      v-if="activeTab === 'registrations'"
      :records="records"
      :show-add-modal="showAddModal"
      :editing-record="editingRecord"
      :form="form"
      :filter-type="filterType"
      :filter-status="filterStatus"
      :type-labels="typeLabels"
      :jurisdiction-labels="jurisdictionLabels"
      :status-labels="statusLabels"
      :status-variants="statusVariants"
      @update:show-add-modal="showAddModal = $event"
      @update:editing-record="editingRecord = $event"
      @update:form="form = $event"
      @update:filter-type="filterType = $event"
      @update:filter-status="filterStatus = $event"
      @load-records="loadRecords()"
      @open-add-modal="openAddModal()"
      @edit-record="editRecord"
      @save-record="saveRecord"
      @delete-record="deleteRecord"
      @view-record-detail="viewRecordDetail"
      @withdraw-record="withdrawRecord"
      @open-supplement="openSupplement"
      @submit-supplement="submitSupplement"
    />

    <DashboardTab
      v-if="activeTab === 'dashboard'"
      :portfolio="portfolio"
      :dash-filter-type="dashFilterType"
      :type-labels="typeLabels"
      :status-labels="statusLabels"
      :status-variants="statusVariants"
      :jurisdiction-labels="jurisdictionLabels"
      :jurisdiction-flags="jurisdictionFlags"
      :ip-type-icons="ipTypeIcons"
      @update:dash-filter-type="dashFilterType = $event"
      @export-csv="handleExportPortfolio"
    />

    <CalculatorTab
      v-if="activeTab === 'calculator'"
      :calc-data="calcData"
      :fee-calc-result="feeCalcResult"
      :fee-jurisdictions="feeJurisdictions"
      :class-short-list="classShortList"
      :wipo-designation-options="wipoDesignationOptions"
      :key-labels="keyLabels"
      :trademark-fee-labels="trademarkFeeLabels"
      :design-patent-fee-labels="designPatentFeeLabels"
      @update:calc-data="calcData = $event"
      @toggle-jurisdiction="toggleFeeJurisdiction"
      @toggle-class="toggleClass"
      @toggle-designation="toggleDesignation"
      @calculate="handleFeeCalc"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useIprData } from '@/composables/useIprData'
import GuidelinesTab from '@/components/ipr/GuidelinesTab.vue'
import WizardTab from '@/components/ipr/WizardTab.vue'
import RegistrationsTab from '@/components/ipr/RegistrationsTab.vue'
import DashboardTab from '@/components/ipr/DashboardTab.vue'
import CalculatorTab from '@/components/ipr/CalculatorTab.vue'

// Shared state from composable
const {
  disclaimersAccepted, dismissDisclaimers, showDisclaimerDetails,
  acceptDisclaimers, loadGuidelines, switchJurisdiction,
  guidelineJurisdiction, guidelineCollapsed, currentGuidelines,
  hasGuidelinesContent, globalCategories, globalJurisdictions,
  records, filterType, filterStatus, loadRecords,
  portfolio, dashFilterType,
  iprApi, keyLabels, trademarkFeeLabels, designPatentFeeLabels,
  typeLabels, jurisdictionLabels, jurisdictionFlags, ipTypeIcons,
  statusLabels, statusVariants, sourceLabels, nextActionTypeLabels,
  disclaimerMessages,
} = useIprData()

// Tab navigation
const activeTab = ref('guidelines')
const tabs = [
  { key: 'guidelines', label: '📖 登记指引' },
  { key: 'assistant', label: '🪄 智能助手' },
  { key: 'registrations', label: '📋 登记记录' },
  { key: 'dashboard', label: '📊 IP资产' },
  { key: 'calculator', label: '💰 费用计算' },
]

// ─── Wizard state (Task 3 props) ──────────────
const wizardStep = ref(0)
const wizardData = ref({ ip_type: 'copyright', jurisdiction: 'cn', work_id: '', lawyer_consulted: '' })
const riskConfirmations = ref({
  not_law_firm: false, not_legal_advice: false, no_guarantee: false,
  class_miss: false, fee_reference: false,
})
const allRiskConfirmed = computed(() =>
  Object.values(riskConfirmations.value).every(Boolean),
)
const canProceedWithLawyerConfirm = computed(() => {
  if (!wizardData.value.lawyer_consulted) return false
  if (wizardData.value.lawyer_consulted === 'B') return allRiskConfirmed.value
  return true
})
const riskConfirmationLabels = {
  not_law_firm: '我理解 OriStudio 不构成律师事务所',
  not_legal_advice: '我理解系统信息仅供参考，不构成法律建议',
  no_guarantee: '我理解不保证注册成功',
  class_miss: '我理解商标类别推荐可能存在遗漏',
  fee_reference: '我理解费用估算仅供参考',
}
const worksList = ref<any[]>([])
const prefillResult = ref<any>(null)
const validateResult = ref<any>(null)
const generateResult = ref<any>(null)
const exportResult = ref<any>(null)
const recommendTags = ref('')
const recommendCreatorType = ref('')
const recommendResult = ref<any>(null)

try {
  const saved = localStorage.getItem('oristudio-creator-type')
  if (saved) recommendCreatorType.value = saved
} catch {}

const ipTypes = [
  { key: 'copyright', icon: '©️', label: '著作权', desc: '保护作品表达, 创作即获权, 登记强化维权证据' },
  { key: 'trademark', icon: '®️', label: '商标', desc: '保护品牌标识, 须注册方获专用权, 按类别保护' },
  { key: 'design_patent', icon: '🎨', label: '外观设计', desc: '保护产品外观造型, 如手办/盲盒/包装设计' },
  { key: 'utility_patent', icon: '💡', label: '专利', desc: '保护技术方案和发明, 含发明/实用新型' },
]
const jurisdictions = [
  { code: 'cn', flag: '🇨🇳', label: '中国', fee: '¥300起', duration: '6-12月' },
  { code: 'us', flag: '🇺🇸', label: '美国', fee: '$250-350', duration: '9-14月' },
  { code: 'eu', flag: '🇪🇺', label: '欧盟', fee: '€850', duration: '4-6月' },
  { code: 'wipo', flag: '🌐', label: 'WIPO国际', fee: 'CHF 653起', duration: '12-18月' },
]

// ─── Registration CRUD state (Task 4 props) ──
const showAddModal = ref(false)
const editingRecord = ref<any>(null)
const form = ref<any>({
  ip_type: 'copyright', jurisdiction: 'cn', application_no: '', registration_no: '',
  filing_date: '', registration_date: '', expiration_date: '',
  status: 'draft', official_fee: 0, total_cost: 0,
  agent_name: '', agent_fee: 0, official_url: '',
  next_action_date: '', next_action_type: '', notes: '',
})

function openAddModal() {
  editingRecord.value = null
  form.value = {
    ip_type: 'copyright', jurisdiction: 'cn', application_no: '', registration_no: '',
    filing_date: '', registration_date: '', expiration_date: '',
    status: 'draft', official_fee: 0, total_cost: 0,
    agent_name: '', agent_fee: 0, official_url: '',
    next_action_date: '', next_action_type: '', notes: '',
  }
  showAddModal.value = true
}

function editRecord(r: any) {
  editingRecord.value = r
  form.value = { ...r }
  showAddModal.value = true
}

async function saveRecord() {
  if (!form.value.ip_type || !form.value.jurisdiction) return
  if (!form.value.application_no?.trim() && !form.value.registration_no?.trim()) return
  if (!form.value.status) return
  try {
    if (editingRecord.value) {
      await iprApi.update(editingRecord.value.id, form.value)
    } else {
      await iprApi.create(form.value)
    }
    showAddModal.value = false
    editingRecord.value = null
    loadRecords()
    loadPortfolio()
    ;(window as any).$toast?.show('已保存', 'success')
  } catch {
    ;(window as any).$toast?.show('保存失败', 'error')
  }
}

async function deleteRecord(id: string) {
  if (!confirm('确认删除此记录？')) return
  try {
    await iprApi.delete(id)
    loadRecords()
    loadPortfolio()
    ;(window as any).$toast?.show('已删除', 'success')
  } catch {
    ;(window as any).$toast?.show('删除失败', 'error')
  }
}

const showDetailModal = ref(false)
const showSupplementModal = ref(false)
const detailRecord = ref<any>(null)
const supplementRecordId = ref('')
const supplementType = ref('')
const supplementNotes = ref('')

function viewRecordDetail(r: any) {
  detailRecord.value = {
    ...r,
    history: [
      { time: r.filing_date || '未知', action: '提交申请' },
      ...(r.status === 'registered' && r.registration_date
        ? [{ time: r.registration_date, action: '注册成功' }]
        : []),
    ].filter((h: any) => h.time !== '—' && h.time !== '未知'),
  }
  showDetailModal.value = true
}

async function withdrawRecord(id: string) {
  if (!confirm('确认撤回此登记申请？')) return
  try {
    await iprApi.update(id, { status: 'withdrawn' })
    loadRecords()
    loadPortfolio()
    ;(window as any).$toast?.show('已撤回', 'success')
  } catch {
    ;(window as any).$toast?.show('撤回失败', 'error')
  }
}

function openSupplement(r: any) {
  supplementRecordId.value = r.id
  supplementType.value = ''
  supplementNotes.value = ''
  showSupplementModal.value = true
}

async function submitSupplement() {
  if (!supplementRecordId.value || !supplementType.value) return
  try {
    await iprApi.update(supplementRecordId.value, {
      supplement_type: supplementType.value,
      supplement_notes: supplementNotes.value,
      status: 'supplemented',
    })
    showSupplementModal.value = false
    loadRecords()
    loadPortfolio()
    ;(window as any).$toast?.show('补充材料已提交', 'success')
  } catch {
    ;(window as any).$toast?.show('提交失败', 'error')
  }
}

// ─── Wizard handlers ──────────────────────────
async function loadWorks() {
  try {
    const res = await client.get('/works', { params: { page_size: 200 } })
    worksList.value = res.data.data?.items || res.data.data || []
  } catch { worksList.value = [] }
}

async function handlePrefill() {
  if (!wizardData.value.work_id) return
  try {
    const res = await iprApi.prefill({
      work_id: wizardData.value.work_id,
      ip_type: wizardData.value.ip_type,
      jurisdiction: wizardData.value.jurisdiction,
    })
    prefillResult.value = res.data.data
  } catch (e: any) {
    ;(window as any).$toast?.show('预填失败: ' + (e.response?.data?.detail || e.message), 'error')
  }
}

async function handleValidate() {
  const fields: Record<string, any> = {}
  if (prefillResult.value?.fields) {
    for (const f of prefillResult.value.fields) {
      fields[f.official_field] = f.value
    }
  }
  try {
    const res = await iprApi.validate({
      ip_type: wizardData.value.ip_type,
      jurisdiction: wizardData.value.jurisdiction,
      fields,
    })
    validateResult.value = res.data.data
  } catch {
    ;(window as any).$toast?.show('校验失败', 'error')
  }
}

async function handleGenerate() {
  const fields: Record<string, any> = {}
  if (prefillResult.value?.fields) {
    for (const f of prefillResult.value.fields) {
      fields[f.official_field] = f.value
    }
  }
  try {
    const res = await iprApi.generate({
      ip_type: wizardData.value.ip_type,
      jurisdiction: wizardData.value.jurisdiction,
      fields,
    })
    generateResult.value = res.data.data
  } catch {
    ;(window as any).$toast?.show('生成失败', 'error')
  }
}

async function handleExport() {
  try {
    const res = await iprApi.export({
      ip_type: wizardData.value.ip_type,
      jurisdiction: wizardData.value.jurisdiction,
    })
    exportResult.value = res.data.data
  } catch (e: any) {
    ;(window as any).$toast?.show(e.response?.data?.detail || '导出失败', 'error')
  }
}

async function handleRecommend() {
  const tags = recommendTags.value.split(/[,，]/).map(t => t.trim()).filter(Boolean)
  if (!tags.length && !recommendCreatorType.value) {
    ;(window as any).$toast?.show('请输入标签或选择创作者类型', 'warning')
    return
  }
  try {
    const res = await iprApi.recommendClasses({
      tags,
      creator_type: recommendCreatorType.value || undefined,
      jurisdiction: 'cn',
    })
    recommendResult.value = res.data.data
  } catch {
    ;(window as any).$toast?.show('推荐失败', 'error')
  }
}

function handleReset() {
  wizardData.value = { ip_type: 'copyright', jurisdiction: 'cn', work_id: '', lawyer_consulted: '' }
  prefillResult.value = null
  validateResult.value = null
  generateResult.value = null
  exportResult.value = null
  riskConfirmations.value = {
    not_law_firm: false, not_legal_advice: false, no_guarantee: false,
    class_miss: false, fee_reference: false,
  }
  wizardStep.value = 0
}

function handleSelectClass(classNo: number) {
  activeTab.value = 'assistant'
  recommendTags.value = ''
  setTimeout(() => handleRecommend(), 100)
}

// ─── Dashboard handlers ───────────────────────
async function loadPortfolio() {
  try {
    const res = await iprApi.portfolio()
    portfolio.value = res.data.data
  } catch { portfolio.value = null }
}

function handleExportPortfolio() {
  if (!portfolio.value) return
  const rows: string[][] = [['IP类型', '名称', '申请号', '注册号', '状态', '申请日期', '到期日', '官费(CNY)']]
  if (portfolio.value.items) {
    for (const item of portfolio.value.items) {
      rows.push([
        typeLabels[item.ip_type] || item.ip_type,
        item.name || '—',
        item.application_no || '—',
        item.registration_no || '—',
        statusLabels[item.status] || item.status,
        item.filing_date || '—',
        item.expiration_date || '—',
        String(item.official_fee || 0),
      ])
    }
  }
  const csv = rows.map(r => r.join(',')).join('\n')
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `ip_portfolio_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

// ─── Calculator handlers ──────────────────────
const calcData = ref({
  ip_type: 'trademark',
  jurisdictions: ['cn'] as string[],
  classes: [] as number[],
  design_count: 1,
  wipo_designations: [] as string[],
  is_color: false,
})
const feeCalcResult = ref<any>(null)
const feeJurisdictions = [
  { code: 'cn', flag: '🇨🇳', label: '中国' },
  { code: 'us', flag: '🇺🇸', label: '美国' },
  { code: 'eu', flag: '🇪🇺', label: '欧盟' },
  { code: 'wipo', flag: '🌐', label: 'WIPO' },
  { code: 'jp', flag: '🇯🇵', label: '日本' },
  { code: 'kr', flag: '🇰🇷', label: '韩国' },
]
const wipoDesignationOptions = [
  { code: 'eu', label: '🇪🇺 欧盟' },
  { code: 'us', label: '🇺🇸 美国' },
  { code: 'jp', label: '🇯🇵 日本' },
  { code: 'kr', label: '🇰🇷 韩国' },
  { code: 'cn', label: '🇨🇳 中国' },
]
const classShortList = ref<{ class_no: number; class_name_zh: string }[]>([])

async function loadClassShortList() {
  try {
    const res = await iprApi.niceClasses(true)
    classShortList.value = (res.data.data || []).map((c: any) => ({
      class_no: c.class_no,
      class_name_zh: c.class_name_zh,
    }))
  } catch {}
}

function toggleFeeJurisdiction(code: string) {
  const idx = calcData.value.jurisdictions.indexOf(code)
  if (idx >= 0) calcData.value.jurisdictions.splice(idx, 1)
  else calcData.value.jurisdictions.push(code)
}

function toggleClass(classNo: number) {
  const idx = calcData.value.classes.indexOf(classNo)
  if (idx >= 0) calcData.value.classes.splice(idx, 1)
  else calcData.value.classes.push(classNo)
}

function toggleDesignation(code: string) {
  const idx = calcData.value.wipo_designations.indexOf(code)
  if (idx >= 0) calcData.value.wipo_designations.splice(idx, 1)
  else calcData.value.wipo_designations.push(code)
}

async function handleFeeCalc() {
  if (!calcData.value.jurisdictions.length) {
    ;(window as any).$toast?.show('请至少选择一个辖区', 'warning')
    return
  }
  try {
    const params: any = {
      ip_type: calcData.value.ip_type,
      jurisdictions: calcData.value.jurisdictions,
    }
    if (calcData.value.ip_type === 'trademark' && calcData.value.classes.length) {
      params.classes = calcData.value.classes
    }
    if (calcData.value.ip_type === 'design_patent') {
      params.design_count = calcData.value.design_count
    }
    if (calcData.value.jurisdictions.includes('wipo')) {
      params.wipo_designations = calcData.value.wipo_designations.length ? calcData.value.wipo_designations : undefined
      params.is_color = calcData.value.is_color
    }
    const res = await iprApi.feeCalculator(params)
    feeCalcResult.value = res.data.data
  } catch (e: any) {
    ;(window as any).$toast?.show('计算失败: ' + (e.response?.data?.detail || e.message), 'error')
  }
}

onMounted(() => {
  loadGuidelines()
  loadRecords()
  loadWorks()
  loadPortfolio()
  loadClassShortList()
})
</script>

<style scoped>
.ipr-view { display:flex; flex-direction:column; gap:20px; }
.cat-tabs { display:flex; gap:8px; flex-wrap:wrap; }
.cat-tab { padding:8px 18px; border-radius:100px; font-size:.84rem; font-weight:600; cursor:pointer; border:1px solid var(--border); background:var(--surface); color:var(--muted); font-family:var(--font-body); transition:all .2s; }
.cat-tab.active { background:var(--accent); color:#fff; border-color:var(--accent); }
.disclaimer-bar { padding:10px 16px; background:oklch(62% 0.18 55 / 0.06); border:1px solid oklch(62% 0.18 55 / 0.2); border-radius:var(--radius-sm); font-size:.82rem; color:var(--orange); }
.modal-overlay { position:fixed; inset:0; background:oklch(0 0 0 / .4); backdrop-filter:blur(4px); z-index:9998; display:flex; align-items:center; justify-content:center; }
.modal-card { background:var(--surface); border-radius:var(--radius-xl); padding:28px; max-width:560px; width:90%; max-height:90vh; overflow-y:auto; box-shadow:0 16px 64px oklch(0 0 0 / .16); display:flex; flex-direction:column; gap:14px; }
.modal-header { display:flex; align-items:center; justify-content:space-between; }
.modal-header h3 { margin:0; }
.modal-close-btn { background:none; border:none; cursor:pointer; font-size:1.4rem; color:var(--muted); }
.modal-footer { display:flex; justify-content:flex-end; gap:10px; }
.form-group { display:flex; flex-direction:column; gap:6px; }
.form-group label { font-size:.82rem; font-weight:600; color:var(--muted); }
.form-input,.form-textarea { padding:10px 14px; border:1px solid var(--border); border-radius:var(--radius-sm); font-size:.88rem; font-family:var(--font-body); color:var(--fg); background:var(--surface); outline:none; }
.form-input:focus,.form-textarea:focus { border-color:var(--accent); box-shadow:0 0 0 3px oklch(56% 0.12 170 / .1); }
.form-textarea { resize:vertical; }
.btn-sm { padding:6px 12px; font-size:.78rem; }
.btn-accent { background:oklch(56% 0.12 260); color:#fff; border:none; }
.btn-accent:hover { opacity:0.85; }
.btn-danger { background:var(--red); color:#fff; border:none; }
.btn-danger:hover { opacity:0.85; }
.btn-warning { background: var(--orange); color: #fff; border: none; }
.btn-warning:hover { opacity: .85; }
.btn-info { background: var(--blue); color: #fff; border: none; }
.btn-info:hover { opacity: .85; }
.btn-primary.disabled { opacity: .5; cursor: not-allowed; }
.btn-primary.disabled:hover { opacity: .5; }
@media (max-width:768px) {
  .actions-bar { flex-direction:column; align-items:stretch; }
  .filter-group { flex-wrap:wrap; }
}
</style>
```

Note: The modal overlays (detail, supplement, add/edit) are kept inline in the main view since they're tightly coupled to the registrations flow and need z-index management.

- [ ] **Step 2: Move all shared CSS to individual components**

Move the CSS from IprView.vue into each component file:
- Guidelines CSS → GuidelinesTab.vue (`jurisdiction-bar`, `guideline-card`, `gl-*`, `fee-grid`, `materials-list`, `process-flow`, `country-grid`, `fee-example-*`, `sme-*`, `trademark-search-box`, `similarity-*`)
- Wizard CSS → WizardTab.vue (`wizard-steps`, `wizard-card`, `ip-type-grid`, `jurisdiction-grid`, `prefill-*`, `validate-*`, `export-*`, `category-recommender`, `rec-*`)
- Registrations CSS → RegistrationsTab.vue (`registrations`, `actions-bar`, `records-list`, `record-*`, `detail-*`, `lawyer-audit-*`, `audit-*`, `risk-confirm-*`)
- Dashboard CSS → DashboardTab.vue (`dashboard`, `stats-row`, `stat-card`, `summary-row`, `jurisdiction-stats`, `renewals-section`, `renewal-*`)
- Calculator CSS → CalculatorTab.vue (`calc-*`, `class-chip`, `selected-class-tag`)
- Shared CSS stays in IprView.vue (`.ipr-view`, `.cat-tabs`, `.disclaimer-bar`, modal styles, button styles)

- [ ] **Step 3: Verify the refactored view compiles**

Run: `npx vue-tsc --noEmit --pretty 2>&1 | grep IprView | head -10`

- [ ] **Step 4: Run Vitest to ensure nothing broke**

Run: `npx vitest run src/__tests__/` 
Expected: All existing tests still pass

- [ ] **Step 5: Commit**

```bash
git add frontend-web/src/views/IprView.vue frontend-web/src/components/ipr/
git commit -m "refactor(ipr): split IprView.vue into 5 tab components (~2000→~80 lines)"
```

---

### Task 8: Final verification

**Files:**
- All files in `frontend-web/src/components/ipr/`
- `frontend-web/src/views/IprView.vue`
- `frontend-web/src/composables/useIprData.ts`

**Steps:**

- [ ] **Step 1: Full type check**

Run: `npx vue-tsc --noEmit`
Expected: Zero errors

- [ ] **Step 2: Full test suite**

Run: `npx vitest run`
Expected: All 105 tests pass

- [ ] **Step 3: Verify file sizes**

Run: `wc -l frontend-web/src/views/IprView.vue frontend-web/src/composables/useIprData.ts frontend-web/src/components/ipr/*.vue`
Expected:
- IprView.vue: ~250-300 lines
- useIprData.ts: ~120 lines
- GuidelinesTab.vue: ~350-380 lines
- WizardTab.vue: ~380-400 lines
- RegistrationsTab.vue: ~120-130 lines
- DashboardTab.vue: ~70-80 lines
- CalculatorTab.vue: ~140-150 lines

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "refactor(ipr): finalize IprView splitting — all tabs under 400 lines"
```
