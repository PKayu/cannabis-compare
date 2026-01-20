import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add request interceptor for auth tokens (future use)
apiClient.interceptors.request.use((config) => {
  // TODO: Add JWT token to headers if available
  return config
})

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // TODO: Handle authentication errors, redirects, etc.
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
    search: (query: string) => apiClient.get('/api/products/search', { params: { q: query } }),
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
    list: () => apiClient.get('/api/dispensaries'),
    get: (id: string) => apiClient.get(`/api/dispensaries/${id}`),
  },

  // Authentication
  auth: {
    register: (email: string, username: string, password: string) =>
      apiClient.post('/api/auth/register', { email, username, password }),
    login: (email: string, password: string) =>
      apiClient.post('/api/auth/login', { email, password }),
    logout: () => apiClient.post('/api/auth/logout'),
  },
}

export default apiClient
