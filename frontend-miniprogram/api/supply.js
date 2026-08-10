/**
 * 供应链 API
 */
const { request } = require('./request')

// 工厂管理
function createFactory(data) {
  return request({ url: '/api/operator/supply/factories', method: 'POST', data })
}

function getFactories(params = {}) {
  return request({ url: '/api/operator/supply/factories', method: 'GET', data: params })
}

function getFactory(id) {
  return request({ url: `/api/operator/supply/factories/${id}`, method: 'GET' })
}

// 生产订单
function createOrder(data) {
  return request({ url: '/api/operator/supply/orders', method: 'POST', data })
}

function getOrders(params = {}) {
  return request({ url: '/api/operator/supply/orders', method: 'GET', data: params })
}

function confirmOrder(id) {
  return request({ url: `/api/operator/supply/orders/${id}/confirm`, method: 'POST' })
}

function startProduction(id) {
  return request({ url: `/api/operator/supply/orders/${id}/start`, method: 'POST' })
}

function shipOrder(id, data) {
  return request({ url: `/api/operator/supply/orders/${id}/ship`, method: 'POST', data })
}

function inspectOrder(id, data) {
  return request({ url: `/api/operator/supply/orders/${id}/inspect`, method: 'POST', data })
}

// POD 配置
function createPODConfig(data) {
  return request({ url: '/api/operator/supply/pod/configs', method: 'POST', data })
}

function getPODConfigs() {
  return request({ url: '/api/operator/supply/pod/configs', method: 'GET' })
}

module.exports = {
  createFactory, getFactories, getFactory,
  createOrder, getOrders, confirmOrder, startProduction, shipOrder, inspectOrder,
  createPODConfig, getPODConfigs,
}
