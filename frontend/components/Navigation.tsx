'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { useAuth } from '@/lib/AuthContext'
import CannabisLeaf from '@/components/CannabisLeaf'

export default function Navigation() {
  const pathname = usePathname()
  const { user, loading: authLoading } = useAuth()
  const [watchlistCount, setWatchlistCount] = useState(0)
  const [mobileOpen, setMobileOpen] = useState(false)

  const isLoggedIn = !!user

  useEffect(() => {
    if (isLoggedIn) {
      loadWatchlistCount()
    } else {
      setWatchlistCount(0)
    }
  }, [isLoggedIn])

  const loadWatchlistCount = async () => {
    try {
      const response = await api.watchlist.list()
      setWatchlistCount(response.data.length)
    } catch {
      // Ignore errors
    }
  }

  if (pathname === '/') return null

  const linkClass = (active: boolean) =>
    `font-display font-semibold text-base transition-all duration-150 py-1 border-b-2 ${
      active
        ? 'text-groovy-amber border-groovy-amber'
        : 'text-groovy-ink border-transparent hover:text-groovy-teal hover:border-groovy-teal'
    }`

  return (
    <nav className="bg-groovy-cream border-b-4 border-groovy-ink shadow-[0_4px_0_#1C1917]">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 group">
            <CannabisLeaf size={28} color="#0D9488" className="group-hover:rotate-12 transition-transform duration-300" />
            <span className="font-display font-bold text-xl text-groovy-ink tracking-tight">
              Utah Cannabis <span className="text-groovy-teal">Compare</span>
            </span>
          </Link>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-8">
            <Link href="/products/search" className={linkClass(pathname.startsWith('/products'))}>
              Search
            </Link>
            <Link href="/dispensaries" className={linkClass(pathname.startsWith('/dispensaries'))}>
              Dispensaries
            </Link>
            {!authLoading && isLoggedIn && (
              <Link href="/watchlist" className={`${linkClass(pathname === '/watchlist')} flex items-center gap-1`}>
                Watchlist
                {watchlistCount > 0 && (
                  <span className="ml-1 inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-groovy-amber rounded-full border border-groovy-ink">
                    {watchlistCount}
                  </span>
                )}
              </Link>
            )}
            {authLoading ? (
              <div className="w-16 h-8 bg-stone-200 rounded-xl animate-pulse" />
            ) : isLoggedIn ? (
              <Link href="/profile" className={linkClass(pathname.startsWith('/profile'))}>
                Profile
              </Link>
            ) : (
              <Link
                href="/auth/login"
                className="btn-groovy-teal text-sm px-4 py-2"
              >
                Login
              </Link>
            )}
          </div>

          {/* Mobile burger */}
          <button
            className="md:hidden p-2 rounded-xl border-2 border-groovy-ink bg-groovy-cream shadow-sticker"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle menu"
          >
            <svg className="h-5 w-5 text-groovy-ink" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              {mobileOpen
                ? <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                : <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              }
            </svg>
          </button>
        </div>

        {/* Mobile menu */}
        {mobileOpen && (
          <div className="md:hidden border-t-2 border-groovy-ink py-4 flex flex-col gap-3">
            <Link href="/products/search" className={linkClass(pathname.startsWith('/products'))} onClick={() => setMobileOpen(false)}>
              Search
            </Link>
            <Link href="/dispensaries" className={linkClass(pathname.startsWith('/dispensaries'))} onClick={() => setMobileOpen(false)}>
              Dispensaries
            </Link>
            {!authLoading && isLoggedIn && (
              <Link href="/watchlist" className={linkClass(pathname === '/watchlist')} onClick={() => setMobileOpen(false)}>
                Watchlist {watchlistCount > 0 && `(${watchlistCount})`}
              </Link>
            )}
            {!authLoading && (isLoggedIn
              ? <Link href="/profile" className={linkClass(pathname.startsWith('/profile'))} onClick={() => setMobileOpen(false)}>Profile</Link>
              : <Link href="/auth/login" className="btn-groovy-teal self-start" onClick={() => setMobileOpen(false)}>Login</Link>
            )}
          </div>
        )}
      </div>
    </nav>
  )
}
