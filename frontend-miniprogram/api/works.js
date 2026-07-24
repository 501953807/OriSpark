/**
 * 作品 API
 */
const { request } = require('./request')

function getPublicWorks(params = {}) {
  return request({ url: '/public/works', method: 'GET', data: params })
}

function getPublicWorkDetail(id) {
  return request({ url: `/public/works/${id}`, method: 'GET' })
}

function getFeaturedWorks(params = {}) {
  return request({ url: '/public/works?limit=6', method: 'GET', data: params })
}

module.exports = { getPublicWorks, getPublicWorkDetail, getFeaturedWorks }
