'use client'

import Link from 'next/link'
import { useEffect, useRef, useState } from 'react'
import { BRAND_NAME } from '@/lib/brand'

export default function PublicNavigation({ pathname, signedIn, loading, savedCount }: {
  pathname: string; signedIn: boolean; loading: boolean; savedCount: number
}) {
  const [open, setOpen] = useState(false)
  const toggle = useRef<HTMLButtonElement>(null)
  useEffect(() => setOpen(false), [pathname])
  const links = [
    { href: '/products/search', label: 'Discover', active: pathname.startsWith('/products') },
    { href: '/dispensaries', label: 'Dispensaries', active: pathname.startsWith('/dispensaries') },
    { href: '/watchlist', label: savedCount ? `Saved (${savedCount})` : 'Saved', active: pathname === '/watchlist' },
  ]
  return (
    <header className="bloom-shell bloom-dark bg-bloom-navy font-bloom text-bloom-cream">
      <div className="bloom-container flex min-h-20 items-center justify-between gap-4 py-3">
        <Link href="/" className="min-w-0" aria-label={`${BRAND_NAME} home`}>
          <span className="block font-bloom-display text-2xl sm:text-3xl">{BRAND_NAME}</span>
          <span className="block text-[10px] font-bold uppercase tracking-[0.2em] text-bloom-mustard">A little clarity. A little sunshine.</span>
        </Link>
        <nav aria-label="Primary" className="hidden items-center gap-6 lg:flex">
          {links.map(link => <Link key={link.href} href={link.href} aria-current={link.active ? 'page' : undefined} className={`inline-flex min-h-[44px] items-center border-b-2 text-sm font-bold ${link.active ? 'border-bloom-mustard text-bloom-mustard' : 'border-transparent hover:border-bloom-cream'}`}>{link.label}</Link>)}
          {loading ? <span role="status" className="text-sm">Loading account…</span> : <Link className="bloom-button" href={signedIn ? '/profile' : '/auth/login'}>{signedIn ? 'My account' : 'Sign in'}</Link>}
        </nav>
        <button ref={toggle} type="button" className="min-h-[44px] rounded-xl border border-bloom-cream px-4 text-sm font-bold lg:hidden" aria-expanded={open} aria-controls="bloom-mobile-nav" onClick={() => setOpen(!open)}>{open ? 'Close' : 'Menu'}</button>
      </div>
      {open && <nav id="bloom-mobile-nav" aria-label="Mobile primary" className="bloom-container flex flex-col border-t border-white/20 pb-4 lg:hidden" onKeyDown={event => { if (event.key === 'Escape') { setOpen(false); toggle.current?.focus() } }}>
        {links.map(link => <Link key={link.href} href={link.href} onClick={() => setOpen(false)} aria-current={link.active ? 'page' : undefined} className="flex min-h-[44px] items-center py-2 font-bold">{link.label}</Link>)}
        {!loading && <Link className="bloom-button self-start" href={signedIn ? '/profile' : '/auth/login'} onClick={() => setOpen(false)}>{signedIn ? 'My account' : 'Sign in'}</Link>}
      </nav>}
    </header>
  )
}
