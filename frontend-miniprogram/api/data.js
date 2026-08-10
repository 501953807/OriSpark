/**
 * 数据看板 API
 */
const { request } = require('./request')

// 平台总览
function getPlatformStats() {
  return request({ url: '/api/operator/data/platform-stats', method: 'GET' })
}

// 创作者排行
function getCreatorRanking(params = {}) {
  return request({ url: '/api/operator/data/creator-ranking', method: 'GET', data: params })
}

// 品类趋势
function getCategoryTrends(params = {}) {
  return request({ url: '/api/operator/data/category-trends', method: 'GET', data: params })
}

// 行业报告
function getIndustryReport(params = {}) {
  return request({ url: '/api/operator/data/industry-report', method: 'GET', data: params })
}

module.exports = {
  getPlatformStats,
  getCreatorRanking,
  getCategoryTrends,
  getIndustryReport,
}
