/**
 * 合约 API
 */
const { request } = require('./request')

function getMyContracts(params = {}) {
  return request({ url: '/contracts/my', method: 'GET', data: params })
}

function getContractDetail(id) {
  return request({ url: `/contracts/${id}`, method: 'GET' })
}

function getPublicContracts(params = {}) {
  return request({ url: '/public/contracts', method: 'GET', data: params })
}

module.exports = { getMyContracts, getContractDetail, getPublicContracts }
