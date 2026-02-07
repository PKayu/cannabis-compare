'use client'

import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuth } from '@/lib/AuthContext'

export default function CallbackPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { user, loading } = useAuth()
  const [error, setError] = useState<string | null>(null)
  const [hasTimedOut, setHasTimedOut] = useState(false)

  // Timeout: if auth doesn't resolve in 10 seconds, show error
  useEffect(() => {
    const timeout = setTimeout(() => {
      setHasTimedOut(true)
    }, 10000)

    return () => clearTimeout(timeout)
  }, [])

  // Main logic: when auth resolves with a user, redirect
  useEffect(() => {
    // Still loading auth state -- wait
    if (loading) return

    if (user) {
      // Auth succeeded. Redirect to the return URL.
      const returnUrl = searchParams.get('returnUrl') || '/'
      console.log('[Callback] Auth confirmed, redirecting to:', returnUrl)
      router.replace(returnUrl)
    } else if (hasTimedOut) {
      // Auth finished loading but no user, and we've waited long enough
      setError('Authentication failed. Please try signing in again.')
    }
  }, [user, loading, hasTimedOut, router, searchParams])

  // Grace period: if auth finishes loading with no user before the timeout,
  // wait 2 more seconds for the SIGNED_IN event to propagate (hash processing).
  useEffect(() => {
    if (!loading && !user && !hasTimedOut && !error) {
      const grace = setTimeout(() => {
        setError('Authentication failed. Please try signing in again.')
      }, 2000)

      return () => clearTimeout(grace)
    }
  }, [loading, user, hasTimedOut, error])

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-cannabis-50 to-gray-50 flex items-center justify-center px-4">
        <div className="w-full max-w-md bg-white rounded-lg shadow-lg p-8">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Authentication Error</h1>
          <p className="text-gray-600 mb-6">{error}</p>

          <div className="space-y-3">
            <button
              onClick={() => router.push('/auth/login')}
              className="w-full px-4 py-2 bg-cannabis-600 text-white font-medium rounded-lg hover:bg-cannabis-700 transition-colors"
            >
              Try Again
            </button>
            <button
              onClick={() => router.push('/')}
              className="w-full px-4 py-2 border-2 border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-colors"
            >
              Back to Home
            </button>
          </div>

          <p className="text-xs text-gray-500 text-center mt-6">
            If you continue to have issues, please clear your browser cookies and try again.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-cannabis-50 to-gray-50 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cannabis-600 mx-auto mb-4"></div>
        <p className="text-gray-600 font-medium">Verifying your credentials...</p>
        <p className="text-sm text-gray-500 mt-2">Please wait</p>
      </div>
    </div>
  )
}
