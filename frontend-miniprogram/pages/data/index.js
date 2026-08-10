// pages/data/index.js
const { getPlatformStats, getCreatorRanking, getCategoryTrends, getIndustryReport } = require('../../api/data')

Page({
  data: {
    activeTab: 'overview',
    stats: {},
    loading: false,
    ranking: [],
    loadingRanking: false,
    rankSort: 'works',
    trends: [],
    loadingTrends: false,
    period: 'monthly',
    report: {},
    loadingReport: false,
    reportError: '',
    reportMonth: '',
  },

  onLoad() {
    const now = new Date()
    this.setData({
      reportMonth: `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`,
    })
    this.loadOverview()
  },

  onShow() {
    if (this.data.activeTab === 'overview') this.loadOverview()
    else if (this.data.activeTab === 'ranking') this.loadRanking()
    else if (this.data.activeTab === 'trends') this.loadTrends()
    else if (this.data.activeTab === 'report') this.loadReport()
  },

  switchTab(e) {
    const tab = e.currentTarget.dataset.tab
    this.setData({ activeTab: tab })
    if (tab === 'overview') this.loadOverview()
    else if (tab === 'ranking') this.loadRanking()
    else if (tab === 'trends') this.loadTrends()
    else if (tab === 'report') this.loadReport()
  },

  async loadOverview() {
    this.setData({ loading: true })
    try {
      const res = await getPlatformStats()
      this.setData({ stats: res })
    } catch (e) {
      console.error('loadOverview failed:', e)
    } finally {
      this.setData({ loading: false })
    }
  },

  async loadRanking() {
    this.setData({ loadingRanking: true })
    try {
      const res = await getCreatorRanking({ sort_by: this.data.rankSort })
      this.setData({ ranking: Array.isArray(res) ? res : [] })
    } catch (e) {
      console.error('loadRanking failed:', e)
    } finally {
      this.setData({ loadingRanking: false })
    }
  },

  setRankSort(e) {
    this.setData({ rankSort: e.currentTarget.dataset.sort })
    this.loadRanking()
  },

  getRankStat(item) {
    if (this.data.rankSort === 'works') return `${item.work_count} 作品`
    if (this.data.rankSort === 'transactions') return `¥${(item.total_transactions || 0).toFixed(0)}`
    if (this.data.rankSort === 'scr') return `${item.scr_score?.toFixed(1) || '-'} ${item.rating_level || ''}`
    return '-'
  },

  async loadTrends() {
    this.setData({ loadingTrends: true })
    try {
      const res = await getCategoryTrends({ period: this.data.period })
      this.setData({ trends: Array.isArray(res) ? res : [] })
    } catch (e) {
      console.error('loadTrends failed:', e)
    } finally {
      this.setData({ loadingTrends: false })
    }
  },

  setPeriod(e) {
    this.setData({ period: e.currentTarget.dataset.period })
    this.loadTrends()
  },

  getBarWidth(count) {
    const max = Math.max(...this.data.trends.map(t => t.work_count), 1)
    return (count / max) * 100
  },

  async loadReport() {
    this.setData({ loadingReport: true, reportError: '' })
    try {
      const res = await getIndustryReport({ month: this.data.reportMonth })
      this.setData({ report: res })
    } catch (e) {
      this.setData({ reportError: e.message || '加载失败' })
    } finally {
      this.setData({ loadingReport: false })
    }
  },

  onMonthChange(e) {
    this.setData({ reportMonth: e.detail.value })
  },

  formatAmount(amount) {
    if (!amount) return '¥0.00'
    if (amount >= 10000) return `¥${(amount / 10000).toFixed(2)}万`
    return `¥${amount.toFixed(2)}`
  },
})
