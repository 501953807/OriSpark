/**
 * 用户 API
 */
const { request } = require('./request')

function getProfile() {
  return request({ url: '/api/auth/me', method: 'GET' })
}

function updateProfile(data) {
  return request({ url: '/api/auth/me', method: 'PATCH', data })
}

module.exports = { getProfile, updateProfile }
