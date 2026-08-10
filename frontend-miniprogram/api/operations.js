/**
 * 运营合作 API
 */
const { request } = require('./request')

// 运营者：发起合作要约
function proposeCooperation(data) {
  return request({ url: '/api/operator/operations/propose', method: 'POST', data })
}

// 运营者：查看我的合作列表
function getOperatorOperations(params = {}) {
  return request({ url: '/api/operator/operations', method: 'GET', data: params })
}

// 创作者：查看待处理合作请求
function getCreatorPendingOperations() {
  return request({ url: '/api/operator/operations/creator/pending', method: 'GET' })
}

// 创作者：接受合作
function acceptCooperation(id) {
  return request({ url: `/api/operator/operations/creator/accept/${id}`, method: 'POST' })
}

// 创作者：拒绝合作
function rejectCooperation(id) {
  return request({ url: `/api/operator/operations/creator/reject/${id}`, method: 'POST' })
}

module.exports = {
  proposeCooperation,
  getOperatorOperations,
  getCreatorPendingOperations,
  acceptCooperation,
  rejectCooperation,
}
