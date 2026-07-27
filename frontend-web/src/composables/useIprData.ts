import { ref, computed } from 'vue'
import { iprApi } from '@/api/ipr'

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
export const disclaimersAccepted = ref(localStorage.getItem('ipr_disclaimer_accepted') === 'true')
export const dismissDisclaimers = ref(false)
export const showDisclaimerDetails = ref(true)

export const guidelineJurisdiction = ref('cn')
export const guidelineCollapsed = ref(false)
const guidelinesData = ref<Record<string, any>>({})

export const currentGuidelines = computed(() => guidelinesData.value[guidelineJurisdiction.value] || null)
export const hasGuidelinesContent = computed(() => {
  const cg = currentGuidelines.value
  return cg && (cg.copyright || cg.trademark || cg.design_patent || cg.sme_fund)
})
export const globalCategories = computed(() => guidelinesData.value['categories'] || null)

export const records = ref<any[]>([])
export const portfolio = ref<any>(null)
export const dashFilterType = ref('')
export const filterType = ref('')
export const filterStatus = ref('')

// ─── Disclaimer Messages ───────────────────────
export const disclaimerMessages = [
  '1. 不构成律师-客户关系：OriStudio 是软件工具，不是律师事务所。使用本软件不建立律师-客户特权关系。',
  '2. 不构成法律建议：系统提供的IP登记指引、分类推荐、费用估算仅供参考，不构成正式法律意见。做法律决策前应咨询持证律师。',
  '3. 不保证注册成功：系统辅助准备申请材料，不保证商标/版权/专利注册一定成功。注册结果取决于官方审查。',
  '7. 司法管辖区限制：IP登记指引覆盖中国/美国/欧盟/WIPO主要辖区，不包括所有国家/地区。',
]

// ─── Global Jurisdictions ──────────────────────
export const globalJurisdictions = [
  { code: 'cn', flag: '🇨🇳', label: '中国' },
  { code: 'us', flag: '🇺🇸', label: '美国' },
  { code: 'eu', flag: '🇪🇺', label: '欧盟' },
  { code: 'wipo', flag: '🌐', label: 'WIPO' },
  { code: 'jp', flag: '🇯🇵', label: '日本' },
  { code: 'kr', flag: '🇰🇷', label: '韩国' },
]

// ─── Shared Functions ──────────────────────────
export function acceptDisclaimers() {
  disclaimersAccepted.value = true
  localStorage.setItem('ipr_disclaimer_accepted', 'true')
  dismissDisclaimers.value = false
  try {
    fetch('/api/system/disclaimers/accept', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ disclaimer_key: 'no_legal_advice', context: 'ipr_first_entry' }),
    }).catch(() => {})
  } catch {}
}

export async function loadGuidelines() {
  const res = await iprApi.guidelines(guidelineJurisdiction.value)
  const data = res.data.data
  if (data.jurisdiction) {
    guidelinesData.value[data.jurisdiction] = data.guidelines
  } else {
    guidelinesData.value = data.guidelines || data
  }
}

export async function switchJurisdiction(jur: string) {
  guidelineJurisdiction.value = jur
  await loadGuidelines()
}

export async function loadRecords() {
  const params: any = {}
  if (filterType.value) params.ip_type = filterType.value
  if (filterStatus.value) params.status = filterStatus.value
  const res = await iprApi.registrations(params)
  records.value = res.data.data
}

export async function loadPortfolio() {
  try {
    const res = await iprApi.portfolio()
    portfolio.value = res.data.data
  } catch { portfolio.value = null }
}
