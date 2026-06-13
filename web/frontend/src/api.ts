const API_BASE = import.meta.env.VITE_API_BASE || '/api'

export function token() {
  return localStorage.getItem('token') || ''
}

export function setToken(value: string) {
  localStorage.setItem('token', value)
}

export function logout() {
  localStorage.removeItem('token')
}

export async function api(path: string, options: RequestInit = {}) {
  const headers = new Headers(options.headers || {})
  if (token()) headers.set('Authorization', `Bearer ${token()}`)
  if (!(options.body instanceof FormData) && !(options.body instanceof URLSearchParams) && options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers })
  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(data.detail || `请求失败：${response.status}`)
  }
  return response.json()
}
