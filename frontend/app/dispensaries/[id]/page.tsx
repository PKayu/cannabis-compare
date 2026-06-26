'use client'

import React, { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { api } from '@/lib/api'
import CurrentPromotions from '@/components/CurrentPromotions'
import DispensaryInventory from '@/components/DispensaryInventory'
import CannabisLeaf from '@/components/CannabisLeaf'

interface Promotion {
  id: string
  title: string
  description: string | null
  discount_percentage: number | null
  discount_amount: number | null
  recurring_pattern: string | null
  start_date: string
  end_date: string | null
}

interface Dispensary {
  id: string
  name: string
  location: string
  hours: string | null
  website: string | null
  product_count: number
  promotions: Promotion[]
  created_at: string | null
}

export default function DispensaryDetailPage() {
  const params = useParams()
  const dispensaryId = params.id as string
  const [dispensary, setDispensary] = useState<Dispensary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (dispensaryId) loadDispensaryData()
  }, [dispensaryId])

  const loadDispensaryData = async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await api.dispensaries.get(dispensaryId)
      setDispensary(res.data)
    } catch (err: any) {
      setError(err.response?.status === 404 ? 'Dispensary not found' : 'Failed to load dispensary')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-groovy-cream flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-groovy-teal border-t-transparent"></div>
          <p className="mt-4 font-display font-semibold text-groovy-ink">Loading dispensary…</p>
        </div>
      </div>
    )
  }

  if (error || !dispensary) {
    return (
      <div className="min-h-screen bg-groovy-cream flex items-center justify-center">
        <div className="card-sticker p-10 max-w-sm text-center">
          <CannabisLeaf size={56} color="#9CA3AF" className="mx-auto mb-4" variant="stalk" />
          <h2 className="font-display font-bold text-xl text-groovy-ink mb-4">{error || 'Dispensary not found'}</h2>
          <Link href="/dispensaries" className="btn-groovy-teal">
            ← Back to Dispensaries
          </Link>
        </div>
      </div>
    )
  }

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
            <Link href="/dispensaries" className="hover:text-groovy-teal transition-colors">Dispensaries</Link>
            <span>/</span>
            <span className="text-groovy-ink font-semibold truncate">{dispensary.name}</span>
          </nav>
        </div>
      </div>

      {/* Dispensary Hero — cobalt-to-teal gradient */}
      <div
        className="border-b-4 border-groovy-ink relative overflow-hidden"
        style={{
          background: 'linear-gradient(135deg, #2563EB 0%, #0D9488 60%, #0F766E 100%)',
          filter: 'saturate(110%) contrast(105%)',
        }}
      >
        {/* Decorative leaves */}
        <div className="absolute right-4 top-6 opacity-20 hidden md:block">
          <CannabisLeaf size={80} color="#FFF8EE" rotate={25} variant="stalk" />
        </div>
        <div className="absolute left-8 bottom-0 opacity-15 hidden md:block">
          <CannabisLeaf size={56} color="#FFF8EE" rotate={-20} />
        </div>
        <div className="absolute right-32 top-4 opacity-15 hidden lg:block">
          <CannabisLeaf size={40} color="#FFF8EE" rotate={10} variant="sprig" />
        </div>

        <div className="relative max-w-4xl mx-auto px-4 py-10">
          <div className="flex flex-col md:flex-row md:justify-between md:items-start gap-6">
            <div>
              <h1
                className="font-display font-bold text-white leading-tight"
                style={{
                  fontSize: 'clamp(2rem, 5vw, 3.5rem)',
                  WebkitTextStroke: '1.5px rgba(28,25,23,0.25)',
                }}
              >
                {dispensary.name}
              </h1>
              <p className="font-body text-white/80 mt-2 flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                {dispensary.location}
              </p>
              {dispensary.hours && (
                <p className="font-body text-white/70 mt-1 flex items-center gap-2 text-sm">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {dispensary.hours}
                </p>
              )}
            </div>

            {dispensary.website && (
              <a
                href={dispensary.website}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-shrink-0 inline-flex items-center gap-2 font-display font-bold px-5 py-3 bg-groovy-sun text-groovy-ink rounded-2xl border-2 border-groovy-ink shadow-[4px_4px_0px_#1C1917] hover:-translate-y-0.5 hover:shadow-[6px_6px_0px_#1C1917] transition-all duration-150"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
                Visit Website
              </a>
            )}
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-3 mt-8">
            <div className="bg-white/20 backdrop-blur-sm border-2 border-white/30 rounded-2xl p-4">
              <p className="font-body text-white/70 text-xs">Products</p>
              <p className="font-display font-bold text-2xl text-groovy-sun">{dispensary.product_count}</p>
            </div>
            <div className="bg-white/20 backdrop-blur-sm border-2 border-white/30 rounded-2xl p-4">
              <p className="font-body text-white/70 text-xs">Active Deals</p>
              <p className="font-display font-bold text-2xl text-white">{dispensary.promotions.length}</p>
            </div>
            <div className="bg-white/20 backdrop-blur-sm border-2 border-white/30 rounded-2xl p-4">
              <p className="font-body text-white/70 text-xs">License</p>
              <div className="flex items-center gap-1.5 mt-1">
                <span className="w-2.5 h-2.5 rounded-full bg-groovy-sun flex-shrink-0"></span>
                <p className="font-display font-bold text-base text-white">Active</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 py-10">

        {/* Promotions */}
        {dispensary.promotions.length > 0 && (
          <section className="mb-12">
            <div className="flex items-center gap-3 mb-5">
              <CannabisLeaf size={24} color="#F97316" rotate={-10} />
              <h2 className="font-display font-bold text-2xl text-groovy-ink">Current Promotions & Deals</h2>
            </div>
            <CurrentPromotions promotions={dispensary.promotions} />
          </section>
        )}

        {/* Inventory */}
        <section className="mb-12">
          <div className="flex items-center gap-3 mb-5">
            <CannabisLeaf size={24} color="#0D9488" rotate={10} variant="stalk" />
            <h2 className="font-display font-bold text-2xl text-groovy-ink">Inventory</h2>
          </div>
          <DispensaryInventory dispensaryId={dispensaryId} />
        </section>
      </div>
    </div>
  )
}
