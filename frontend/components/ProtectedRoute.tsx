'use client'

import { useEffect, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { authEvents } from '@/lib/api'
import { useAuth } from '@/lib/AuthContext'

interface ProtectedRouteProps {
  children: React.ReactNode
}

/**
 * Protected Route wrapper component
 *
 * Ensures only authenticated users can access wrapped content.
 * Redirects to /auth/login if user is not authenticated.
 *
 * Uses the shared AuthContext as the single source of truth for auth state.
 */
export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { user, loading } = useAuth()
  const [isRedirecting, setIsRedirecting] = useState(false)
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    if (!loading && !user && !isRedirecting) {
      console.log('[ProtectedRoute] No user, redirecting to login')
      setIsRedirecting(true)
      const returnUrl = encodeURIComponent(pathname)
      router.push(`/auth/login?returnUrl=${returnUrl}`)
    }
  }, [user, loading, pathname, router, isRedirecting])

  // Listen for API auth failures (401 responses)
  useEffect(() => {
    const cleanupAuthEvents = authEvents.onAuthFailure(() => {
      if (!isRedirecting) {
        console.log('[ProtectedRoute] API auth failure, redirecting to login')
        setIsRedirecting(true)
        const returnUrl = encodeURIComponent(pathname)
        router.push(`/auth/login?returnUrl=${returnUrl}`)
      }
    })

    return () => {
      cleanupAuthEvents()
    }
  }, [pathname, router, isRedirecting])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cannabis-600 mx-auto mb-4"></div>
          <p className="text-gray-600 font-medium">Loading...</p>
        </div>
      </div>
    )
  }

  return user ? <>{children}</> : null
}
