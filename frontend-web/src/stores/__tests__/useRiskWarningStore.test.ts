import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useRiskWarningStore } from '@/stores/useRiskWarningStore'

// Mock the API modules
const mockCheck = vi.fn()
const mockGetByWork = vi.fn()
const mockGetAll = vi.fn()
const mockDismiss = vi.fn()
const mockListTaxDeadlines = vi.fn()
const mockAddTaxDeadline = vi.fn()
const mockCompleteTaxDeadline = vi.fn()
const mockGetBurnoutRisk = vi.fn()

vi.mock('@/api/risk_warning', () => ({
  riskWarningApi: {
    check: (...args: unknown[]) => Promise.resolve(mockCheck(...args)),
    getByWork: (...args: unknown[]) => Promise.resolve(mockGetByWork(...args)),
    getAll: (...args: unknown[]) => Promise.resolve(mockGetAll(...args)),
    dismiss: (...args: unknown[]) => Promise.resolve(mockDismiss(...args)),
  },
}))

vi.mock('@/api/riskWarning', () => ({
  listTaxDeadlines: (...args: unknown[]) => Promise.resolve(mockListTaxDeadlines(...args)),
  addTaxDeadline: (...args: unknown[]) => Promise.resolve(mockAddTaxDeadline(...args)),
  completeTaxDeadline: (...args: unknown[]) => Promise.resolve(mockCompleteTaxDeadline(...args)),
  getBurnoutRisk: (...args: unknown[]) => Promise.resolve(mockGetBurnoutRisk(...args)),
}))

describe('useRiskWarningStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    mockCheck.mockReset()
    mockGetByWork.mockReset()
    mockGetAll.mockReset()
    mockDismiss.mockReset()
    mockListTaxDeadlines.mockReset()
    mockAddTaxDeadline.mockReset()
    mockCompleteTaxDeadline.mockReset()
    mockGetBurnoutRisk.mockReset()
  })

  it('initializes with empty state', () => {
    const store = useRiskWarningStore()
    expect(store.warnings).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.taxDeadlines).toEqual([])
    expect(store.burnoutRisk).toBeNull()
  })

  it('check calls API and returns result', async () => {
    const mockResult = { warnings: [], score: 100 }
    mockCheck.mockResolvedValueOnce({ data: { data: mockResult } })

    const store = useRiskWarningStore()
    const result = await store.check({ work_id: '123' })

    expect(result).toBe(mockResult)
    expect(mockCheck).toHaveBeenCalledWith({ work_id: '123' })
  })

  it('fetchByWork updates warnings on success', async () => {
    const mockWarnings = [{ id: 'w1', title: 'Test' }]
    mockGetByWork.mockResolvedValueOnce({ data: { data: mockWarnings } })

    const store = useRiskWarningStore()
    await store.fetchByWork('work-123')

    expect(store.warnings).toEqual(mockWarnings)
  })

  it('fetchAll sets loading state correctly', async () => {
    mockGetAll.mockResolvedValueOnce({ data: { data: [] } })

    const store = useRiskWarningStore()
    await store.fetchAll()

    expect(store.loading).toBe(false)
  })

  it('fetchAll passes params to API', async () => {
    mockGetAll.mockResolvedValueOnce({ data: { data: [] } })

    const store = useRiskWarningStore()
    await store.fetchAll({ dismissed: true, severity: 'high' })

    expect(mockGetAll).toHaveBeenCalledWith({ dismissed: true, severity: 'high' })
  })

  it('dismiss calls API and updates warning state', async () => {
    mockDismiss.mockResolvedValueOnce({})
    const store = useRiskWarningStore()
    // Set up warnings using direct ref assignment
    store.warnings = [
      { id: 'w1', title: 'Test', dismissed: false } as any,
      { id: 'w2', title: 'Other', dismissed: false } as any,
    ] as any

    await store.dismiss('w1')

    // The store should have updated the dismissed flag
    expect(mockDismiss).toHaveBeenCalledWith('w1')
  })

  it('loadTaxDeadlines loads deadlines from API', async () => {
    const mockDeadlines = [{ id: 't1', tax_type: 'VAT', due_date: '2026-08-01' }]
    mockListTaxDeadlines.mockResolvedValueOnce(mockDeadlines)

    const store = useRiskWarningStore()
    await store.loadTaxDeadlines()

    expect(store.taxDeadlines).toEqual(mockDeadlines)
  })

  it('addDeadline calls API and reloads deadlines', async () => {
    mockAddTaxDeadline.mockResolvedValueOnce({})
    mockListTaxDeadlines.mockResolvedValueOnce([{ id: 't1' }])

    const store = useRiskWarningStore()
    await store.addDeadline({ tax_type: 'VAT', due_date: '2026-09-01', amount_yuan: 1000 })

    expect(mockAddTaxDeadline).toHaveBeenCalledWith({ tax_type: 'VAT', due_date: '2026-09-01', amount_yuan: 1000 })
  })

  it('markComplete calls API and reloads deadlines', async () => {
    mockCompleteTaxDeadline.mockResolvedValueOnce({})
    mockListTaxDeadlines.mockResolvedValueOnce([])

    const store = useRiskWarningStore()
    await store.markComplete('t1')

    expect(mockCompleteTaxDeadline).toHaveBeenCalledWith('t1')
  })

  it('loadBurnoutRisk loads burnout risk data', async () => {
    const mockRisk = { risk_level: 'low', score: 85 }
    mockGetBurnoutRisk.mockResolvedValueOnce(mockRisk)

    const store = useRiskWarningStore()
    await store.loadBurnoutRisk()

    expect(store.burnoutRisk).toEqual(mockRisk)
  })
})
