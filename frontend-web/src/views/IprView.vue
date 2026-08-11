<template>
  <div class="ipr-view">
    <!-- Disclaimer banner (top of page, always visible after initial acceptance) -->
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
      @toggle-collapse="guidelineCollapsed = !guidelineCollapsed"
      @select-class="handleSelectClass"
    />

    <WizardTab
      v-if="activeTab === 'assistant'"
      :active-tab="activeTab"
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
      :wizard-steps="wizardSteps"
      :source-labels="sourceLabels"
      @prev-step="wizardStep--"
      @next-step="wizardStep++"
      @prefill="handlePrefill"
      @validate="handleValidate"
      @generate="handleGenerate"
      @export="handleExport"
      @recommend="handleRecommend"
      @reset="handleReset"
    />

    <RegistrationsTab
      v-if="activeTab === 'registrations'"
      :active-tab="activeTab"
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
      :active-tab="activeTab"
      :portfolio="portfolio"
      :dash-filter-type="dashFilterType"
      :type-labels="typeLabels"
      :status-labels="statusLabels"
      :status-variants="statusVariants"
      :jurisdiction-labels="jurisdictionLabels"
      :jurisdiction-flags="jurisdictionFlags"
      :ip-type-icons="ipTypeIcons"
      @update:dash-filter-type="dashFilterType = $event"
      @load-portfolio="loadPortfolio()"
      @export-csv="handleExportPortfolio"
    />

    <CalculatorTab
      v-if="activeTab === 'calculator'"
      :active-tab="activeTab"
      :calc-data="calcData"
      :fee-calc-result="feeCalcResult"
      :fee-jurisdictions="feeJurisdictions"
      :class-short-list="classShortList"
      :wipo-designation-options="wipoDesignationOptions"
      :ip-types="ipTypes"
      :jurisdiction-flags="jurisdictionFlags"
      @update:calc-data="calcData = $event"
      @toggle-jurisdiction="toggleFeeJurisdiction"
      @toggle-class="toggleClass"
      @toggle-designation="toggleDesignation"
      @calculate="handleFeeCalc"
    />

    <!-- ==================== Detail Modal ==================== -->
    <div v-if="showDetailModal" class="modal-overlay" @click.self="showDetailModal = false">
      <div class="modal-card animate-scale-in" style="max-width:640px">
        <div class="modal-header"><h3>📄 登记记录详情</h3><button class="modal-close-btn" @click="showDetailModal = false">×</button></div>
        <div v-if="detailRecord" class="detail-content">
          <div class="detail-header-card">
            <span class="record-type">{{ typeLabels[detailRecord.ip_type] || detailRecord.ip_type }}</span>
            <span class="record-jurisdiction">{{ jurisdictionLabels[detailRecord.jurisdiction] || detailRecord.jurisdiction }}</span>
            <StatusBadge :status="detailRecord.status" :labels="statusLabels" :variants="statusVariants" />
          </div>
          <div class="detail-grid">
            <div class="detail-field"><label>申请号</label><span>{{ detailRecord.application_no || '—' }}</span></div>
            <div class="detail-field"><label>注册号</label><span>{{ detailRecord.registration_no || '—' }}</span></div>
            <div class="detail-field"><label>申请日期</label><span>{{ detailRecord.filing_date || '—' }}</span></div>
            <div class="detail-field"><label>注册日期</label><span>{{ detailRecord.registration_date || '—' }}</span></div>
            <div class="detail-field"><label>到期日</label><span>{{ detailRecord.expiration_date || '—' }}</span></div>
            <div class="detail-field"><label>官费</label><span>{{ detailRecord.official_fee ? '¥' + detailRecord.official_fee : '—' }}</span></div>
            <div class="detail-field"><label>总费用</label><span>{{ detailRecord.total_cost ? '¥' + detailRecord.total_cost : '—' }}</span></div>
            <div class="detail-field"><label>代理机构</label><span>{{ detailRecord.agent_name || '—' }}</span></div>
            <div class="detail-field"><label>代理费</label><span>{{ detailRecord.agent_fee ? '¥' + detailRecord.agent_fee : '—' }}</span></div>
            <div class="detail-field"><label>下次动作</label><span>{{ detailRecord.next_action_date ? detailRecord.next_action_date + ' (' + nextActionTypeLabels[detailRecord.next_action_type] + ')' : '—' }}</span></div>
          </div>
          <div v-if="detailRecord.notes" class="detail-notes">
            <h5>备注</h5>
            <p>{{ detailRecord.notes }}</p>
          </div>
          <div v-if="detailRecord.official_url" class="detail-links">
            <a :href="detailRecord.official_url" target="_blank" class="btn btn-secondary btn-sm">🔗 官方链接</a>
          </div>
          <div v-if="detailRecord.history && detailRecord.history.length" class="detail-history">
            <h5>操作历史</h5>
            <div v-for="(h, i) in detailRecord.history" :key="i" class="history-item">
              <span class="history-time">{{ h.time }}</span>
              <span class="history-action">{{ h.action }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== Supplement Modal ==================== -->
    <div v-if="showSupplementModal" class="modal-overlay" @click.self="showSupplementModal = false">
      <div class="modal-card animate-scale-in">
        <div class="modal-header"><h3>📎 补充材料</h3><button class="modal-close-btn" @click="showSupplementModal = false">×</button></div>
        <div class="form-group">
          <label>补充材料类型</label>
          <select v-model="supplementType" class="form-input">
            <option value="">请选择</option>
            <option value="image">补充图片/图样</option>
            <option value="document">补充证明文件</option>
            <option value="description">补充说明文字</option>
            <option value="other">其他</option>
          </select>
        </div>
        <div class="form-group">
          <label>材料说明</label>
          <textarea v-model="supplementNotes" class="form-textarea" rows="3" placeholder="请描述补充的材料内容..."></textarea>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showSupplementModal = false">取消</button>
          <button class="btn btn-primary" @click="submitSupplement" :disabled="!supplementType">提交补充</button>
        </div>
      </div>
    </div>

    <!-- ==================== Add/Edit Modal ==================== -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
      <div class="modal-card animate-scale-in">
        <div class="modal-header"><h3>{{ editingRecord ? '编辑' : '新增' }}登记记录</h3><button class="modal-close-btn" @click="showAddModal = false">×</button></div>
        <div class="form-group">
          <label>IP 类型</label>
          <select v-model="form.ip_type" class="form-input">
            <option value="copyright">著作权</option>
            <option value="trademark">商标</option>
            <option value="design_patent">外观设计</option>
            <option value="utility_patent">专利</option>
          </select>
        </div>
        <div class="form-group">
          <label>辖区</label>
          <select v-model="form.jurisdiction" class="form-input">
            <option value="cn">中国</option>
            <option value="us">美国</option>
            <option value="eu">欧盟</option>
            <option value="jp">日本</option>
            <option value="kr">韩国</option>
            <option value="wipo">WIPO</option>
          </select>
        </div>
        <div class="form-group"><label>申请号</label><input v-model="form.application_no" class="form-input" /></div>
        <div class="form-group"><label>注册号</label><input v-model="form.registration_no" class="form-input" /></div>
        <div class="form-group"><label>申请日期</label><input v-model="form.filing_date" type="date" class="form-input" /></div>
        <div class="form-group"><label>注册日期</label><input v-model="form.registration_date" type="date" class="form-input" /></div>
        <div class="form-group"><label>到期日</label><input v-model="form.expiration_date" type="date" class="form-input" /></div>
        <div class="form-group"><label>状态</label>
          <select v-model="form.status" class="form-input">
            <option value="draft">草稿</option><option value="filed">已提交</option><option value="under_review">审查中</option><option value="registered">已注册</option><option value="rejected">已驳回</option><option value="expired">已过期</option><option value="withdrawn">已撤回</option><option value="supplemented">已补充</option>
          </select>
        </div>
        <div class="form-group"><label>官费 (CNY)</label><input v-model.number="form.official_fee" type="number" class="form-input" /></div>
        <div class="form-group"><label>总费用 (CNY)</label><input v-model.number="form.total_cost" type="number" class="form-input" /></div>
        <div class="form-group"><label>代理机构</label><input v-model="form.agent_name" class="form-input" /></div>
        <div class="form-group"><label>代理费 (CNY)</label><input v-model.number="form.agent_fee" type="number" class="form-input" /></div>
        <div class="form-group"><label>官方链接</label><input v-model="form.official_url" class="form-input" /></div>
        <div class="form-group"><label>下次动作日期</label><input v-model="form.next_action_date" type="date" class="form-input" /></div>
        <div class="form-group"><label>下次动作类型</label>
          <select v-model="form.next_action_type" class="form-input">
            <option value="">无</option>
            <option value="renewal">续展</option>
            <option value="annuity">年费</option>
            <option value="declaration_of_use">使用声明</option>
          </select>
        </div>
        <div class="form-group"><label>备注</label><textarea v-model="form.notes" class="form-textarea" rows="2"></textarea></div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showAddModal = false">取消</button>
          <button class="btn btn-primary" @click="saveRecord">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  disclaimersAccepted, dismissDisclaimers, showDisclaimerDetails,
  acceptDisclaimers, loadGuidelines, switchJurisdiction,
  guidelineJurisdiction, guidelineCollapsed, currentGuidelines,
  hasGuidelinesContent, globalCategories, globalJurisdictions,
  records, filterType, filterStatus, loadRecords,
  portfolio, dashFilterType, loadPortfolio,
  typeLabels, jurisdictionLabels, jurisdictionFlags, ipTypeIcons,
  statusLabels, statusVariants, sourceLabels, nextActionTypeLabels, keyLabels,
  trademarkFeeLabels, designPatentFeeLabels,
  disclaimerMessages,
} from '@/composables/useIprData'
import GuidelinesTab from '@/components/ipr/GuidelinesTab.vue'
import WizardTab from '@/components/ipr/WizardTab.vue'
import RegistrationsTab from '@/components/ipr/RegistrationsTab.vue'
import DashboardTab from '@/components/ipr/DashboardTab.vue'
import CalculatorTab from '@/components/ipr/CalculatorTab.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import client from '@/api/client'

