'use client'

import React, { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { api } from '@/lib/api'
import CurrentPromotions from '@/components/CurrentPromotions'
import DispensaryInventory from '@/components/DispensaryInventory'

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
    if (dispensaryId) {
      loadDispensaryData()
    }
  }, [dispensaryId])

  const loadDispensaryData = async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await api.dispensaries.get(dispensaryId)
      setDispensary(res.data)
    } catch (err: any) {
      console.error('Failed to load dispensary:', err)
      setError(err.response?.status === 404 ? 'Dispensary not found' : 'Failed to load dispensary')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-cannabis-600"></div>
          <p className="mt-4 text-gray-600">Loading dispensary...</p>
        </div>
      </div>
    )
  }

  if (error || !dispensary) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <svg className="mx-auto h-16 w-16 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
          <h2 className="mt-4 text-xl font-semibold text-gray-700">{error || 'Dispensary not found'}</h2>
          <Link href="/dispensaries" className="mt-4 inline-block text-cannabis-600 hover:underline">
            ← Back to Dispensaries
          </Link>
        </div>
      </div>
    )
  }

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
            <Link href="/dispensaries" className="hover:text-cannabis-600">Dispensaries</Link>
            <span className="mx-2">/</span>
            <span className="text-gray-900">{dispensary.name}</span>
          </nav>
        </div>
      </div>

      {/* Dispensary Header */}
      <div className="bg-white shadow">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="flex flex-col md:flex-row md:justify-between md:items-start">
            <div>
              <h1 className="text-3xl md:text-4xl font-bold text-cannabis-700">{dispensary.name}</h1>
              <p className="text-gray-600 mt-2 flex items-center">
                <svg className="w-5 h-5 mr-2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                {dispensary.location}
              </p>
              {dispensary.hours && (
                <p className="text-gray-600 mt-1 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
                className="mt-4 md:mt-0 inline-flex items-center px-4 py-2 bg-cannabis-600 text-white rounded-lg hover:bg-cannabis-700 transition-colors"
              >
                <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
                Visit Website
              </a>
            )}
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-6">
            <div className="bg-cannabis-50 p-4 rounded-lg">
              <p className="text-gray-600 text-sm">Products in Stock</p>
              <p className="text-2xl font-bold text-cannabis-700">{dispensary.product_count}</p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <p className="text-gray-600 text-sm">Active Deals</p>
              <p className="text-2xl font-bold text-green-700">{dispensary.promotions.length}</p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg col-span-2 md:col-span-1">
              <p className="text-gray-600 text-sm">License Status</p>
              <p className="text-lg font-semibold text-gray-700">
                <span className="inline-flex items-center">
                  <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                  Active
                </span>
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Current Promotions */}
        {dispensary.promotions.length > 0 && (
          <section className="mb-12">
            <h2 className="text-2xl font-bold mb-4 text-gray-800">Current Promotions & Deals</h2>
            <CurrentPromotions promotions={dispensary.promotions} />
          </section>
        )}

        {/* Inventory */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold mb-4 text-gray-800">Inventory</h2>
          <DispensaryInventory dispensaryId={dispensaryId} />
        </section>
      </div>
    </div>
  )
}
