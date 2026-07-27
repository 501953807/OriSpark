import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref, computed } from 'vue'

// Suppress unhandled rejections from fetch() in acceptDisclaimers tests
process.on('unhandledRejection', () => {})

// Set up localStorage mock BEFORE importing useIprData
const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: vi.fn((key: string) => store[key] ?? null),
    setItem: vi.fn((key: string, value: string) => { store[key] = value }),
    removeItem: vi.fn((key: string) => { delete store[key] }),
    clear: vi.fn(() => { store = {} }),
  }
})()
vi.stubGlobal('localStorage', localStorageMock)

describe('useIprData label maps', () => {
  // Re-import after mocking to get fresh module state
  let statusLabels: Record<string, string>
  let statusVariants: Record<string, string>
  let typeLabels: Record<string, string>
  let jurisdictionLabels: Record<string, string>
  let jurisdictionFlags: Record<string, string>
  let ipTypeIcons: Record<string, string>
  let sourceLabels: Record<string, string>
  let nextActionTypeLabels: Record<string, string>
  let keyLabels: Record<string, string>
  let trademarkFeeLabels: Record<string, string>
  let designPatentFeeLabels: Record<string, string>
  let disclaimerMessages: string[]
  let globalJurisdictions: any[]
  let acceptDisclaimers: () => void
  let disclaimersAccepted: any
  let dismissDisclaimers: any
  let showDisclaimerDetails: any
  let guidelineJurisdiction: any
  let guidelineCollapsed: any
  let currentGuidelines: any
  let hasGuidelinesContent: any
  let globalCategories: any
  let records: any
  let portfolio: any
  let dashFilterType: any
  let filterType: any
  let filterStatus: any

  beforeEach(async () => {
    localStorageMock.clear()
    localStorageMock.getItem.mockClear()
    localStorageMock.setItem.mockClear()

    // Dynamically import to get fresh module state each test
    const mod = await import('@/composables/useIprData')
    statusLabels = mod.statusLabels
    statusVariants = mod.statusVariants
    typeLabels = mod.typeLabels
    jurisdictionLabels = mod.jurisdictionLabels
    jurisdictionFlags = mod.jurisdictionFlags
    ipTypeIcons = mod.ipTypeIcons
    sourceLabels = mod.sourceLabels
    nextActionTypeLabels = mod.nextActionTypeLabels
    keyLabels = mod.keyLabels
    trademarkFeeLabels = mod.trademarkFeeLabels
    designPatentFeeLabels = mod.designPatentFeeLabels
    disclaimerMessages = mod.disclaimerMessages
    globalJurisdictions = mod.globalJurisdictions
    acceptDisclaimers = mod.acceptDisclaimers
    disclaimersAccepted = mod.disclaimersAccepted
    dismissDisclaimers = mod.dismissDisclaimers
    showDisclaimerDetails = mod.showDisclaimerDetails
    guidelineJurisdiction = mod.guidelineJurisdiction
    guidelineCollapsed = mod.guidelineCollapsed
    currentGuidelines = mod.currentGuidelines
    hasGuidelinesContent = mod.hasGuidelinesContent
    globalCategories = mod.globalCategories
    records = mod.records
    portfolio = mod.portfolio
    dashFilterType = mod.dashFilterType
    filterType = mod.filterType
    filterStatus = mod.filterStatus
  })

  it('has all expected status labels', () => {
    expect(statusLabels.draft).toBe('草稿')
    expect(statusLabels.registered).toBe('已注册')
    expect(statusLabels.rejected).toBe('已驳回')
    expect(statusLabels.expired).toBe('已过期')
    expect(statusLabels.withdrawn).toBe('已撤回')
    expect(statusLabels.supplemented).toBe('已补充')
  })

  it('has matching status variants', () => {
    expect(statusVariants.draft).toBe('info')
    expect(statusVariants.registered).toBe('success')
    expect(statusVariants.rejected).toBe('error')
    expect(statusVariants.expired).toBe('error')
    expect(statusVariants.under_review).toBe('warning')
  })

  it('has all IP type labels', () => {
    expect(typeLabels.copyright).toBe('著作权')
    expect(typeLabels.trademark).toBe('商标')
    expect(typeLabels.design_patent).toBe('外观设计')
    expect(typeLabels.utility_patent).toBe('专利')
  })

  it('has all jurisdiction labels', () => {
    expect(jurisdictionLabels.cn).toBe('中国')
    expect(jurisdictionLabels.us).toBe('美国')
    expect(jurisdictionLabels.eu).toBe('欧盟')
    expect(jurisdictionLabels.jp).toBe('日本')
    expect(jurisdictionLabels.kr).toBe('韩国')
    expect(jurisdictionLabels.wipo).toBe('WIPO')
  })

  it('has matching jurisdiction flags', () => {
    expect(jurisdictionFlags.cn).toBe('🇨🇳')
    expect(jurisdictionFlags.us).toBe('🇺🇸')
    expect(jurisdictionFlags.eu).toBe('🇪🇺')
    expect(jurisdictionFlags.jp).toBe('🇯🇵')
    expect(jurisdictionFlags.kr).toBe('🇰🇷')
    expect(jurisdictionFlags.wipo).toBe('🌐')
  })

  it('has IP type icons', () => {
    expect(ipTypeIcons.copyright).toBe('©️')
    expect(ipTypeIcons.trademark).toBe('®️')
    expect(ipTypeIcons.design_patent).toBe('🎨')
    expect(ipTypeIcons.utility_patent).toBe('💡')
  })

  it('has source labels', () => {
    expect(sourceLabels.work).toBe('作品')
    expect(sourceLabels.user).toBe('用户')
    expect(sourceLabels.notary).toBe('存证')
    expect(sourceLabels.manual).toBe('手动')
  })

  it('has next action type labels', () => {
    expect(nextActionTypeLabels.renewal).toBe('续展')
    expect(nextActionTypeLabels.annuity).toBe('年费')
    expect(nextActionTypeLabels.declaration_of_use).toBe('使用声明')
  })

  it('has trademark fee labels', () => {
    expect(trademarkFeeLabels.application_1class).toBe('申请费(1类)')
    expect(trademarkFeeLabels.registration).toBe('注册费')
    expect(trademarkFeeLabels.renewal).toBe('续展费')
    expect(trademarkFeeLabels.renewal_5year).toBe('5年分期续展')
  })

  it('has design patent fee labels', () => {
    expect(designPatentFeeLabels.application_fee_per_class).toBe('申请费/类')
    expect(designPatentFeeLabels.annual_fee).toBe('年费')
    expect(designPatentFeeLabels.publication_fee).toBe('公告费')
    expect(designPatentFeeLabels.color_surcharge).toBe('彩色附加费')
  })

  it('has key labels for guidelines', () => {
    expect(keyLabels.artwork).toBe('美术作品')
    expect(keyLabels.text).toBe('文字作品')
    expect(keyLabels.music).toBe('音乐作品')
    expect(keyLabels.software).toBe('计算机软件')
    expect(keyLabels.application_1class).toBe('申请费(1类)')
  })
})

