import axios from 'axios'
import { supabase } from './supabase'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Auth event bus for consistent auth failure handling across the app
export const authEvents = {
  // Trigger an auth failure event (called by API interceptor on 401)
  emitAuthFailure: () => {
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('auth:failed'))
    }
  },
  // Listen for auth failure events
  onAuthFailure: (callback: () => void) => {
    if (typeof window !== 'undefined') {
      window.addEventListener('auth:failed', callback)
      // Return cleanup function
      return () => window.removeEventListener('auth:failed', callback)
    }
    return () => {}
  }
}

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * Add request interceptor for auth tokens
 * Retrieves the Supabase session token and attaches it to the Authorization header
 * IMPORTANT: Uses the shared supabase client to access the same session
 */
apiClient.interceptors.request.use(async (config) => {
  try {
    // Use the shared Supabase client to get the session
    // This ensures we access the same session that was established during login
    const { data } = await supabase.auth.getSession()

    if (data?.session?.access_token) {
      config.headers.Authorization = `Bearer ${data.session.access_token}`
    }
  } catch (error) {
    console.error('Failed to add auth token to request:', error)
  }

  return config
})

/**
 * Add response interceptor for error handling
 * Handles 401 Unauthorized responses by emitting an auth failure event.
 * IMPORTANT: Does NOT call signOut() -- a 401 may be a timing issue during
 * session establishment, and signOut() would destroy a valid session.
 * ProtectedRoute and individual components handle the redirect.
 */
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      console.warn('[API] 401 Unauthorized response received')
      authEvents.emitAuthFailure()
    }

    return Promise.reject(error)
  }
)

// API endpoints
export const api = {
  // Health check
  health: () => apiClient.get('/health'),

  // Products
  products: {
    list: (params?: any) => apiClient.get('/api/products', { params }),
    get: (id: string) => apiClient.get(`/api/products/${id}`),
    search: (params: any) => apiClient.get('/api/products/search', { params }),
    autocomplete: (q: string) => apiClient.get('/api/products/autocomplete', { params: { q } }),
    getPrices: (productId: string) => apiClient.get(`/api/products/${productId}/prices`),
    getRelated: (productId: string, limit?: number) =>
      apiClient.get(`/api/products/${productId}/related`, { params: { limit } }),
    getPricingHistory: (productId: string, days: number = 30) =>
      apiClient.get(`/api/products/${productId}/pricing-history`, { params: { days } }),
  },

  // Prices
  prices: {
    compare: (productId: string) => apiClient.get(`/api/prices/compare?product_id=${productId}`),
    list: (productId: string) => apiClient.get(`/api/prices/${productId}`),
  },

  // Reviews
  reviews: {
    list: (productId: string, params?: any) => apiClient.get(`/api/reviews/product/${productId}`, { params }),
    create: (data: any) => apiClient.post('/api/reviews', data),
    update: (id: string, data: any) => apiClient.put(`/api/reviews/${id}`, data),
    delete: (id: string) => apiClient.delete(`/api/reviews/${id}`),
    upvote: (id: string) => apiClient.post(`/api/reviews/${id}/upvote`),
  },

  // Dispensaries
  dispensaries: {
    list: (params?: any) => apiClient.get('/api/dispensaries', { params }),
    get: (id: string) => apiClient.get(`/api/dispensaries/${id}`),
    getInventory: (dispensaryId: string, params?: any) =>
      apiClient.get(`/api/dispensaries/${dispensaryId}/inventory`, { params }),
  },

  // Authentication
  auth: {
    register: (email: string, username: string, password: string) =>
      apiClient.post('/api/auth/register', { email, username, password }),
    login: (email: string, password: string) =>
      apiClient.post('/api/auth/login', { email, password }),
    logout: () => apiClient.post('/api/auth/logout'),
  },

  // Users
  users: {
    me: () => apiClient.get('/api/users/me'),
    myReviews: () => apiClient.get('/api/users/me/reviews'),
    update: (data: any) => apiClient.put('/api/users/me', data),
  },

  // Watchlist
  watchlist: {
    add: (data: { product_id: string; alert_on_stock?: boolean; alert_on_price_drop?: boolean; price_drop_threshold?: number }) =>
      apiClient.post('/api/watchlist/add', data),
    remove: (productId: string) => apiClient.delete(`/api/watchlist/remove/${productId}`),
    list: () => apiClient.get('/api/watchlist/'),
    check: (productId: string) => apiClient.get(`/api/watchlist/check/${productId}`),
  },

  // Notifications
  notifications: {
    getPreferences: () => apiClient.get('/api/notifications/preferences'),
    updatePreferences: (data: any) => apiClient.put('/api/notifications/preferences', data),
  },

  // Admin
  admin: {
    dashboard: () => apiClient.get('/api/admin/dashboard'),
    flags: {
      pending: (params?: any) => apiClient.get('/api/admin/flags/pending', { params }),
      stats: () => apiClient.get('/api/admin/flags/stats'),
      approve: (flagId: string, data?: {
        notes?: string; name?: string; brand_name?: string; product_type?: string;
        thc_percentage?: number | null; cbd_percentage?: number | null;
        weight?: string; price?: number | null;
      }) => apiClient.post(`/api/admin/flags/approve/${flagId}`, data || {}),
      reject: (flagId: string, data?: {
        notes?: string; name?: string; brand_name?: string; product_type?: string;
        thc_percentage?: number | null; cbd_percentage?: number | null;
        weight?: string; price?: number | null;
      }) => apiClient.post(`/api/admin/flags/reject/${flagId}`, data || {}),
      dismiss: (flagId: string, notes?: string) =>
        apiClient.post(`/api/admin/flags/dismiss/${flagId}`, { notes }),
      analytics: (days?: number) =>
        apiClient.get('/api/admin/flags/analytics', { params: { days } }),
    },
    scrapers: {
      health: () => apiClient.get('/api/admin/scrapers/health'),
      runs: (params?: any) => apiClient.get('/api/admin/scrapers/runs', { params }),
      trigger: (scraperId: string) => apiClient.post(`/api/admin/scrapers/run/${scraperId}`),
      pause: (scraperId: string) => apiClient.post(`/api/admin/scrapers/scheduler/pause/${scraperId}`),
      resume: (scraperId: string) => apiClient.post(`/api/admin/scrapers/scheduler/resume/${scraperId}`),
      schedulerStatus: () => apiClient.get('/api/admin/scrapers/scheduler/status'),
    },
    quality: {
      metrics: () => apiClient.get('/api/admin/scrapers/quality/metrics'),
      freshness: () => apiClient.get('/api/admin/scrapers/dispensaries/freshness'),
      outliers: (limit = 50) => apiClient.get('/api/admin/outliers', { params: { limit } }),
    },
  },

  // Generic methods for direct API calls
  get: (url: string, config?: any) => apiClient.get(url, config),
  post: (url: string, data?: any, config?: any) => apiClient.post(url, data, config),
  put: (url: string, data?: any, config?: any) => apiClient.put(url, data, config),
  delete: (url: string, config?: any) => apiClient.delete(url, config),
}

export default apiClient