// ─── Tab navigation ──────────────────────────
const activeTab = ref('guidelines')
const tabs = [
  { key: 'guidelines', label: '📖 登记指引' },
  { key: 'assistant', label: '🪄 智能助手' },
  { key: 'registrations', label: '📋 登记记录' },
  { key: 'dashboard', label: '📊 IP资产' },
  { key: 'calculator', label: '💰 费用计算' },
]

// ─── Wizard state ────────────────────────────
const wizardSteps = ['选择IP类型', '选择辖区', '自动预填', '校验', '律师审核确认', '导出']
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

import { useGlobalState } from '@/stores/useGlobalState'

try {
  const globalState = useGlobalState()
  const saved = localStorage.getItem('oristudio-creator-type')
  if (saved) {
    recommendCreatorType.value = saved
    globalState.setCreatorType(saved)
  }
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

async function loadWorks() {
  try {
    const res = await client.get('/works', { params: { page_size: 200 } })
    worksList.value = res.data.data?.items || res.data.data || []
  } catch { worksList.value = [] }
}

// ─── Registration CRUD state ─────────────────
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
  form.value = {
    ip_type: r.ip_type, jurisdiction: r.jurisdiction || 'cn',
    application_no: r.application_no || '', registration_no: r.registration_no || '',
    filing_date: r.filing_date || '', registration_date: r.registration_date || '',
    expiration_date: r.expiration_date || '', status: r.status,
    official_fee: r.official_fee || 0, total_cost: r.total_cost || 0,
    agent_name: r.agent_name || '', agent_fee: r.agent_fee || 0,
    official_url: r.official_url || '',
    next_action_date: r.next_action_date || '', next_action_type: r.next_action_type || '',
    notes: r.notes || '',
  }
  showAddModal.value = true
}

