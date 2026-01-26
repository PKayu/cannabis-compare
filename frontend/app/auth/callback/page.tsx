'use client'

import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { supabase } from '@/lib/supabase'

export default function CallbackPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true
    let attempts = 0
    const maxAttempts = 5

    const checkSession = async () => {
      try {
        // Get the code from URL hash (Supabase auth redirect)
        const hash = window.location.hash
        if (!hash && attempts === 0) {
          // No auth data in URL on first attempt
          if (mounted) {
            setError('No authentication data received. Please try signing in again.')
            setLoading(false)
          }
          return
        }

        // Supabase automatically exchanges the code for a session
        // Check if we have an active session
        const {
          data: { session },
          error: sessionError,
        } = await supabase.auth.getSession()

        if (sessionError && mounted) {
          throw sessionError
        }

        if (session && mounted) {
          // Session established successfully
          // Get returnUrl from query params or default to homepage
          const returnUrl = searchParams.get('returnUrl') || '/'
          router.push(returnUrl)
        } else if (attempts < maxAttempts && mounted) {
          // No session yet, retry with exponential backoff
          attempts++
          setTimeout(() => checkSession(), 300 * attempts)
        } else if (mounted) {
          // All retries exhausted
          setError('Authentication failed. Please try signing in again.')
          setLoading(false)
        }
      } catch (err: any) {
        if (mounted) {
          setError(err.message || 'An error occurred during authentication')
          setLoading(false)
        }
      }
    }

    checkSession()

    return () => {
      mounted = false
    }
  }, [router, searchParams])

  if (loading) {
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

  return null
}
