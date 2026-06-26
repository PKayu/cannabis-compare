import Link from 'next/link'
import CannabisLeaf from '@/components/CannabisLeaf'

export default function Footer() {
  return (
    <footer className="bg-groovy-dark border-t-4 border-groovy-ink">
      {/* Wavy top edge */}
      <div className="w-full overflow-hidden -mt-px">
        <svg viewBox="0 0 1440 48" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full block" preserveAspectRatio="none" style={{ height: 32 }}>
          <path d="M0 48 C240 0 480 48 720 24 C960 0 1200 48 1440 24 L1440 0 L0 0 Z" fill="#FFF8EE"/>
        </svg>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
          {/* Brand */}
          <div className="flex items-center gap-3">
            <CannabisLeaf size={32} color="#FCD34D" rotate={-10} />
            <div>
              <p className="font-display font-bold text-lg text-groovy-sun">Utah Cannabis Compare</p>
              <p className="text-teal-200 text-xs mt-0.5">Informational only — not a dispensary</p>
            </div>
            <CannabisLeaf size={24} color="#FCD34D" rotate={20} variant="sprig" />
          </div>

          {/* Links */}
          <nav className="flex gap-6">
            <Link
              href="/terms"
              className="font-display text-sm text-teal-200 hover:text-groovy-sun transition-colors border-b border-transparent hover:border-groovy-sun"
            >
              Terms
            </Link>
            <Link
              href="/privacy"
              className="font-display text-sm text-teal-200 hover:text-groovy-sun transition-colors border-b border-transparent hover:border-groovy-sun"
            >
              Privacy
            </Link>
          </nav>
        </div>

        <p className="text-center text-teal-300 text-xs mt-6 font-body">
          &copy; {new Date().getFullYear()} Utah Cannabis Compare &mdash; For informational purposes only. Not affiliated with any dispensary.
        </p>
      </div>
    </footer>
  )
}