async function saveRecord() {
  const f = form.value
  if (!f.ip_type) {
    ;(window as any).$toast?.show('请选择知识产权类型', 'warning')
    return
  }
  if (!f.jurisdiction) {
    ;(window as any).$toast?.show('请选择管辖区域', 'warning')
    return
  }
  if (!f.application_no?.trim() && !f.registration_no?.trim()) {
    ;(window as any).$toast?.show('请输入申请号或注册号', 'warning')
    return
  }
  if (!f.status) {
    ;(window as any).$toast?.show('请选择状态', 'warning')
    return
  }
  try {
    const { iprApi } = await import('@/api/ipr')
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
    const { iprApi } = await import('@/api/ipr')
    await iprApi.delete(id)
    loadRecords()
    loadPortfolio()
    ;(window as any).$toast?.show('已删除', 'success')
  } catch {
    ;(window as any).$toast?.show('删除失败', 'error')
  }
}

// ─── Record Detail & Actions ─────────────────
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
  if (!confirm('确认撤回此登记申请？撤回后可重新提交。')) return
  try {
    const { iprApi } = await import('@/api/ipr')
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
    const { iprApi } = await import('@/api/ipr')
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

// ─── Wizard handlers ─────────────────────────
async function handlePrefill() {
  if (!wizardData.value.work_id) return
  try {
    const { iprApi } = await import('@/api/ipr')
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
    const { iprApi } = await import('@/api/ipr')
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
    const { iprApi } = await import('@/api/ipr')
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
    const { iprApi } = await import('@/api/ipr')
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
    const { iprApi } = await import('@/api/ipr')
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

// ─── Dashboard handlers ──────────────────────
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

// ─── Calculator state ────────────────────────
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
    const { iprApi } = await import('@/api/ipr')
    const res = await iprApi.niceClasses(true)
    classShortList.value = (res.data.data || []).map((c: any) => ({
      class_no: c.class_no,
      class_name_zh: c.class_name_zh,
    }))
  } catch { /* fallback */ }
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
    const { iprApi } = await import('@/api/ipr')
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

/* ── Tabs ────────────────────────────────────── */
.cat-tabs { display:flex; gap:8px; flex-wrap:wrap; }
.cat-tab { padding:8px 18px; border-radius:100px; font-size:.84rem; font-weight:600; cursor:pointer; border:1px solid var(--border); background:var(--surface); color:var(--muted); font-family:var(--font-body); transition:all .2s; }
.cat-tab.active { background:var(--accent); color:#fff; border-color:var(--accent); }

/* ── Disclaimer ──────────────────────────────── */
.disclaimer-bar { padding:10px 16px; background:oklch(62% 0.18 55 / 0.06); border:1px solid oklch(62% 0.18 55 / 0.2); border-radius:var(--radius-sm); font-size:.82rem; color:var(--orange); }

/* ── Inline disclaimer banner ──────────────────── */
.disclaimer-banner {
  margin-bottom: 16px;
  padding: 16px 20px;
  border: 1px solid oklch(72% 0.18 40 / 0.15);
  border-radius: var(--radius-md);
  background: oklch(72% 0.18 40 / 0.04);
}
.disclaimer-banner-header {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;
}
.disclaimer-banner-header strong { font-size: .92rem; }
.disclaimer-banner .disclaimer-list {
  display: flex; flex-direction: column; gap: 8px;
  padding: 12px; background: oklch(96% .003 240);
  border-radius: var(--radius-sm);
  max-height: 30vh; overflow-y: auto;
}
.disclaimer-banner .disclaimer-footer {
  margin-top: 12px; display: flex; align-items: center; gap: 16px; flex-wrap: wrap;
}
.disclaimer-list {
  display: flex; flex-direction: column; gap: 10px;
  padding: 16px; background: oklch(96% .003 240);
  border-radius: var(--radius-sm);
  max-height: 40vh; overflow-y: auto;
}
.disclaimer-item {
  display: flex; gap: 10px; align-items: flex-start;
  font-size: .84rem; line-height: 1.5; color: var(--fg);
}
.disclaimer-num {
  min-width: 28px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  background: var(--accent); color: #fff;
  border-radius: 50%; font-size: .78rem; font-weight: 700;
  flex-shrink: 0;
}
.disclaimer-footer { margin-top: 8px; display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
.disclaimer-checkbox-label {
  display: flex; align-items: center; gap: 6px;
  font-size: 0.82rem; color: var(--muted); cursor: pointer;
}
.disclaimer-checkbox-label input { width: 15px; height: 15px; cursor: pointer; }

/* ── Modal & Form ────────────────────────────── */
.btn-sm { padding:6px 12px; font-size:.78rem; }
.btn-accent { background:oklch(56% 0.12 260); color:#fff; border:none; }
.btn-accent:hover { opacity:0.85; }
.btn-danger { background:var(--red); color:#fff; border:none; }
.btn-danger:hover { opacity:0.85; }
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

/* ── Detail & Supplement Modals ─────────────────── */
.detail-header-card { display: flex; gap: 8px; align-items: center; padding: 12px; background: oklch(96% .003 240); border-radius: var(--radius-sm); margin-bottom: 12px; }
.detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px; }
.detail-field label { font-size: .72rem; color: var(--muted); font-weight: 600; display: block; }
.detail-field span { font-size: .85rem; }
.detail-notes { margin-top: 12px; }
.detail-notes h5 { margin: 0 0 4px; font-size: .85rem; }
.detail-notes p { font-size: .82rem; color: var(--muted); margin: 0; }
.detail-links { margin-top: 12px; }
.detail-history { margin-top: 12px; }
.detail-history h5 { margin: 0 0 6px; font-size: .85rem; }
.history-item { display: flex; gap: 12px; font-size: .78rem; padding: 4px 0; }
.history-time { color: var(--muted); min-width: 100px; }
.history-action { color: var(--fg); }

.btn-lg { padding: 12px 32px; font-size: .95rem; }
.btn-warning { background: var(--orange); color: #fff; border: none; }
.btn-warning:hover { opacity: .85; }
.btn-info { background: var(--blue); color: #fff; border: none; }
.btn-info:hover { opacity: .85; }
.btn-neutral { background: var(--muted); color: #fff; border: none; }
.btn-primary.disabled {
  opacity: .5;
  cursor: not-allowed;
}
.btn-primary.disabled:hover { opacity: .5; }

@media (max-width:768px) {
  .stats-row { grid-template-columns:1fr 1fr; }
  .summary-row { flex-wrap:wrap; gap:16px; }
  .ip-type-grid { grid-template-columns:1fr; }
  .jurisdiction-grid { grid-template-columns:1fr; }
  .prefill-fields { grid-template-columns:1fr; }
  .record-body { grid-template-columns:1fr 1fr; }
  .category-grid { grid-template-columns:1fr; }
  .actions-bar { flex-direction:column; align-items:stretch; }
  .filter-group { flex-wrap:wrap; }
}
</style>
