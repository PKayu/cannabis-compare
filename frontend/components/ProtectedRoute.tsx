'use client'

import { useEffect, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { supabase } from '@/lib/supabase'

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
          router.push(`/auth/login?returnUrl=${returnUrl}`)
        }
      } catch (err) {
        console.error('Auth check failed:', err)
        router.push('/auth/login')
      } finally {
        setIsLoading(false)
      }
    }

    checkAuth()

    // Set up listener for auth state changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, session) => {
      if (session) {
        setIsAuthed(true)
      } else {
        setIsAuthed(false)
        router.push('/auth/login')
      }
    })

    return () => {
      subscription?.unsubscribe()
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
