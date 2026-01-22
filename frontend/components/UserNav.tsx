'use client'

import React, { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs'

interface UserNavProps {
  className?: string
}

/**
 * User Navigation Menu Component
 *
 * Displays different navigation options based on authentication state:
 * - If authenticated: Shows username and dropdown with profile/settings/logout
 * - If not authenticated: Shows "Sign In" button
 */
export default function UserNav({ className = '' }: UserNavProps) {
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [isOpen, setIsOpen] = useState(false)
  const supabase = createClientComponentClient()
  const router = useRouter()

  useEffect(() => {
    checkAuth()

    // Listen for auth state changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, session) => {
      if (session?.user) {
        setUser(session.user)
      } else {
        setUser(null)
      }
      setLoading(false)
    })

    return () => {
      subscription?.unsubscribe()
    }
  }, [supabase])

  const checkAuth = async () => {
    try {
      const {
        data: { session },
      } = await supabase.auth.getSession()

      if (session?.user) {
        setUser(session.user)
      }
    } catch (error) {
      console.error('Auth check failed:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = async () => {
    try {
      await supabase.auth.signOut()
      setUser(null)
      setIsOpen(false)
      router.push('/')
    } catch (error) {
      console.error('Logout failed:', error)
    }
  }

  if (loading) {
    return (
      <div className={`text-gray-500 ${className}`}>
        <div className="h-10 w-20 bg-gray-200 rounded animate-pulse"></div>
      </div>
    )
  }

  if (!user) {
    // Not authenticated
    return (
      <div className={className}>
        <Link
          href="/auth/login"
          className="px-4 py-2 bg-cannabis-600 text-white font-medium rounded-lg hover:bg-cannabis-700 transition-colors"
        >
          Sign In
        </Link>
      </div>
    )
  }

  // Authenticated
  const userEmail = user.email || 'User'

  return (
    <div className={`relative ${className}`}>
      {/* User Menu Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
      >
        {/* Avatar Circle */}
        <div className="w-8 h-8 bg-cannabis-600 rounded-full flex items-center justify-center">
          <span className="text-white text-sm font-semibold">
            {userEmail.charAt(0).toUpperCase()}
          </span>
        </div>

        {/* Email/Username */}
        <span className="text-gray-700 font-medium hidden sm:inline max-w-[120px] truncate">
          {userEmail}
        </span>

        {/* Dropdown Arrow */}
        <svg
          className={`w-4 h-4 text-gray-600 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
        </svg>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
          {/* User Info */}
          <div className="px-4 py-3 border-b border-gray-200">
            <p className="text-sm text-gray-500">Signed in as</p>
            <p className="font-semibold text-gray-900 truncate">{userEmail}</p>
          </div>

          {/* Menu Items */}
          <nav className="py-2">
            <Link
              href="/profile"
              className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
              onClick={() => setIsOpen(false)}
            >
              <span className="flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                  />
                </svg>
                My Profile
              </span>
            </Link>

            <Link
              href="/profile"
              className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
              onClick={() => setIsOpen(false)}
            >
              <span className="flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                My Reviews
              </span>
            </Link>

            <Link
              href="#"
              className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors opacity-50 cursor-not-allowed"
              onClick={(e) => e.preventDefault()}
            >
              <span className="flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4.848 4.848a.75.75 0 1 0 1.057 1.057m5.838 5.838a.75.75 0 1 0 1.057 1.057m5.838 5.838a.75.75 0 1 0 1.057 1.057M9.11 4.848A8.25 8.25 0 1 0 20.25 15"
                  />
                </svg>
                Watchlist
              </span>
            </Link>

            <div className="border-t border-gray-200 my-2"></div>

            {/* Sign Out */}
            <button
              onClick={handleLogout}
              className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                />
              </svg>
              Sign Out
            </button>
          </nav>
        </div>
      )}

      {/* Close dropdown when clicking outside */}
      {isOpen && (
        <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
      )}
    </div>
  )
}
