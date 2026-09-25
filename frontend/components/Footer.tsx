import Link from 'next/link'
import { BRAND_NAME } from '@/lib/brand'

export default function Footer() {
  return <footer className="bloom-shell bloom-dark border-t border-white/20 bg-bloom-navy py-10 font-bloom text-bloom-cream">
    <div className="bloom-container flex flex-col gap-8 sm:flex-row sm:items-center sm:justify-between">
      <div><Link href="/" className="font-bloom-display text-3xl">{BRAND_NAME}</Link><p className="mt-2 max-w-sm text-sm">Utah products. Clear comparisons. Your next step.</p></div>
      <nav aria-label="Footer" className="flex flex-wrap gap-x-6 gap-y-2 text-sm font-bold">
        <Link className="inline-flex min-h-[44px] items-center hover:underline" href="/products/search">Discover</Link>
        <Link className="inline-flex min-h-[44px] items-center hover:underline" href="/dispensaries">Dispensaries</Link>
        <Link className="inline-flex min-h-[44px] items-center hover:underline" href="/terms">Terms</Link>
        <Link className="inline-flex min-h-[44px] items-center hover:underline" href="/privacy">Privacy</Link>
      </nav>
    </div>
    <p className="bloom-container mt-8 text-xs leading-relaxed">© {new Date().getFullYear()} {BRAND_NAME}. Informational only. Not affiliated with any dispensary.</p>
  </footer>
}
