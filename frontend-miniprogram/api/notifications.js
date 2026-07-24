/**
 * 通知 API
 */
const { request } = require('./request')

function getPublicNotifications(params = {}) {
  return request({ url: '/public/notifications', method: 'GET', data: params })
}

module.exports = { getPublicNotifications }
