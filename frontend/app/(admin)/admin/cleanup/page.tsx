'use client'

import React, { useEffect, useState } from 'react'
import { api } from '@/lib/api'

interface MatchedProduct {
  id: string
  name: string
  brand: string | null
  thc_percentage: number | null
  cbd_percentage: number | null
}

interface ScraperFlag {
  id: string
  original_name: string
  original_thc: number | null
  original_cbd: number | null
  original_weight: string | null
  original_price: number | null
  original_category: string | null
  brand_name: string
  dispensary_id: string
  dispensary_name: string | null
  matched_product_id: string | null
  matched_product: MatchedProduct | null
  confidence_score: number
  confidence_percent: string
  created_at: string
}

interface FlagStats {
  pending: number
  approved: number
  rejected: number
  total: number
}

export default function CleanupQueuePage() {
  const [flags, setFlags] = useState<ScraperFlag[]>([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<FlagStats | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadFlags()
    loadStats()
  }, [])

  const loadFlags = async () => {
    try {
      const res = await api.get('/api/admin/flags/pending?limit=50')
      setFlags(res.data)
      setError(null)
    } catch (err) {
      console.error('Failed to load flags:', err)
      setError('Failed to load pending flags')
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const res = await api.get('/api/admin/flags/stats')
      setStats(res.data)
    } catch (err) {
      console.error('Failed to load stats:', err)
    }
  }

  const handleApprove = async (flagId: string, notes: string) => {
    try {
      await api.post(`/api/admin/flags/approve/${flagId}`, { notes })
      setFlags(flags.filter(f => f.id !== flagId))
      loadStats()
    } catch (err) {
      console.error('Failed to approve flag:', err)
      setError('Failed to approve flag')
    }
  }

  const handleReject = async (flagId: string, notes: string) => {
    try {
      await api.post(`/api/admin/flags/reject/${flagId}`, { notes })
      setFlags(flags.filter(f => f.id !== flagId))
      loadStats()
    } catch (err) {
      console.error('Failed to reject flag:', err)
      setError('Failed to reject flag')
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-600">Loading cleanup queue...</div>
      </div>
    )
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2 text-gray-900">Cleanup Queue</h2>
      <p className="text-gray-600 mb-6">
        Review and resolve product naming discrepancies from scraped data.
      </p>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
              <p className="text-sm text-yellow-700 font-medium">Pending Review</p>
              <p className="text-3xl font-bold text-yellow-900">{stats.pending}</p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg border border-green-200">
              <p className="text-sm text-green-700 font-medium">Approved</p>
              <p className="text-3xl font-bold text-green-900">{stats.approved}</p>
            </div>
            <div className="bg-red-50 p-4 rounded-lg border border-red-200">
              <p className="text-sm text-red-700 font-medium">Rejected</p>
              <p className="text-3xl font-bold text-red-900">{stats.rejected}</p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
              <p className="text-sm text-gray-700 font-medium">Total Processed</p>
              <p className="text-3xl font-bold text-gray-900">{stats.total}</p>
            </div>
          </div>
        )}

        {/* Flags List */}
        {flags.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <p className="text-gray-600 text-lg">No pending flags to review.</p>
            <p className="text-gray-500 mt-2">All product matches have been processed.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {flags.map((flag) => (
              <FlagCard
                key={flag.id}
                flag={flag}
                onApprove={handleApprove}
                onReject={handleReject}
              />
            ))}
          </div>
        )}
    </div>
  )
}

interface FlagCardProps {
  flag: ScraperFlag
  onApprove: (flagId: string, notes: string) => Promise<void>
  onReject: (flagId: string, notes: string) => Promise<void>
}

function FlagCard({ flag, onApprove, onReject }: FlagCardProps) {
  const [notes, setNotes] = useState('')
  const [processing, setProcessing] = useState(false)

  const confidenceColor =
    flag.confidence_score >= 0.8 ? 'text-green-600' :
    flag.confidence_score >= 0.7 ? 'text-yellow-600' : 'text-orange-600'

  return (
    <div className="bg-white border rounded-lg shadow-sm overflow-hidden">
      <div className="p-4 border-b bg-gray-50">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="font-bold text-lg text-gray-900">{flag.original_name}</h3>
            <p className="text-gray-600">{flag.brand_name}</p>
          </div>
          <div className="text-right">
            <p className={`font-semibold ${confidenceColor}`}>
              {(flag.confidence_score * 100).toFixed(1)}% match
            </p>
            <p className="text-sm text-gray-500">{flag.dispensary_name}</p>
          </div>
        </div>
      </div>

      <div className="p-4">
        {/* Comparison View */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="bg-gray-50 p-3 rounded">
            <p className="text-sm font-medium text-gray-700 mb-2">Scraped Data</p>
            <p className="font-semibold">{flag.original_name}</p>
            <p className="text-sm text-gray-600">Brand: {flag.brand_name}</p>
            {flag.original_thc && (
              <p className="text-sm text-gray-600">THC: {flag.original_thc}%</p>
            )}
            {flag.original_cbd && (
              <p className="text-sm text-gray-600">CBD: {flag.original_cbd}%</p>
            )}
            {flag.original_weight && (
              <p className="text-sm text-gray-600">Weight: {flag.original_weight}</p>
            )}
            {flag.original_price != null && (
              <p className="text-sm text-gray-600">Price: ${flag.original_price.toFixed(2)}</p>
            )}
            {flag.original_category && (
              <p className="text-sm text-gray-600">Category: {flag.original_category}</p>
            )}
          </div>

          {flag.matched_product ? (
            <div className="bg-blue-50 p-3 rounded">
              <p className="text-sm font-medium text-blue-700 mb-2">Matched Product</p>
              <p className="font-semibold">{flag.matched_product.name}</p>
              <p className="text-sm text-gray-600">Brand: {flag.matched_product.brand || 'N/A'}</p>
              {flag.matched_product.thc_percentage && (
                <p className="text-sm text-gray-600">THC: {flag.matched_product.thc_percentage}%</p>
              )}
              {flag.matched_product.cbd_percentage && (
                <p className="text-sm text-gray-600">CBD: {flag.matched_product.cbd_percentage}%</p>
              )}
            </div>
          ) : (
            <div className="bg-gray-50 p-3 rounded">
              <p className="text-sm font-medium text-gray-700 mb-2">No Match Found</p>
              <p className="text-gray-500">Will create new product if rejected</p>
            </div>
          )}
        </div>

        {/* Admin Notes */}
        <textarea
          className="w-full p-3 border rounded-lg text-sm resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          placeholder="Admin notes (optional)..."
          rows={2}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />

        {/* Action Buttons */}
        <div className="flex gap-3 mt-4">
          <button
            className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            onClick={async () => {
              setProcessing(true)
              await onApprove(flag.id, notes)
              setProcessing(false)
            }}
            disabled={processing || !flag.matched_product}
            title={!flag.matched_product ? 'No product to merge with' : 'Approve merge'}
          >
            {processing ? 'Processing...' : 'Approve Merge'}
          </button>
          <button
            className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            onClick={async () => {
              setProcessing(true)
              await onReject(flag.id, notes)
              setProcessing(false)
            }}
            disabled={processing}
          >
            {processing ? 'Processing...' : 'Reject (Create New)'}
          </button>
        </div>
      </div>

      <div className="px-4 py-2 bg-gray-50 border-t text-xs text-gray-500">
        Created: {new Date(flag.created_at).toLocaleString()}
      </div>
    </div>
  )
}
