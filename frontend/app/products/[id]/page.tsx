'use client'

import React, { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { api } from '@/lib/api'
import PriceComparisonTable from '@/components/PriceComparisonTable'
import PricingChart from '@/components/PricingChart'
import ReviewsSection from '@/components/ReviewsSection'
import WatchlistButton from '@/components/WatchlistButton'
import CannabisLeaf from '@/components/CannabisLeaf'

interface Variant {
  id: string
  weight: string | null
  weight_grams: number | null
}

interface Product {
  id: string
  name: string
  brand: string | null
  brand_id: string | null
  product_type: string
  thc_percentage: number | null
  cbd_percentage: number | null
  is_master: boolean
  normalization_confidence: number | null
  variants: Variant[]
  created_at: string | null
  updated_at: string | null
}

interface RelatedProduct {
  id: string
  name: string
  brand: string | null
  product_type: string
  thc_percentage: number | null
  cbd_percentage: number | null
  min_price: number | null
  max_price: number | null
  similarity_score?: number
}

interface PriceData {
  dispensary_id: string
  dispensary_name: string
  dispensary_location: string
  dispensary_hours: string | null
  dispensary_website: string | null
  msrp: number
  deal_price: number | null
  savings: number | null
  savings_percentage: number | null
  in_stock: boolean
  promotion: {
    id: string
    title: string
    description: string | null
    discount_percentage: number | null
    discount_amount: number | null
  } | null
  last_updated: string | null
  product_url: string | null
}

interface WeightGroup {
  variant_id: string
  weight: string | null
  weight_grams: number | null
  prices: PriceData[]
}

export default function ProductDetailPage() {
  const params = useParams()
  const productId = params.id as string
  const [product, setProduct] = useState<Product | null>(null)
  const [weightGroups, setWeightGroups] = useState<WeightGroup[]>([])
  const [relatedProducts, setRelatedProducts] = useState<RelatedProduct[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (productId) loadProductData()
  }, [productId])

  const loadProductData = async () => {
    try {
      setLoading(true)
      setError(null)
      const [productRes, pricesRes, relatedRes] = await Promise.all([
        api.products.get(productId),
        api.products.getPrices(productId),
        api.products.getRelated(productId, 8).catch(() => ({ data: [] }))
      ])
      setProduct(productRes.data)
      setWeightGroups(pricesRes.data)
      setRelatedProducts(relatedRes.data)
    } catch (err: any) {
      setError(err.response?.status === 404 ? 'Product not found' : 'Failed to load product data')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-groovy-cream flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-groovy-teal border-t-transparent"></div>
          <p className="mt-4 font-display font-semibold text-groovy-ink">Loading product…</p>
        </div>
      </div>
    )
  }

  if (error || !product) {
    return (
      <div className="min-h-screen bg-groovy-cream flex items-center justify-center">
        <div className="text-center card-sticker p-10 max-w-sm">
          <CannabisLeaf size={56} color="#9CA3AF" className="mx-auto mb-4" />
          <h2 className="font-display font-bold text-xl text-groovy-ink mb-2">{error || 'Product not found'}</h2>
          <Link href="/products/search" className="btn-groovy-teal mt-4">
            ← Back to Search
          </Link>
        </div>
      </div>
    )
  }

  const allPrices = weightGroups.flatMap(g => g.prices)
  const bestPrice = allPrices.length > 0
    ? allPrices.reduce((best, p) => {
        const bestVal = best.deal_price ?? best.msrp
        const pVal = p.deal_price ?? p.msrp
        return pVal < bestVal ? p : best
      })
    : null
  const inStockCount = allPrices.filter(p => p.in_stock).length
  const nonNullWeights = [...new Set(weightGroups.map(g => g.weight).filter((w): w is string => w !== null))]
  const hasMultipleWeights = nonNullWeights.length > 1
  const displayGroups = hasMultipleWeights
    ? nonNullWeights.map(w => ({
        weight: w,
        prices: weightGroups.filter(g => g.weight === w || g.weight === null).flatMap(g => g.prices),
      }))
    : [{ weight: nonNullWeights[0] ?? null, prices: allPrices }]

  return (
    <div className="min-h-screen bg-groovy-cream">
      {/* Compliance */}
      <div className="compliance-banner">
        <div className="max-w-4xl mx-auto flex items-center gap-2">
          <CannabisLeaf size={16} color="#1C1917" />
          <p className="text-sm">⚠️ For informational purposes only. Not affiliated with any dispensary. Does not sell controlled substances.</p>
        </div>
      </div>

      {/* Breadcrumb */}
      <div className="bg-white border-b-2 border-stone-200">
        <div className="max-w-4xl mx-auto px-4 py-3">
          <nav className="text-sm font-body text-stone-500 flex items-center gap-2">
            <Link href="/" className="hover:text-groovy-teal transition-colors">Home</Link>
            <span>/</span>
            <Link href="/products/search" className="hover:text-groovy-teal transition-colors">Search</Link>
            <span>/</span>
            <span className="text-groovy-ink font-semibold truncate">{product.name}</span>
          </nav>
        </div>
      </div>

      {/* Product Hero Header — retro gradient band */}
      <div
        className="border-b-4 border-groovy-ink relative overflow-hidden"
        style={{
          background: 'linear-gradient(135deg, #F59E0B 0%, #F97316 40%, #0D9488 100%)',
          filter: 'saturate(115%) contrast(105%)',
        }}
      >
        {/* Decorative leaves */}
        <div className="absolute right-6 top-4 opacity-20 hidden md:block">
          <CannabisLeaf size={72} color="#FFF8EE" rotate={20} />
        </div>
        <div className="absolute right-20 bottom-0 opacity-15 hidden md:block">
          <CannabisLeaf size={48} color="#FFF8EE" rotate={-15} variant="sprig" />
        </div>

        <div className="relative max-w-4xl mx-auto px-4 py-10">
          <div className="flex flex-col md:flex-row md:justify-between md:items-start gap-6">
            <div>
              <h1
                className="font-display font-bold text-white leading-tight"
                style={{
                  fontSize: 'clamp(2rem, 5vw, 3.5rem)',
                  WebkitTextStroke: '1.5px rgba(28,25,23,0.3)',
                }}
              >
                {product.name}
              </h1>
              {product.brand && (
                <p className="font-body text-white/80 text-lg mt-1">by {product.brand}</p>
              )}
              <div className="flex items-center gap-3 mt-3">
                <span className="font-display font-bold text-sm px-3 py-1 bg-groovy-sun text-groovy-ink rounded-full border-2 border-groovy-ink shadow-[2px_2px_0px_#1C1917]">
                  {product.product_type}
                </span>
                <div className="mt-0 [&>button]:border-white [&>button]:text-white">
                  <WatchlistButton productId={productId} />
                </div>
              </div>
            </div>

            {bestPrice && (
              <div className="bg-white/20 backdrop-blur-sm border-2 border-white/40 rounded-2xl px-6 py-4 text-right flex-shrink-0">
                <p className="font-body text-white/70 text-sm">Best Price</p>
                <p className="font-display font-bold text-3xl text-groovy-sun">
                  ${(bestPrice.deal_price || bestPrice.msrp).toFixed(2)}
                </p>
                {bestPrice.deal_price && bestPrice.savings_percentage && (
                  <span className="inline-block font-display font-bold text-xs px-2 py-0.5 bg-groovy-sun text-groovy-ink rounded-full border-2 border-groovy-ink mt-1">
                    Save {bestPrice.savings_percentage}%
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Stats row */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-8">
            {product.thc_percentage !== null && (
              <div className="bg-white/20 backdrop-blur-sm border-2 border-white/30 rounded-2xl p-4">
                <p className="font-body text-white/70 text-xs">THC</p>
                <p className="font-display font-bold text-2xl text-groovy-sun">{product.thc_percentage}%</p>
              </div>
            )}
            {product.cbd_percentage !== null && (
              <div className="bg-white/20 backdrop-blur-sm border-2 border-white/30 rounded-2xl p-4">
                <p className="font-body text-white/70 text-xs">CBD</p>
                <p className="font-display font-bold text-2xl text-white">{product.cbd_percentage}%</p>
              </div>
            )}
            <div className="bg-white/20 backdrop-blur-sm border-2 border-white/30 rounded-2xl p-4">
              <p className="font-body text-white/70 text-xs">Dispensaries</p>
              <p className="font-display font-bold text-2xl text-white">{new Set(allPrices.map(p => p.dispensary_id)).size}</p>
            </div>
            <div className="bg-white/20 backdrop-blur-sm border-2 border-white/30 rounded-2xl p-4">
              <p className="font-body text-white/70 text-xs">In Stock</p>
              <p className="font-display font-bold text-2xl text-white">{inStockCount}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 py-10">

        {/* Price Comparison */}
        <section className="mb-12">
          <div className="flex items-center gap-3 mb-5">
            <CannabisLeaf size={24} color="#0D9488" rotate={-10} />
            <h2 className="font-display font-bold text-2xl text-groovy-ink">Prices Across Dispensaries</h2>
          </div>
          {displayGroups.length > 0 && allPrices.length > 0 ? (
            <div className="space-y-6">
              {displayGroups.map((group, i) => (
                <div key={group.weight ?? i}>
                  {hasMultipleWeights && group.weight && (
                    <h3 className="font-display font-semibold text-lg text-groovy-ink mb-2 px-1">{group.weight}</h3>
                  )}
                  <PriceComparisonTable prices={group.prices} productId={productId} productName={product.name} />
                </div>
              ))}
            </div>
          ) : (
            <div className="card-sticker p-8 text-center text-stone-500 font-body">
              No pricing data available for this product.
            </div>
          )}
        </section>

        {/* Price History */}
        <section className="mb-12">
          <div className="flex items-center gap-3 mb-5">
            <CannabisLeaf size={24} color="#F97316" rotate={15} />
            <h2 className="font-display font-bold text-2xl text-groovy-ink">Price History</h2>
          </div>
          <div className="card-sticker overflow-hidden">
            <PricingChart productId={productId} />
          </div>
        </section>

        {/* Reviews */}
        <section className="mb-12">
          <div className="flex items-center gap-3 mb-5">
            <CannabisLeaf size={24} color="#0D9488" rotate={-5} variant="sprig" />
            <h2 className="font-display font-bold text-2xl text-groovy-ink">Community Reviews</h2>
          </div>
          <ReviewsSection productId={productId} />
        </section>

        {/* Similar Products */}
        {relatedProducts.length > 0 && (
          <section>
            <div className="flex items-center gap-3 mb-5">
              <CannabisLeaf size={24} color="#F97316" rotate={10} />
              <h2 className="font-display font-bold text-2xl text-groovy-ink">Similar Products</h2>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {relatedProducts.map((rp) => (
                <Link
                  key={rp.id}
                  href={`/products/${rp.id}`}
                  className="card-sticker p-4 hover:-translate-y-0.5 transition-all duration-150 block"
                >
                  <h3 className="font-display font-bold text-sm text-groovy-ink leading-tight line-clamp-2">{rp.name}</h3>
                  {rp.brand && (
                    <p className="font-body text-xs text-stone-500 mt-1 truncate">{rp.brand}</p>
                  )}
                  <span className="inline-block mt-2 px-2 py-0.5 bg-groovy-sun text-groovy-ink text-xs font-display font-bold rounded-full border-2 border-groovy-ink">
                    {rp.product_type}
                  </span>
                  <div className="mt-2 flex items-center gap-2 text-xs font-body text-stone-600">
                    {rp.thc_percentage != null && <span>THC {rp.thc_percentage}%</span>}
                    {rp.cbd_percentage != null && <span>CBD {rp.cbd_percentage}%</span>}
                  </div>
                  {rp.min_price != null && (
                    <p className="mt-2 font-display font-bold text-sm text-groovy-teal">
                      {rp.min_price === rp.max_price
                        ? `$${rp.min_price.toFixed(2)}`
                        : `$${rp.min_price.toFixed(2)}–$${rp.max_price!.toFixed(2)}`}
                    </p>
                  )}
                </Link>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  )
}
