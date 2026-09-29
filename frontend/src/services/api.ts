/**
 * Axios API client with JWT auth, refresh token handling, and error normalization.
 */
import axios, { AxiosError, AxiosInstance } from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Token storage — sessionStorage for access, localStorage for refresh
const TOKEN_KEY = 'aiip_access_token'
const REFRESH_KEY = 'aiip_refresh_token'

export const tokenStorage = {
  get: (): string | null => sessionStorage.getItem(TOKEN_KEY),
  set: (token: string) => sessionStorage.setItem(TOKEN_KEY, token),
  clear: () => sessionStorage.removeItem(TOKEN_KEY),
}

export const refreshStorage = {
  get: (): string | null => localStorage.getItem(REFRESH_KEY),
  set: (token: string) => localStorage.setItem(REFRESH_KEY, token),
  clear: () => localStorage.removeItem(REFRESH_KEY),
}

export function clearAuthTokens() {
  tokenStorage.clear()
  refreshStorage.clear()
}

export function storeAuthTokens(access: string, refresh: string) {
  tokenStorage.set(access)
  refreshStorage.set(refresh)
}

// Create the main axios instance
const api: AxiosInstance = axios.create({
  baseURL: `${BASE_URL}/api`,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
})

// Request interceptor — attach access token
api.interceptors.request.use(
  (config) => {
    const token = tokenStorage.get()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

let isRefreshing = false
let failedQueue: Array<{ resolve: (t: string) => void; reject: (e: unknown) => void }> = []

function processQueue(error: unknown, token: string | null = null) {
  failedQueue.forEach((prom) => {
    if (error) prom.reject(error)
    else prom.resolve(token!)
  })
  failedQueue = []
}

// Response interceptor — auto-refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any
    if (error.response?.status === 401 && !originalRequest._retry) {
      const refreshToken = refreshStorage.get()
      if (!refreshToken) {
        clearAuthTokens()
        window.location.href = '/login'
        return Promise.reject(error)
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return api(originalRequest)
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const resp = await axios.post(`${BASE_URL}/api/auth/refresh`, {
          refresh_token: refreshToken,
        })
        const { access_token, refresh_token } = resp.data
        storeAuthTokens(access_token, refresh_token)
        api.defaults.headers.common.Authorization = `Bearer ${access_token}`
        processQueue(null, access_token)
        originalRequest.headers.Authorization = `Bearer ${access_token}`
        return api(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        clearAuthTokens()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }
    return Promise.reject(error)
  }
)

export default api

// ─── Typed API methods ─────────────────────────────────────────────────────

export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  refresh: (refresh_token: string) =>
    api.post('/auth/refresh', { refresh_token }),
  logout: () => api.post('/auth/logout'),
  me: () => api.get('/auth/me'),
}

export const projectsApi = {
  list: (params?: Record<string, any>) => api.get('/projects', { params }),
  hero: () => api.get('/projects/hero'),
  get: (id: number) => api.get(`/projects/${id}`),
  create: (data: any) => api.post('/projects', data),
  update: (id: number, data: any) => api.put(`/projects/${id}`, data),
}

export const monitoringApi = {
  summary: () => api.get('/monitoring/summary'),
  alerts: (params?: Record<string, any>) => api.get('/monitoring/alerts', { params }),
  health: (projectId: number) => api.get(`/monitoring/health/${projectId}`),
  computeHealth: (projectId: number) => api.post(`/monitoring/health/${projectId}/compute`),
  anomalies: (projectId: number) => api.get(`/monitoring/anomaly/${projectId}`),
}

export const analyticsApi = {
  runAnomaly: (projectId: number) => api.post(`/analytics/anomaly/${projectId}`),
  attendance: (projectId: number, days?: number) =>
    api.get(`/analytics/attendance/${projectId}`, { params: { days } }),
  dashboard: () => api.get('/analytics/dashboard'),
}

export const inspectionsApi = {
  recommend: (projectId: number) =>
    api.post(`/inspections/recommend?project_id=${projectId}`),
  assign: (data: any) => api.post('/inspections/assign', data),
  list: (params?: Record<string, any>) => api.get('/inspections', { params }),
  get: (id: number) => api.get(`/inspections/${id}`),
  start: (id: number, data: any) => api.post(`/inspections/${id}/start`, data),
  submit: (id: number, data: any) => api.post(`/inspections/${id}/submit`, data),
  decision: (id: number, data: any) => api.post(`/inspections/${id}/decision`, data),
  timeline: (id: number) => api.get(`/inspections/${id}/timeline`),
}

export const routesApi = {
  generate: (data: any) => api.post('/routes/generate', data),
  get: (id: number) => api.get(`/routes/${id}`),
}

export const evidenceApi = {
  upload: (formData: FormData) =>
    api.post('/evidence/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  verify: (id: number) => api.post(`/evidence/verify/${id}`),
  get: (id: number) => api.get(`/evidence/${id}`),
}

export const cctvApi = {
  list: (projectId?: number) =>
    api.get('/cctv', { params: projectId ? { project_id: projectId } : {} }),
  summary: () => api.get('/cctv/summary'),
  get: (id: number) => api.get(`/cctv/${id}`),
}

export const followupApi = {
  create: (data: any) => api.post('/followups', data),
  list: (params?: Record<string, any>) => api.get('/followups', { params }),
  get: (id: number) => api.get(`/followups/${id}`),
  resolve: (id: number, data: any) => api.put(`/followups/${id}/resolve`, data),
}

export const notificationsApi = {
  list: (params?: Record<string, any>) => api.get('/notifications', { params }),
  markRead: (id: number) => api.put(`/notifications/${id}/read`),
  markAllRead: () => api.put('/notifications/read-all'),
}

export const auditApi = {
  list: (params?: Record<string, any>) => api.get('/audit', { params }),
}
