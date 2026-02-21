/**
 * Tests for API client and interceptors
 */
import axios from 'axios'
import MockAdapter from 'axios-mock-adapter'

// Mock both the supabase-js library and our local wrapper
// Use inline factory to avoid hoisting issues
jest.mock('@supabase/supabase-js', () => ({
  createClient: jest.fn(() => ({
    auth: {
      getSession: jest.fn(() => Promise.resolve({ data: { session: null }, error: null })),
      signOut: jest.fn(() => Promise.resolve({ error: null })),
    },
  })),
}))

// Mock our local supabase module to use the same mock
// We'll get the mock reference after importing
jest.mock('@/lib/supabase', () => ({
  supabase: {
    auth: {
      getSession: jest.fn(() => Promise.resolve({ data: { session: null }, error: null })),
      signOut: jest.fn(() => Promise.resolve({ error: null })),
    },
  },
}))

// Import after mocking
import { apiClient, api } from '../api'
import { supabase } from '../supabase'

// Get reference to the mocked auth methods
const mockGetSession = supabase.auth.getSession as jest.MockedFunction<typeof supabase.auth.getSession>
const mockSignOut = supabase.auth.signOut as jest.MockedFunction<typeof supabase.auth.signOut>

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
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          session: {
            access_token: mockToken,
          } as any,
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

    it('should sign out on 401 Unauthorized but NOT redirect', async () => {
      mock.onGet('/test').reply(401, { detail: 'Unauthorized' })

      await expect(apiClient.get('/test')).rejects.toThrow()

      // Should have called sign out
      expect(mockSignOut).toHaveBeenCalled()

      // NOTE: The interceptor does NOT redirect - components handle redirects
      // This prevents infinite loops when Navigation checks auth
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
