/**
 * HTTP 请求封装
 */

function request(options) {
  return new Promise((resolve, reject) => {
    const app = getApp()
    wx.request({
      url: `${app.globalData.apiBase}${options.url}`,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        'Content-Type': 'application/json',
        ...(app.globalData.token ? { Authorization: `Bearer ${app.globalData.token}` } : {}),
        ...options.header,
      },
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
        } else if (res.statusCode === 401) {
          // Token 过期，清除登录态
          app.logout()
          wx.showToast({ title: '请重新登录', icon: 'none' })
          reject(new Error('Unauthorized'))
        } else {
          reject(new Error(res.data?.message || 'Request failed'))
        }
      },
      fail(err) {
        reject(err)
      },
    })
  })
}

module.exports = { request }
