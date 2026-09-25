'use client'

import { Suspense, useEffect, useState } from 'react'
import { useParams, useSearchParams } from 'next/navigation'
import Image from 'next/image'
import Link from 'next/link'
import { api } from '@/lib/api'
import { comparisonGroups, money, potency, type ProductDetail, type RelatedProduct, type WeightGroup } from '@/lib/product-contracts'
import PriceComparisonTable from '@/components/PriceComparisonTable'
import PricingChart from '@/components/PricingChart'
import ReviewsSection from '@/components/ReviewsSection'
import WatchlistButton from '@/components/WatchlistButton'
import ProductArtwork from '@/components/bloom/ProductArtwork'
import JourneyState from '@/components/bloom/JourneyState'

function ProductExperience() {
  const productId = useParams().id as string
  const search = useSearchParams()
  const returnTo = search.get('returnTo')
  const back = returnTo === '/products/search' || returnTo?.startsWith('/products/search?') ? returnTo : '/products/search'
  const [product, setProduct] = useState<ProductDetail | null>(null)
  const [groups, setGroups] = useState<WeightGroup[]>([])
  const [related, setRelated] = useState<RelatedProduct[]>([])
  const [status, setStatus] = useState<'loading' | 'ready' | 'missing' | 'error'>('loading')
  const [priceStatus, setPriceStatus] = useState<'loading' | 'ready' | 'error'>('loading')
  const [relatedError, setRelatedError] = useState(false)
  const [selectedId, setSelectedId] = useState('')
  const [retry, setRetry] = useState(0)
  const [priceRetry, setPriceRetry] = useState(0)

  useEffect(() => {
    let current = true
    setStatus('loading'); setProduct(null); setSelectedId(productId)
    api.products.get(productId).then(response => { if (current) { setProduct(response.data); setStatus('ready') } }).catch(error => { if (current) setStatus(error.response?.status === 404 ? 'missing' : 'error') })
    return () => { current = false }
  }, [productId, retry])
  useEffect(() => {
    let current = true
    setPriceStatus('loading'); setGroups([])
    api.products.getPrices(productId).then(response => { if (current) { setGroups(response.data); setPriceStatus('ready') } }).catch(() => { if (current) setPriceStatus('error') })
    return () => { current = false }
  }, [productId, retry, priceRetry])
  useEffect(() => {
    let current = true
    setRelated([]); setRelatedError(false)
    api.products.getRelated(productId, 4).then(response => { if (current) setRelated(response.data) }).catch(() => { if (current) setRelatedError(true) })
    return () => { current = false }
  }, [productId, retry])

  if (status === 'loading') return <div className="bloom-page bloom-leaf-field"><div className="bloom-container py-12"><JourneyState busy title="Loading product details..." /></div></div>
  if (!product) return <div className="bloom-page bloom-leaf-field"><div className="bloom-container py-12"><JourneyState error title={status === 'missing' ? 'This product could not be found' : 'Product details could not be loaded'}><p>{status === 'missing' ? 'The listing may have changed. Search for the product or its brand.' : 'Your place is saved. Try loading this product again.'}</p><div className="mt-5 flex flex-wrap gap-3">{status !== 'missing' && <button className="bloom-button" onClick={() => setRetry(value => value + 1)}>Retry product</button>}<Link href={back} className="bloom-button-secondary">Back to discovery</Link></div></JourneyState></div></div>

  const variants = comparisonGroups(product, groups)
  const selected = variants.find(group => group.variant_id === selectedId) || variants[0]
  const label = (group: WeightGroup) => group.weight || (group.weight_grams != null ? `${group.weight_grams} g` : 'Size not reported')

  return <div className="bloom-page bloom-leaf-field pb-16">
    <section className="relative isolate h-40 overflow-hidden sm:h-48"><Image src="/images/mountain-bloom/groovy-van-hero.png" alt="" aria-hidden="true" fill priority unoptimized sizes="100vw" className="object-cover object-[center_36%]" /><div aria-hidden="true" className="absolute inset-0 bg-bloom-navy/50" /><div className="bloom-container relative z-10 flex h-full items-end pb-5"><Link className="bloom-button-glass" href={back}>← Back to discovery</Link></div></section>
    <section className="bloom-warm-surface py-8 sm:py-10">
      <div className="bloom-container grid items-stretch gap-6 md:grid-cols-[0.8fr_1.2fr]">
        <div className="self-start overflow-hidden rounded-[2rem] border border-bloom-ink/20 shadow-[4px_4px_0_#102A32]"><ProductArtwork type={product.product_type} priority /></div>
        <div className="bloom-card min-w-0 p-6 sm:p-8"><p className="text-xs font-bold uppercase tracking-[0.15em] text-bloom-navy/75">{product.brand || 'Brand not reported'} · {product.product_type}</p><h1 className="bloom-title mt-3 text-4xl sm:text-5xl">{product.name}</h1><p className="mt-4 max-w-lg text-sm leading-relaxed">A little clarity before you choose. Compare the same package size, then confirm availability with the dispensary.</p><dl className="mt-7 grid grid-cols-2 gap-4 border-y border-bloom-ink/25 py-5"><div><dt className="text-xs font-bold uppercase tracking-wider">THC</dt><dd className="mt-1 text-xl font-bold">{potency(product.thc_percentage)}</dd></div><div><dt className="text-xs font-bold uppercase tracking-wider">CBD</dt><dd className="mt-1 text-xl font-bold">{potency(product.cbd_percentage)}</dd></div></dl><div className="mt-5 flex flex-wrap items-center gap-3"><a href="#compare-offers" className="bloom-button">Compare offers ↓</a><WatchlistButton productId={product.id} /></div><p className="mt-3 text-xs text-bloom-navy/75">Potency can vary by batch. Confirm the product label; this is not medical advice.</p></div>
      </div>
    </section>
    <div className="bloom-container py-10 sm:py-12">
      <section id="compare-offers" className="scroll-mt-6" aria-labelledby="compare-title"><div className="mb-6 flex flex-wrap items-end justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-widest text-bloom-mustard">Find your offering</p><h2 id="compare-title" className="bloom-title mt-2 text-4xl">Same size. Clearer choice.</h2></div><p className="max-w-sm text-sm text-bloom-cream/80">Listings can change. Confirm stock, taxes, promotions, and final price with the dispensary.</p></div>{priceStatus === 'loading' ? <JourneyState busy title="Loading dispensary offers..." /> : priceStatus === 'error' ? <JourneyState error title="Offers could not be loaded"><p>Product details are still available. Try the prices again.</p><button className="bloom-button mt-4" onClick={() => setPriceRetry(value => value + 1)}>Retry offers</button></JourneyState> : <>{variants.length > 0 && <fieldset className="mb-6"><legend className="mb-3 font-bold">Choose a package size</legend><div className="flex flex-wrap gap-3">{variants.map((group, index) => <label key={group.variant_id} className={`flex min-h-[48px] cursor-pointer items-center gap-2 rounded-full border px-4 py-3 text-sm font-bold shadow-[3px_3px_0_#102A32] transition-all duration-200 hover:-translate-x-0.5 hover:-translate-y-0.5 ${selected?.variant_id === group.variant_id ? 'border-bloom-ink bg-bloom-orange text-bloom-cream' : 'border-bloom-cream/40 bg-bloom-blue text-bloom-cream'}`}><input className="h-4 w-4 accent-bloom-mustard" type="radio" name="package" checked={selected?.variant_id === group.variant_id} onChange={() => setSelectedId(group.variant_id)} value={group.variant_id} />{label(group)}{variants.filter(item => label(item) === label(group)).length > 1 && ` · option ${index + 1}`}</label>)}</div></fieldset>}<div aria-live="polite" className="mb-4 text-sm text-bloom-cream/80">{selected && <p>{label(selected)} · {selected.prices.length} {selected.prices.length === 1 ? 'offering' : 'offerings'}{!selected.weight && selected.weight_grams == null ? '. Confirm package size before comparing value.' : ''}</p>}</div>{selected?.prices.length ? <PriceComparisonTable prices={selected.prices} weightGrams={selected.weight_grams} /> : <JourneyState title="No current prices for this package"><p>Try another package size or return to discovery. Missing prices do not mean the product is out of stock everywhere.</p><Link href={back} className="bloom-button-secondary mt-4">Back to discovery</Link></JourneyState>}</>}</section>
    </div>
    <section className="bloom-warm-surface py-10 sm:py-12"><div className="bloom-container space-y-12"><PricingChart productId={product.id} /><section aria-label="Community reviews"><ReviewsSection productId={product.id} /></section>{(related.length > 0 || relatedError) && <section aria-labelledby="related-title"><h2 id="related-title" className="bloom-title text-4xl">Keep exploring</h2><p className="mt-3 text-sm text-bloom-navy/75">Similar catalog entries, not personalized or medical recommendations.</p>{relatedError ? <p className="mt-4 text-sm">Similar products are unavailable right now. <Link href={back} className="underline">Continue discovery</Link>.</p> : <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{related.map(item => <Link key={item.id} href={`/products/${item.id}?returnTo=${encodeURIComponent(back)}`} className="bloom-card block p-5 transition-transform duration-200 hover:-translate-y-1 hover:shadow-[6px_6px_0_#102A32]"><p className="text-xs text-bloom-navy/75">{item.brand || 'Brand not reported'} · {item.product_type}</p><h3 className="mt-2 text-lg font-bold">{item.name}</h3><p className="mt-3 text-sm">THC {potency(item.thc_percentage)} · CBD {potency(item.cbd_percentage)}</p><p className="mt-4 font-bold">{item.min_price == null ? 'Price not reported' : item.max_price != null && item.max_price !== item.min_price ? `${money(item.min_price)}–${money(item.max_price)}` : money(item.min_price)}</p><p className="mt-3 text-sm underline">Compare product →</p></Link>)}</div>}</section>}</div></section>
  </div>
}

export default function ProductDetailPage() {
  return <Suspense fallback={<div className="bloom-page bloom-leaf-field"><div className="bloom-container py-12"><JourneyState busy title="Loading product details..." /></div></div>}><ProductExperience /></Suspense>
}
