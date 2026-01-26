'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useState, useEffect } from 'react'
import { api } from '@/lib/api'

export default function Navigation() {
  const pathname = usePathname()
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [watchlistCount, setWatchlistCount] = useState(0)

  useEffect(() => {
    // Skip auth check on auth pages to prevent redirect loops
    // Also skip on home page since we don't show nav there anyway
    if (pathname === '/' || pathname.startsWith('/auth')) {
      setIsLoggedIn(false)
      return
    }
    checkAuth()
  }, [pathname])

  const checkAuth = async () => {
    try {
      await api.users.me()
      setIsLoggedIn(true)
      loadWatchlistCount()
    } catch (error) {
      // Silently handle - user not logged in
      setIsLoggedIn(false)
    }
  }

  const loadWatchlistCount = async () => {
    try {
      const response = await api.watchlist.list()
      setWatchlistCount(response.data.length)
    } catch (error) {
      // Ignore errors
    }
  }

  // Don't show on home page
  if (pathname === '/') {
    return null
  }

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
            <span className="text-2xl font-bold text-cannabis-700">
              Utah Cannabis Aggregator
            </span>
          </Link>

          {/* Navigation Links */}
          <div className="hidden md:flex space-x-8">
            <Link
              href="/products/search"
              className={`${
                pathname.startsWith('/products')
                  ? 'text-cannabis-700 border-b-2 border-cannabis-700'
                  : 'text-gray-600 hover:text-cannabis-700'
              } py-2 transition`}
            >
              Search
            </Link>

            <Link
              href="/dispensaries"
              className={`${
                pathname.startsWith('/dispensaries')
                  ? 'text-cannabis-700 border-b-2 border-cannabis-700'
                  : 'text-gray-600 hover:text-cannabis-700'
              } py-2 transition`}
            >
              Dispensaries
            </Link>

            {isLoggedIn && (
              <Link
                href="/watchlist"
                className={`${
                  pathname === '/watchlist'
                    ? 'text-cannabis-700 border-b-2 border-cannabis-700'
                    : 'text-gray-600 hover:text-cannabis-700'
                } py-2 transition flex items-center gap-1`}
              >
                Watchlist
                {watchlistCount > 0 && (
                  <span className="inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white bg-cannabis-600 rounded-full">
                    {watchlistCount}
                  </span>
                )}
              </Link>
            )}

            {isLoggedIn ? (
              <Link
                href="/profile"
                className={`${
                  pathname.startsWith('/profile')
                    ? 'text-cannabis-700 border-b-2 border-cannabis-700'
                    : 'text-gray-600 hover:text-cannabis-700'
                } py-2 transition`}
              >
                Profile
              </Link>
            ) : (
              <Link
                href="/auth/login"
                className="text-gray-600 hover:text-cannabis-700 py-2 transition"
              >
                Login
              </Link>
            )}
          </div>

          {/* Mobile Menu Button */}
          <div className="md:hidden">
            <button className="text-gray-600 hover:text-cannabis-700">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </nav>
  )
}
