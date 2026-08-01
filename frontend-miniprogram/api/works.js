/**
 * 作品 API
 */
const { request } = require('./request')

function getPublicWorks(params = {}) {
  return request({ url: '/api/public/works', method: 'GET', data: params })
}

function getPublicWorkDetail(id) {
  return request({ url: `/api/public/works/${id}`, method: 'GET' })
}

function getMyWorks(params = {}) {
  return request({ url: '/api/v1/works/my', method: 'GET', data: params })
}

function getMyWorkDetail(id) {
  return request({ url: `/api/v1/works/${id}`, method: 'GET' })
}

module.exports = { getPublicWorks, getPublicWorkDetail, getFeaturedWorks }
