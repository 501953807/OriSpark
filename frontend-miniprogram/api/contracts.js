/**
 * 合约 API
 */
const { request } = require('./request')

function getMyContracts(params = {}) {
  return request({ url: '/api/v1/contracts/my', method: 'GET', data: params })
}

function getContractDetail(id) {
  return request({ url: `/api/v1/contracts/${id}`, method: 'GET' })
}

function getPublicContracts(params = {}) {
  return request({ url: '/api/public/contracts', method: 'GET', data: params })
}

module.exports = { getMyContracts, getContractDetail, getPublicContracts }
