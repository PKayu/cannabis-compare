'use client'

import React, { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { api } from '@/lib/api'
import PriceComparisonTable from '@/components/PriceComparisonTable'
import PricingChart from '@/components/PricingChart'
import ReviewsSection from '@/components/ReviewsSection'
import WatchlistButton from '@/components/WatchlistButton'

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
  created_at: string | null
  updated_at: string | null
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
}

export default function ProductDetailPage() {
  const params = useParams()
  const productId = params.id as string
  const [product, setProduct] = useState<Product | null>(null)
  const [prices, setPrices] = useState<PriceData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (productId) {
      loadProductData()
    }
  }, [productId])

  const loadProductData = async () => {
    try {
      setLoading(true)
      setError(null)

      const [productRes, pricesRes] = await Promise.all([
        api.products.get(productId),
        api.products.getPrices(productId)
      ])

      setProduct(productRes.data)
      setPrices(pricesRes.data)
    } catch (err: any) {
      console.error('Failed to load product:', err)
      setError(err.response?.status === 404 ? 'Product not found' : 'Failed to load product data')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-cannabis-600"></div>
          <p className="mt-4 text-gray-600">Loading product...</p>
        </div>
      </div>
    )
  }

  if (error || !product) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <svg className="mx-auto h-16 w-16 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h2 className="mt-4 text-xl font-semibold text-gray-700">{error || 'Product not found'}</h2>
          <Link href="/products/search" className="mt-4 inline-block text-cannabis-600 hover:underline">
            ← Back to Search
          </Link>
        </div>
      </div>
    )
  }

  const bestPrice = prices.length > 0 ? prices[0] : null
  const inStockCount = prices.filter(p => p.in_stock).length

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Compliance Banner */}
      <div className="bg-yellow-50 border-b border-yellow-200 py-2 px-4">
        <div className="max-w-7xl mx-auto">
          <p className="text-sm text-yellow-800 text-center">
            ⚠️ For informational purposes only. Not affiliated with any dispensary.
            This site does not sell controlled substances.
          </p>
        </div>
      </div>

      {/* Breadcrumb */}
      <div className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-4 py-3">
          <nav className="text-sm text-gray-600">
            <Link href="/" className="hover:text-cannabis-600">Home</Link>
            <span className="mx-2">/</span>
            <Link href="/products/search" className="hover:text-cannabis-600">Search</Link>
            <span className="mx-2">/</span>
            <span className="text-gray-900">{product.name}</span>
          </nav>
        </div>
      </div>

      {/* Product Header */}
      <div className="bg-white shadow">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="flex flex-col md:flex-row md:justify-between md:items-start">
            <div>
              <h1 className="text-3xl md:text-4xl font-bold text-cannabis-700">{product.name}</h1>
              {product.brand && (
                <p className="text-xl text-gray-600 mt-2">by {product.brand}</p>
              )}
              <span className="inline-block mt-3 px-3 py-1 bg-cannabis-100 text-cannabis-800 rounded-full text-sm">
                {product.product_type}
              </span>

              {/* Watchlist Button */}
              <div className="mt-4">
                <WatchlistButton productId={productId} />
              </div>
            </div>

            {bestPrice && (
              <div className="mt-4 md:mt-0 text-right">
                <p className="text-gray-600 text-sm">Best Price</p>
                <p className="text-3xl font-bold text-green-600">
                  ${(bestPrice.deal_price || bestPrice.msrp).toFixed(2)}
                </p>
                {bestPrice.deal_price && bestPrice.savings_percentage && (
                  <span className="inline-block px-2 py-1 bg-green-100 text-green-800 rounded text-sm">
                    Save {bestPrice.savings_percentage}%
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
            {product.thc_percentage !== null && (
              <div className="bg-cannabis-50 p-4 rounded-lg">
                <p className="text-gray-600 text-sm">THC</p>
                <p className="text-2xl font-bold text-cannabis-700">{product.thc_percentage}%</p>
              </div>
            )}
            {product.cbd_percentage !== null && (
              <div className="bg-blue-50 p-4 rounded-lg">
                <p className="text-gray-600 text-sm">CBD</p>
                <p className="text-2xl font-bold text-blue-700">{product.cbd_percentage}%</p>
              </div>
            )}
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-gray-600 text-sm">Dispensaries</p>
              <p className="text-2xl font-bold text-gray-700">{prices.length}</p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-gray-600 text-sm">In Stock</p>
              <p className="text-2xl font-bold text-gray-700">{inStockCount}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Price Comparison */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold mb-4 text-gray-800">Prices Across Dispensaries</h2>
          {prices.length > 0 ? (
            <PriceComparisonTable prices={prices} productId={productId} />
          ) : (
            <div className="bg-white rounded-lg shadow p-6 text-center text-gray-600">
              No pricing data available for this product.
            </div>
          )}
        </section>

        {/* Pricing History */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold mb-4 text-gray-800">Price History</h2>
          <PricingChart productId={productId} />
        </section>

        {/* Reviews */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold mb-4 text-gray-800">Community Reviews</h2>
          <ReviewsSection productId={productId} />
        </section>

        {/* Related Products - placeholder for now */}
        <section>
          <h2 className="text-2xl font-bold mb-4 text-gray-800">Related Products</h2>
          <p className="text-gray-600 text-center py-8 bg-white rounded-lg shadow">
            Related products feature coming soon.
          </p>
        </section>
      </div>
    </div>
  )
}
