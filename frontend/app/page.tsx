'use client'

import Image from 'next/image'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import SearchBar from '@/components/SearchBar'

export default function Home() {
  const router = useRouter()

  return (
    <div className="bloom-page bloom-leaf-field pb-16">
      <section className="relative isolate overflow-hidden border-b border-bloom-cream/25 bg-bloom-navy">
        <div aria-hidden="true" className="absolute inset-0 bg-bloom-blue/20" />
        <div className="bloom-container relative grid gap-8 py-8 sm:py-12 lg:min-h-[34rem] lg:grid-cols-[minmax(0,0.94fr)_minmax(0,1.06fr)] lg:items-center lg:py-14">
          <div className="relative z-10 max-w-2xl">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-bloom-mustard">Utah cannabis prices, made clearer</p>
            <h1 className="bloom-title mt-3 text-5xl text-bloom-cream sm:text-6xl lg:text-7xl">Find your next stop.</h1>
            <p className="mt-4 max-w-xl text-base leading-relaxed text-bloom-cream/90 sm:text-lg">Search a product or brand, compare the same package across available listings, then continue with a licensed dispensary when you are ready.</p>
            <div className="mt-7"><SearchBar onSearch={query => router.push(`/products/search?q=${encodeURIComponent(query)}`)} /></div>
            <p className="mt-4 max-w-xl text-sm leading-relaxed text-bloom-cream/80">Prices and availability can change. Confirm final details with the dispensary.</p>
          </div>
          <div aria-hidden="true" className="pointer-events-none relative min-h-[18rem] overflow-hidden rounded-[2.25rem] border border-bloom-cream/30 shadow-[6px_6px_0_#102A32] sm:min-h-[24rem] lg:min-h-[29rem]">
            <Image src="/images/mountain-bloom/groovy-van-hero.png" alt="" fill priority unoptimized sizes="(max-width: 1023px) calc(100vw - 2.5rem), 54vw" className="object-cover object-[center_54%]" />
            <div className="absolute inset-0 bg-gradient-to-t from-bloom-navy/45 via-transparent to-bloom-cream/10" />
          </div>
        </div>
      </section>

      <section className="bloom-warm-surface py-14 sm:py-20">
        <div className="bloom-container">
          <div className="max-w-2xl"><p className="text-xs font-bold uppercase tracking-[0.2em] text-bloom-muted">A clearer way to choose</p><h2 className="bloom-title mt-3 text-4xl text-bloom-navy sm:text-5xl">A little clarity before you go.</h2></div>
          <div className="mt-10 grid gap-5 lg:grid-cols-[0.82fr_1.18fr] lg:items-stretch">
            <article className="rounded-[2rem] border border-bloom-ink/20 bg-bloom-cream p-7 text-bloom-ink shadow-[3px_3px_0_#102A32] sm:p-8">
              <p className="text-4xl font-bold text-bloom-orange">01</p><h3 className="bloom-title mt-7 text-3xl">Name what you need.</h3><p className="mt-4 max-w-sm leading-relaxed text-bloom-muted">Begin with a product or brand. The search experience helps you narrow the catalog by the details that are available.</p><Link href="/products/search" className="bloom-button-secondary mt-7">Start exploring <span aria-hidden="true">→</span></Link>
            </article>
            <article className="rounded-[2rem] border border-bloom-cream/30 bg-bloom-avocado p-7 text-bloom-ink shadow-[3px_3px_0_#102A32] sm:p-8 lg:grid lg:grid-cols-[minmax(0,1fr)_minmax(0,0.82fr)] lg:gap-10">
              <div><p className="text-4xl font-bold text-bloom-navy">02</p><h3 className="bloom-title mt-7 text-4xl">Compare the same package.</h3><p className="mt-4 max-w-md leading-relaxed text-bloom-navy/80">See listed price ranges, available package sizes, and the dispensaries reporting each product. Missing information stays clear instead of being guessed.</p></div>
              <div className="mt-7 border-t border-bloom-ink/20 pt-6 lg:mt-0 lg:border-l lg:border-t-0 lg:pl-8 lg:pt-0"><p className="text-4xl font-bold text-bloom-navy">03</p><h3 className="bloom-title mt-7 text-3xl">Choose where to continue.</h3><p className="mt-4 leading-relaxed text-bloom-navy/80">When a listing has a valid destination, Mountain Bloom sends you to the licensed dispensary site to purchase.</p></div>
            </article>
          </div>
        </div>
      </section>

      <section className="bloom-container py-14 sm:py-20">
        <div className="grid items-center gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(18rem,0.72fr)]">
          <div className="max-w-xl"><p className="text-xs font-bold uppercase tracking-[0.2em] text-bloom-mustard">Licensed dispensaries</p><h2 className="bloom-title mt-3 text-4xl text-bloom-cream sm:text-5xl">Keep the local picture in view.</h2><p className="mt-5 text-base leading-relaxed text-bloom-cream/85">Browse the dispensaries Mountain Bloom tracks, then explore the details and inventory that each location makes available.</p></div>
          <div className="justify-self-start rounded-[2rem] border border-bloom-cream/30 bg-bloom-blue p-7 shadow-[4px_4px_0_#102A32] sm:p-8 lg:justify-self-end"><p className="max-w-sm text-lg font-bold text-bloom-cream">Find a licensed dispensary and continue your research there.</p><Link href="/dispensaries" className="bloom-button-secondary mt-7">Browse dispensaries <span aria-hidden="true">→</span></Link></div>
        </div>
      </section>

      <section className="border-y border-bloom-ink/20 bg-bloom-parchment py-14 text-bloom-ink sm:py-20">
        <div className="bloom-container text-center"><h2 className="bloom-title mx-auto max-w-2xl text-4xl sm:text-5xl">Ready to see what is listed?</h2><p className="mx-auto mt-4 max-w-xl leading-relaxed text-bloom-muted">Start with a product name or brand and let the available comparisons guide your next step.</p><Link href="/products/search" className="bloom-button mt-8">Search products <span aria-hidden="true">→</span></Link></div>
      </section>
    </div>
  )
}
