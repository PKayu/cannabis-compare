/**
 * Tests for API client and interceptors
 */
import axios from 'axios'
import MockAdapter from 'axios-mock-adapter'

// This must be defined before importing api.ts
const mockGetSession = jest.fn()
const mockSignOut = jest.fn()

jest.mock('@supabase/supabase-js', () => ({
  createClient: jest.fn(() => ({
    auth: {
      getSession: mockGetSession,
      signOut: mockSignOut,
    },
  })),
}))

// Import after mocking
import { apiClient, api } from '../api'

describe('API Client', () => {
  let mock: MockAdapter

  beforeEach(() => {
    // Create axios mock adapter
    mock = new MockAdapter(apiClient)

    // Reset mocks
    mockGetSession.mockReset()
    mockSignOut.mockReset()

    // Set default mock responses
    mockGetSession.mockResolvedValue({ data: { session: null }, error: null })
    mockSignOut.mockResolvedValue({ error: null })
  })

  afterEach(() => {
    mock.restore()
  })

  describe('Request Interceptor - Auth Token', () => {
    it('should add Authorization header when session exists', async () => {
      const mockToken = 'mock-access-token-12345'

      mockGetSession.mockResolvedValue({
        data: {
          session: {
            access_token: mockToken,
          },
        },
        error: null,
      })

      mock.onGet('/test').reply(200, { success: true })

      await apiClient.get('/test')

      // Check that request was made with Authorization header
      expect(mock.history.get[0].headers).toHaveProperty('Authorization', `Bearer ${mockToken}`)
    })

    it('should not add Authorization header when no session', async () => {
      mockGetSession.mockResolvedValue({
        data: { session: null },
        error: null,
      })

      mock.onGet('/test').reply(200, { success: true })

      await apiClient.get('/test')

      // Check that Authorization header was not added
      expect(mock.history.get[0].headers).not.toHaveProperty('Authorization')
    })

    it('should handle Supabase errors gracefully', async () => {
      mockGetSession.mockRejectedValue(new Error('Supabase error'))

      mock.onGet('/test').reply(200, { success: true })

      // Should not throw, just continue without token
      await expect(apiClient.get('/test')).resolves.toBeDefined()
    })
  })

  describe('Response Interceptor - Error Handling', () => {
    it('should handle successful responses', async () => {
      mock.onGet('/test').reply(200, { data: 'success' })

      const response = await apiClient.get('/test')

      expect(response.status).toBe(200)
      expect(response.data).toEqual({ data: 'success' })
    })

    it('should sign out and redirect on 401 Unauthorized', async () => {
      // Mock window.location
      delete (window as any).location
      window.location = { href: '', pathname: '/profile' } as any

      mock.onGet('/test').reply(401, { detail: 'Unauthorized' })

      await expect(apiClient.get('/test')).rejects.toThrow()

      // Should have called sign out
      expect(mockSignOut).toHaveBeenCalled()

      // Should have redirected to login with return URL
      expect(window.location.href).toBe('/auth/login?returnUrl=%2Fprofile')
    })

    it('should reject other error codes without redirect', async () => {
      mock.onGet('/test').reply(500, { detail: 'Internal Server Error' })

      await expect(apiClient.get('/test')).rejects.toThrow()

      // Should not sign out for non-401 errors
      expect(mockSignOut).not.toHaveBeenCalled()
    })
  })

  describe('API Methods', () => {
    it('health() should call /health endpoint', async () => {
      mock.onGet('/health').reply(200, { status: 'healthy' })

      const response = await api.health()

      expect(response.data).toEqual({ status: 'healthy' })
      expect(mock.history.get[0].url).toBe('/health')
    })

    it('products.list() should call /api/products', async () => {
      mock.onGet('/api/products').reply(200, { products: [] })

      const response = await api.products.list()

      expect(response.data).toEqual({ products: [] })
      expect(mock.history.get[0].url).toBe('/api/products')
    })

    it('products.get() should call /api/products/:id', async () => {
      const productId = 'test-product-123'
      mock.onGet(`/api/products/${productId}`).reply(200, { id: productId })

      const response = await api.products.get(productId)

      expect(response.data).toEqual({ id: productId })
      expect(mock.history.get[0].url).toBe(`/api/products/${productId}`)
    })
  })
})
