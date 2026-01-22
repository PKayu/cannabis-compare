'use client'

import React, { useEffect, useState } from 'react'
import Link from 'next/link'
import { api } from '@/lib/api'
import DispensaryList from '@/components/DispensaryList'

interface Dispensary {
  id: string
  name: string
  location: string
  hours: string | null
  website: string | null
  product_count: number
  active_promotions: number
  created_at: string | null
}

export default function DispensariesPage() {
  const [dispensaries, setDispensaries] = useState<Dispensary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadDispensaries()
  }, [])

  const loadDispensaries = async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await api.dispensaries.list()
      setDispensaries(res.data)
    } catch (err) {
      console.error('Failed to load dispensaries:', err)
      setError('Failed to load dispensaries')
    } finally {
      setLoading(false)
    }
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
        <div className="max-w-6xl mx-auto px-4 py-3">
          <nav className="text-sm text-gray-600">
            <Link href="/" className="hover:text-cannabis-600">Home</Link>
            <span className="mx-2">/</span>
            <span className="text-gray-900">Dispensaries</span>
          </nav>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="flex flex-col md:flex-row md:justify-between md:items-center mb-8">
          <div>
            <h1 className="text-3xl md:text-4xl font-bold text-cannabis-700">Utah Dispensaries</h1>
            <p className="text-gray-600 mt-2">
              Find medical cannabis dispensaries across Utah
            </p>
          </div>
          <div className="mt-4 md:mt-0">
            <span className="text-sm text-gray-500">
              {dispensaries.length} dispensaries found
            </span>
          </div>
        </div>

        {/* Utah Info Card */}
        <div className="bg-cannabis-50 border border-cannabis-200 rounded-lg p-4 mb-8">
          <h2 className="font-semibold text-cannabis-800">Utah Medical Cannabis Program</h2>
          <p className="text-sm text-cannabis-700 mt-1">
            Utah has 15 licensed medical cannabis pharmacies. A valid Utah Medical Cannabis Card is required for purchase.
          </p>
        </div>

        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-cannabis-600"></div>
            <p className="mt-4 text-gray-600">Loading dispensaries...</p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
            <p className="text-red-700">{error}</p>
            <button
              onClick={loadDispensaries}
              className="mt-2 text-red-600 hover:underline"
            >
              Try again
            </button>
          </div>
        )}

        {!loading && !error && dispensaries.length === 0 && (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
            <p className="mt-4 text-gray-600">No dispensaries found</p>
          </div>
        )}

        {!loading && !error && dispensaries.length > 0 && (
          <DispensaryList dispensaries={dispensaries} />
        )}
      </div>
    </div>
  )
}