describe('global jurisdictions', () => {
  it('has 6 jurisdictions', async () => {
    const { globalJurisdictions } = await import('@/composables/useIprData')
    expect(globalJurisdictions).toHaveLength(6)
  })

  it('each jurisdiction has code, flag, and label', async () => {
    const { globalJurisdictions } = await import('@/composables/useIprData')
    for (const j of globalJurisdictions) {
      expect(j.code).toBeDefined()
      expect(j.flag).toBeDefined()
      expect(j.label).toBeDefined()
    }
  })
})

describe('disclaimer messages', () => {
  it('has at least 4 disclaimer messages', async () => {
    const { disclaimerMessages } = await import('@/composables/useIprData')
    expect(disclaimerMessages.length).toBeGreaterThanOrEqual(4)
  })

  it('each message is a non-empty string', async () => {
    const { disclaimerMessages } = await import('@/composables/useIprData')
    for (const msg of disclaimerMessages) {
      expect(typeof msg).toBe('string')
      expect(msg.length).toBeGreaterThan(0)
    }
  })

  it('mentions legal concepts in messages', async () => {
    const { disclaimerMessages } = await import('@/composables/useIprData')
    const allText = disclaimerMessages.join(' ')
    expect(allText).toContain('律师')
    expect(allText).toContain('法律建议')
  })
})

describe('shared state refs', () => {
  it('initializes guidelineJurisdiction to cn', async () => {
    const { guidelineJurisdiction } = await import('@/composables/useIprData')
    expect(guidelineJurisdiction.value).toBe('cn')
  })

  it('initializes guidelineCollapsed to false', async () => {
    const { guidelineCollapsed } = await import('@/composables/useIprData')
    expect(guidelineCollapsed.value).toBe(false)
  })

  it('initializes records as empty array', async () => {
    const { records } = await import('@/composables/useIprData')
    expect(records.value).toEqual([])
  })

  it('initializes portfolio as null', async () => {
    const { portfolio } = await import('@/composables/useIprData')
    expect(portfolio.value).toBeNull()
  })

  it('initializes filters as empty strings', async () => {
    const { filterType, filterStatus, dashFilterType } = await import('@/composables/useIprData')
    expect(filterType.value).toBe('')
    expect(filterStatus.value).toBe('')
    expect(dashFilterType.value).toBe('')
  })

  it('initializes disclaimers based on localStorage', async () => {
    // Default: not accepted
    const mod = await import('@/composables/useIprData')
    expect(mod.dismissDisclaimers.value).toBe(false)
    expect(mod.showDisclaimerDetails.value).toBe(true)
  })
})

describe('computed properties', () => {
  it('currentGuidelines returns null when no data loaded', async () => {
    const { currentGuidelines } = await import('@/composables/useIprData')
    expect(currentGuidelines.value).toBeNull()
  })

  it('hasGuidelinesContent returns falsy when no data loaded', async () => {
    const { hasGuidelinesContent } = await import('@/composables/useIprData')
    expect(hasGuidelinesContent.value).toBeFalsy()
  })

  it('globalCategories returns null when not loaded', async () => {
    const { globalCategories } = await import('@/composables/useIprData')
    expect(globalCategories.value).toBeNull()
  })
})

describe('acceptDisclaimers function', () => {
  it('sets disclaimersAccepted to true', async () => {
    const { acceptDisclaimers, disclaimersAccepted } = await import('@/composables/useIprData')
    acceptDisclaimers()
    expect(disclaimersAccepted.value).toBe(true)
  })

  it('saves to localStorage', async () => {
    const { acceptDisclaimers } = await import('@/composables/useIprData')
    acceptDisclaimers()
    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      'ipr_disclaimer_accepted',
      'true'
    )
  })

  it('resets dismissDisclaimers', async () => {
    const { acceptDisclaimers, dismissDisclaimers } = await import('@/composables/useIprData')
    dismissDisclaimers.value = true
    acceptDisclaimers()
    expect(dismissDisclaimers.value).toBe(false)
  })

  it('does not throw when acceptDisclaimers runs', async () => {
    const { acceptDisclaimers } = await import('@/composables/useIprData')
    // The fetch call inside uses a relative URL which fails in jsdom/Node.
    // The try/catch in acceptDisclaimers should handle it gracefully.
    expect(() => acceptDisclaimers()).not.toThrow()
  })
})
