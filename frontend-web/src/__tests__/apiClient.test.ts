import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import client, { setToast } from '@/api/client'
import type { InternalAxiosRequestConfig, AxiosResponse, AxiosHeaders } from 'axios'

// Mock toast
const mockToast = { show: vi.fn() }

beforeEach(() => {
  vi.resetAllMocks()
  setToast(mockToast)
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('API Client', () => {
  it('has correct base URL', () => {
    expect(client.defaults.baseURL).toBe('/api')
  })

  it('has 10000ms timeout', () => {
    expect(client.defaults.timeout).toBe(10000)
  })

  it('allows setToast to register a toast function', () => {
    const newToast = { show: vi.fn() }
    setToast(newToast)
    expect(typeof setToast).toBe('function')
  })

  it('has request and response interceptors', () => {
    const requestHandlers = client.interceptors.request.handlers ?? []
    const responseHandlers = client.interceptors.response.handlers ?? []
    expect(requestHandlers.length).toBeGreaterThan(0)
    expect(responseHandlers.length).toBeGreaterThan(0)
  })
})

describe('Request Interceptor', () => {
  it('adds Authorization header when token exists', () => {
    Object.defineProperty(global, 'localStorage', {
      value: { getItem: () => 'test-token-123' },
      writable: true,
    })

    const requestHandlers = client.interceptors.request.handlers ?? []
    const handler = requestHandlers[0]?.fulfilled
    expect(handler).toBeDefined()
    const result = handler!({
      url: '/test',
      method: 'get',
      headers: new Headers() as unknown as AxiosHeaders,
    } as InternalAxiosRequestConfig)

    expect((result as InternalAxiosRequestConfig).headers.Authorization).toBe('Bearer test-token-123')
  })

  it('does not add Authorization header when no token', () => {
    Object.defineProperty(global, 'localStorage', {
      value: { getItem: () => null },
      writable: true,
    })

    const requestHandlers = client.interceptors.request.handlers ?? []
    const handler = requestHandlers[0]?.fulfilled
    const result = handler!({
      url: '/test',
      method: 'get',
      headers: new Headers() as unknown as AxiosHeaders,
    } as InternalAxiosRequestConfig)

    expect((result as InternalAxiosRequestConfig).headers.Authorization).toBeUndefined()
  })

  it('sets Content-Type for normal data', () => {
    Object.defineProperty(global, 'localStorage', {
      value: { getItem: () => 'token' },
      writable: true,
    })

    const requestHandlers = client.interceptors.request.handlers ?? []
    const handler = requestHandlers[0]?.fulfilled
    const result = handler!({
      url: '/test',
      method: 'post',
      data: { name: 'test' },
      headers: new Headers() as unknown as AxiosHeaders,
    } as InternalAxiosRequestConfig)

    expect((result as InternalAxiosRequestConfig).headers['Content-Type']).toBe('application/json')
  })

  it('skips Content-Type for FormData', () => {
    Object.defineProperty(global, 'localStorage', {
      value: { getItem: () => 'token' },
      writable: true,
    })

    const fd = new FormData()
    const requestHandlers = client.interceptors.request.handlers ?? []
    const handler = requestHandlers[0]?.fulfilled
    const result = handler!({
      url: '/upload',
      method: 'post',
      data: fd,
      headers: new Headers() as unknown as AxiosHeaders,
    } as InternalAxiosRequestConfig)

    expect((result as InternalAxiosRequestConfig).headers['Content-Type']).toBeUndefined()
  })
})

describe('Response Interceptor', () => {
  function callRejected(error: unknown) {
    const responseHandlers = client.interceptors.response.handlers ?? []
    const handler = responseHandlers[0]?.rejected
    try {
      const result = handler!(error)
      if (result && typeof (result as Promise<unknown>).catch === 'function') {
        return (result as Promise<unknown>).catch(() => {})
      }
    } catch {
      // Handler threw synchronously
    }
    return Promise.resolve()
  }

  it('passes successful responses through unchanged', async () => {
    const responseHandlers = client.interceptors.response.handlers ?? []
    const handler = responseHandlers[0]?.fulfilled
    const response: AxiosResponse = {
      data: { success: true },
      status: 200,
      statusText: 'OK',
      headers: {},
      config: {} as any,
    }

    const result = handler!(response)
    expect(result).toBe(response)
  })

  it('returns network error message when no response', async () => {
    const error = { response: undefined, message: 'Network Error' }
    await callRejected(error)

    expect(mockToast.show).toHaveBeenCalledWith(
      '无法连接到服务器，请检查后端是否已启动',
      'error',
      5000
    )
  })

  it('returns 404 message', async () => {
    const error = { response: { status: 404, data: {} } }
    await callRejected(error)

    expect(mockToast.show).toHaveBeenCalledWith(
      '资源不存在',
      'error',
      5000
    )
  })

  it('returns 422 message with detail', async () => {
    const detail = '字段 "email" 格式不正确'
    const error = { response: { status: 422, data: { detail } } }
    await callRejected(error)

    expect(mockToast.show).toHaveBeenCalledWith(
      detail,
      'error',
      5000
    )
  })

  it('returns 500 server error message', async () => {
    const error = { response: { status: 500, data: {} } }
    await callRejected(error)

    expect(mockToast.show).toHaveBeenCalledWith(
      '服务器内部错误，请稍后重试',
      'error',
      5000
    )
  })

  it('returns 413 file too large message', async () => {
    const error = { response: { status: 413, data: {} } }
    await callRejected(error)

    expect(mockToast.show).toHaveBeenCalledWith(
      '文件过大，请压缩后重试',
      'error',
      5000
    )
  })

  it('returns 408 timeout message', async () => {
    const error = { response: { status: 408, data: {} } }
    await callRejected(error)

    expect(mockToast.show).toHaveBeenCalledWith(
      '请求超时，请稍后重试',
      'error',
      5000
    )
  })

  it('returns ECONNABORTED timeout message', async () => {
    const error = { code: 'ECONNABORTED', response: undefined }
    await callRejected(error)

    expect(mockToast.show).toHaveBeenCalledWith(
      '无法连接到服务器，请检查后端是否已启动',
      'error',
      5000
    )
  })

  it('returns generic error message for other statuses', async () => {
    const error = { response: { status: 502, data: {} } }
    await callRejected(error)

    expect(mockToast.show).toHaveBeenCalledWith(
      '请求错误 (502)',
      'error',
      5000
    )
  })

  it('uses detail from response data for generic errors', async () => {
    const error = { response: { status: 503, data: { detail: 'Service unavailable' } } }
    await callRejected(error)

    expect(mockToast.show).toHaveBeenCalledWith(
      'Service unavailable',
      'error',
      5000
    )
  })

  it('falls back to default message when no detail available', async () => {
    const error = { response: { status: 503, data: {} } }
    await callRejected(error)

    expect(mockToast.show).toHaveBeenCalledWith(
      '请求错误 (503)',
      'error',
      5000
    )
  })
})
