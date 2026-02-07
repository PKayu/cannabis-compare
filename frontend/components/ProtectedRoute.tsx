'use client'

import { useEffect, useState, useRef } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { supabase } from '@/lib/supabase'
import { authEvents } from '@/lib/api'

interface ProtectedRouteProps {
  children: React.ReactNode
}

/**
 * Protected Route wrapper component
 *
 * Ensures only authenticated users can access wrapped content.
 * Redirects to /auth/login if user is not authenticated.
 *
 * Usage:
 * ```tsx
 * <ProtectedRoute>
 *   <YourProtectedComponent />
 * </ProtectedRoute>
 * ```
 */
export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const [isAuthed, setIsAuthed] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()
  const pathname = usePathname()
  const isRedirecting = useRef(false)

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const { data, error } = await supabase.auth.getSession()

        if (error) {
          throw error
        }

        if (data.session) {
          setIsAuthed(true)
        } else {
          // Store the current path so we can redirect back after login
          const returnUrl = encodeURIComponent(pathname)
          isRedirecting.current = true
          router.push(`/auth/login?returnUrl=${returnUrl}`)
        }
      } catch (err) {
        console.error('Auth check failed:', err)
        isRedirecting.current = true
        router.push('/auth/login')
      } finally {
        setIsLoading(false)
      }
    }

    checkAuth()

    // Set up listener for auth state changes from Supabase
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, session) => {
      // Only redirect if we're not already redirecting and auth was truly lost
      if (!isRedirecting.current && event === 'SIGNED_OUT' && !session) {
        isRedirecting.current = true
        const returnUrl = encodeURIComponent(pathname)
        router.push(`/auth/login?returnUrl=${returnUrl}`)
      } else if (event === 'SIGNED_IN' && session) {
        setIsAuthed(true)
        isRedirecting.current = false
      }
    })

    // Set up listener for API auth failures (401 responses)
    const cleanupAuthEvents = authEvents.onAuthFailure(() => {
      if (!isRedirecting.current) {
        isRedirecting.current = true
        const returnUrl = encodeURIComponent(pathname)
        router.push(`/auth/login?returnUrl=${returnUrl}`)
      }
    })

    return () => {
      subscription?.unsubscribe()
      cleanupAuthEvents()
    }
  }, [router, pathname])

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cannabis-600 mx-auto mb-4"></div>
          <p className="text-gray-600 font-medium">Loading...</p>
        </div>
      </div>
    )
  }

  return isAuthed ? <>{children}</> : null
}
