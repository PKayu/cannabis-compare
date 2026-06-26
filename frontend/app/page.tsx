import Link from 'next/link'
import CannabisLeaf from '@/components/CannabisLeaf'

export default function Home() {
  return (
    <main className="min-h-screen bg-groovy-cream">

      {/* ── Compliance Banner ───────────────────────────────── */}
      <div className="compliance-banner">
        <div className="max-w-7xl mx-auto flex items-center gap-2">
          <CannabisLeaf size={18} color="#1C1917" />
          <p>
            ⚠️ Informational purposes only. Does not sell, advertise, or promote controlled substances.
            All data is educational and provided in compliance with Utah law.
          </p>
        </div>
      </div>

      {/* ── Hero ────────────────────────────────────────────── */}
      <section
        className="relative overflow-hidden"
        style={{
          background: 'linear-gradient(135deg, #F59E0B 0%, #F97316 35%, #0D9488 70%, #0F766E 100%)',
          filter: 'saturate(115%) contrast(105%)',
        }}
      >
        {/* Grain / texture overlay */}
        <div
          className="absolute inset-0 opacity-20 pointer-events-none"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='1'/%3E%3C/svg%3E")`,
            backgroundSize: '200px 200px',
          }}
        />

        {/* Decorative leaves */}
        <div className="absolute top-8 left-6 opacity-30 animate-leaf-sway hidden md:block">
          <CannabisLeaf size={80} color="#FFF8EE" rotate={-15} />
        </div>
        <div className="absolute top-16 left-24 opacity-20 hidden md:block">
          <CannabisLeaf size={48} color="#FFF8EE" rotate={20} variant="sprig" />
        </div>
        <div className="absolute bottom-12 right-8 opacity-30 animate-leaf-sway hidden md:block" style={{ animationDelay: '1.5s' }}>
          <CannabisLeaf size={96} color="#FFF8EE" rotate={30} />
        </div>
        <div className="absolute top-12 right-28 opacity-20 hidden md:block">
          <CannabisLeaf size={56} color="#FFF8EE" rotate={-30} variant="stalk" />
        </div>
        <div className="absolute bottom-20 left-1/3 opacity-15 hidden lg:block">
          <CannabisLeaf size={64} color="#FFF8EE" rotate={10} />
        </div>

        {/* Hero content */}
        <div className="relative max-w-4xl mx-auto px-6 pt-20 pb-28 text-center">
          {/* Eyebrow */}
          <div className="inline-flex items-center gap-2 bg-white/20 backdrop-blur-sm border-2 border-white/40 rounded-full px-4 py-1.5 mb-8">
            <CannabisLeaf size={16} color="#FFF8EE" />
            <span className="font-display text-sm font-semibold text-white tracking-wide">Utah Medical Cannabis</span>
            <CannabisLeaf size={16} color="#FFF8EE" rotate={180} />
          </div>

          {/* Main headline */}
          <h1
            className="font-display font-bold text-white leading-none tracking-tight"
            style={{
              fontSize: 'clamp(3.5rem, 10vw, 7rem)',
              WebkitTextStroke: '2px rgba(28,25,23,0.3)',
            }}
          >
            Find the Best
            <br />
            <span style={{ color: '#FCD34D', WebkitTextStroke: '2px rgba(28,25,23,0.4)' }}>
              Cannabis Prices
            </span>
          </h1>

          <p className="mt-6 text-white/90 font-body text-lg max-w-xl mx-auto leading-relaxed">
            Compare real-time pricing across Utah dispensaries.
            Save money. Read community reviews. All in one place.
          </p>

          {/* CTA row */}
          <div className="mt-10 flex flex-wrap gap-4 justify-center">
            <Link
              href="/products/search"
              className="font-display font-bold text-lg px-8 py-4 bg-groovy-sun text-groovy-ink rounded-2xl border-2 border-groovy-ink shadow-[4px_4px_0px_#1C1917] hover:-translate-y-0.5 hover:shadow-[6px_6px_0px_#1C1917] transition-all duration-150"
            >
              Browse Products
            </Link>
            <Link
              href="/dispensaries"
              className="font-display font-bold text-lg px-8 py-4 bg-white/20 backdrop-blur-sm text-white rounded-2xl border-2 border-white hover:bg-white/30 transition-all duration-150"
            >
              View Dispensaries
            </Link>
          </div>
        </div>

        {/* Wavy bottom edge */}
        <div className="absolute bottom-0 left-0 right-0 overflow-hidden leading-none">
          <svg viewBox="0 0 1440 72" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full block" preserveAspectRatio="none" style={{ height: 56 }}>
            <path d="M0 72 C360 20 720 72 1080 32 C1260 12 1380 56 1440 36 L1440 72 Z" fill="#FFF8EE"/>
          </svg>
        </div>
      </section>

      {/* ── Feature Cards ───────────────────────────────────── */}
      <section className="max-w-5xl mx-auto px-6 py-20">
        {/* Section heading */}
        <div className="text-center mb-14 relative">
          <div className="absolute -left-4 top-0 opacity-40 hidden md:block">
            <CannabisLeaf size={40} color="#0D9488" rotate={-25} />
          </div>
          <h2
            className="font-display font-bold text-groovy-ink"
            style={{ fontSize: 'clamp(2rem, 5vw, 3.5rem)' }}
          >
            Everything you need,
            <br />
            <span className="text-groovy-teal">all in one place</span>
          </h2>
          <div className="absolute -right-2 top-0 opacity-40 hidden md:block">
            <CannabisLeaf size={36} color="#0D9488" rotate={25} variant="sprig" />
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {/* Card 1 */}
          <div className="card-sticker p-7 group">
            <div className="w-14 h-14 bg-groovy-sun rounded-2xl border-2 border-groovy-ink flex items-center justify-center mb-5 shadow-sticker group-hover:-translate-y-0.5 transition-transform">
              <CannabisLeaf size={32} color="#1C1917" />
            </div>
            <h3 className="font-display font-bold text-xl text-groovy-ink mb-2">Compare Prices</h3>
            <p className="font-body text-stone-600 text-sm leading-relaxed">
              Real-time pricing from all Utah dispensaries. See stock status and find the best deal before you go.
            </p>
          </div>

          {/* Card 2 */}
          <div className="card-sticker p-7 group" style={{ background: '#FFF0D4' }}>
            <div className="w-14 h-14 bg-groovy-teal rounded-2xl border-2 border-groovy-ink flex items-center justify-center mb-5 shadow-sticker group-hover:-translate-y-0.5 transition-transform">
              <CannabisLeaf size={32} color="#FFF8EE" variant="sprig" />
            </div>
            <h3 className="font-display font-bold text-xl text-groovy-ink mb-2">Read Reviews</h3>
            <p className="font-body text-stone-600 text-sm leading-relaxed">
              Community reviews for strains and brands. Filter by effects, taste, and value to find what works for you.
            </p>
          </div>

          {/* Card 3 */}
          <div className="card-sticker p-7 group" style={{ background: '#F0FDFA' }}>
            <div className="w-14 h-14 bg-groovy-amber rounded-2xl border-2 border-groovy-ink flex items-center justify-center mb-5 shadow-sticker group-hover:-translate-y-0.5 transition-transform">
              <CannabisLeaf size={32} color="#FFF8EE" variant="stalk" />
            </div>
            <h3 className="font-display font-bold text-xl text-groovy-ink mb-2">Price Alerts</h3>
            <p className="font-body text-stone-600 text-sm leading-relaxed">
              Watchlist your favorite products and get notified when prices drop or deals go live.
            </p>
          </div>
        </div>
      </section>

      {/* ── Teal CTA Band ───────────────────────────────────── */}
      <section className="relative overflow-hidden bg-groovy-dark border-y-4 border-groovy-ink">
        {/* Decorative leaves in background */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="absolute -left-8 top-4 opacity-10">
            <CannabisLeaf size={120} color="#FFF8EE" rotate={-20} />
          </div>
          <div className="absolute right-12 top-0 opacity-10">
            <CannabisLeaf size={80} color="#FFF8EE" rotate={30} variant="stalk" />
          </div>
          <div className="absolute right-40 bottom-0 opacity-10">
            <CannabisLeaf size={64} color="#FFF8EE" rotate={-10} />
          </div>
        </div>

        <div className="relative max-w-3xl mx-auto px-6 py-16 text-center">
          <div className="flex justify-center gap-4 mb-6">
            <CannabisLeaf size={32} color="#FCD34D" rotate={-15} />
            <CannabisLeaf size={24} color="#FCD34D" rotate={0} variant="sprig" />
            <CannabisLeaf size={32} color="#FCD34D" rotate={15} />
          </div>

          <h2
            className="font-display font-bold text-groovy-sun leading-tight"
            style={{ fontSize: 'clamp(2rem, 5vw, 3.5rem)' }}
          >
            Ready to find your best deal?
          </h2>
          <p className="mt-4 text-teal-200 font-body text-base max-w-md mx-auto">
            Search across all Utah dispensaries and start saving today.
          </p>
          <div className="mt-8">
            <Link
              href="/products/search"
              className="inline-flex items-center gap-2 font-display font-bold text-lg px-8 py-4 bg-groovy-sun text-groovy-ink rounded-2xl border-2 border-groovy-ink shadow-[4px_4px_0px_#FFF8EE] hover:-translate-y-0.5 hover:shadow-[6px_6px_0px_#FFF8EE] transition-all duration-150"
            >
              <CannabisLeaf size={22} color="#1C1917" />
              Search Products
            </Link>
          </div>
        </div>
      </section>

      {/* ── Dispensaries teaser ─────────────────────────────── */}
      <section className="max-w-5xl mx-auto px-6 py-20">
        <div className="flex flex-col md:flex-row items-center justify-between gap-8">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-4">
              <CannabisLeaf size={28} color="#F97316" rotate={-10} />
              <span className="font-display font-semibold text-groovy-amber text-sm uppercase tracking-widest">All Utah Locations</span>
            </div>
            <h2
              className="font-display font-bold text-groovy-ink leading-tight"
              style={{ fontSize: 'clamp(1.75rem, 4vw, 2.75rem)' }}
            >
              Every dispensary,<br/>one search
            </h2>
            <p className="mt-4 text-stone-600 font-body text-base leading-relaxed max-w-md">
              We track pricing across Utah's licensed medical dispensaries so you always know who has the best price near you.
            </p>
          </div>
          <div className="flex-1 flex justify-center">
            <Link
              href="/dispensaries"
              className="card-sticker px-8 py-6 flex flex-col items-center gap-4 text-center max-w-xs w-full"
              style={{ background: '#FFF0D4' }}
            >
              <div className="flex gap-3">
                <CannabisLeaf size={40} color="#0D9488" rotate={-15} />
                <CannabisLeaf size={40} color="#F97316" rotate={15} />
              </div>
              <p className="font-display font-bold text-xl text-groovy-ink">View All Dispensaries</p>
              <p className="font-body text-sm text-stone-600">Browse inventory, hours, and current deals →</p>
            </Link>
          </div>
        </div>
      </section>

    </main>
  )
}
