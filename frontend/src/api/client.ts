import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

let toastFn: any = null
export function setToast(fn: any) { toastFn = fn }

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('oristudio-token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  // Don't set Content-Type for FormData — let browser set multipart boundary
  if (!(config.data instanceof FormData)) {
    config.headers['Content-Type'] = 'application/json'
  }
  return config
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    const detail = error.response?.data?.detail || ''
    let message = '请求失败'

    if (!error.response) {
      message = '无法连接到服务器，请检查后端是否已启动'
    } else if (status === 404) {
      message = '资源不存在'
    } else if (status === 422) {
      message = detail || '请求参数有误'
    } else if (status === 500) {
      message = '服务器内部错误，请稍后重试'
    } else if (status === 413) {
      message = '文件过大，请压缩后重试'
    } else {
      message = detail || `请求错误 (${status})`
    }

    console.error(`[API ${status}]`, error.config?.url, message)
    if (toastFn) toastFn.show(message, 'error', 5000)
    return Promise.reject(error)
  }
)

export default client
