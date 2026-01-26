import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * Add request interceptor for auth tokens
 * Retrieves the Supabase session token and attaches it to the Authorization header
 */
apiClient.interceptors.request.use(async (config) => {
  try {
    // Dynamically import Supabase to avoid SSR issues
    const { createClient } = await import('@supabase/supabase-js')

    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
    const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

    if (supabaseUrl && supabaseAnonKey) {
      const supabase = createClient(supabaseUrl, supabaseAnonKey)
      const { data } = await supabase.auth.getSession()

      if (data?.session?.access_token) {
        config.headers.Authorization = `Bearer ${data.session.access_token}`
      }
    }
  } catch (error) {
    console.error('Failed to add auth token to request:', error)
  }

  return config
})

/**
 * Add response interceptor for error handling
 * Handles 401 Unauthorized responses by clearing auth state and redirecting to login
 */
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Handle 401 Unauthorized - redirect to login
    if (error.response?.status === 401) {
      try {
        // Clear auth state
        const { createClient } = await import('@supabase/supabase-js')
        const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
        const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

        if (supabaseUrl && supabaseAnonKey) {
          const supabase = createClient(supabaseUrl, supabaseAnonKey)
          await supabase.auth.signOut()
        }
      } catch (signOutError) {
        console.error('Failed to sign out:', signOutError)
      }

      // Redirect to login page
      if (typeof window !== 'undefined') {
        const returnUrl = encodeURIComponent(window.location.pathname)
        window.location.href = `/auth/login?returnUrl=${returnUrl}`
      }
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
    list: (productId: string) => apiClient.get(`/api/products/${productId}/reviews`),
    create: (data: any) => apiClient.post('/api/reviews', data),
    update: (id: string, data: any) => apiClient.put(`/api/reviews/${id}`, data),
    delete: (id: string) => apiClient.delete(`/api/reviews/${id}`),
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

  // Generic methods for direct API calls
  get: (url: string, config?: any) => apiClient.get(url, config),
  post: (url: string, data?: any, config?: any) => apiClient.post(url, data, config),
  put: (url: string, data?: any, config?: any) => apiClient.put(url, data, config),
  delete: (url: string, config?: any) => apiClient.delete(url, config),
}

export default apiClient
