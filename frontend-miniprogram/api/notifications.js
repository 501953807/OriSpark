/**
 * 通知 API
 */
const { request } = require('./request')

function getPublicNotifications(params = {}) {
  return request({ url: '/api/public/notifications', method: 'GET', data: params })
}

function getMyNotifications(params = {}) {
  return request({ url: '/api/v1/notifications', method: 'GET', data: params })
}

function getUnreadCount() {
  return request({ url: '/api/v1/notifications/unread-count', method: 'GET' })
}

module.exports = { getPublicNotifications }
