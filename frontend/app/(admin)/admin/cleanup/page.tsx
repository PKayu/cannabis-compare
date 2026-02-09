'use client'

import React, { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { CleanupSwipeView } from './components/CleanupSwipeView'
import { FlagCard } from './components/FlagCard'
import { ScraperFlag, FlagStats, EditableFields } from './hooks/useCleanupSession'

type ViewMode = 'swipe' | 'list'

export default function CleanupQueuePage() {
  const [viewMode, setViewMode] = useState<ViewMode>('swipe')

  // List view state (only loaded when in list mode)
  const [listFlags, setListFlags] = useState<ScraperFlag[]>([])
  const [listStats, setListStats] = useState<FlagStats | null>(null)
  const [listLoading, setListLoading] = useState(false)
  const [listError, setListError] = useState<string | null>(null)

  // Load list data when switching to list view
  useEffect(() => {
    if (viewMode === 'list') {
      loadListData()
    }
  }, [viewMode])

  const loadListData = async () => {
    setListLoading(true)
    try {
      const [flagsRes, statsRes] = await Promise.all([
        api.admin.flags.pending({ limit: 50 }),
        api.admin.flags.stats(),
      ])
      setListFlags(flagsRes.data)
      setListStats(statsRes.data)
      setListError(null)
    } catch (err) {
      console.error('Failed to load flags:', err)
      setListError('Failed to load pending flags')
    } finally {
      setListLoading(false)
    }
  }

  const handleListApprove = async (flagId: string, edits?: Partial<EditableFields>, notes?: string, issueTags?: string[]) => {
    try {
      const data: Record<string, unknown> = { notes: notes || '' }
      if (edits) {
        if (edits.name) data.name = edits.name
        if (edits.brand_name) data.brand_name = edits.brand_name
        if (edits.product_type) data.product_type = edits.product_type
        if (edits.thc_percentage) data.thc_percentage = parseFloat(edits.thc_percentage)
        if (edits.cbd_percentage) data.cbd_percentage = parseFloat(edits.cbd_percentage)
        if (edits.weight) data.weight = edits.weight
        if (edits.price) data.price = parseFloat(edits.price)
      }
      if (issueTags && issueTags.length > 0) data.issue_tags = issueTags
      await api.admin.flags.approve(flagId, data)
      setListFlags(prev => prev.filter(f => f.id !== flagId))
      loadListStats()
    } catch (err) {
      console.error('Failed to approve:', err)
      setListError('Failed to approve flag')
    }
  }

  const handleListReject = async (flagId: string, edits?: Partial<EditableFields>, notes?: string, issueTags?: string[]) => {
    try {
      const data: Record<string, unknown> = { notes: notes || '' }
      if (edits) {
        if (edits.name) data.name = edits.name
        if (edits.brand_name) data.brand_name = edits.brand_name
        if (edits.product_type) data.product_type = edits.product_type
        if (edits.thc_percentage) data.thc_percentage = parseFloat(edits.thc_percentage)
        if (edits.cbd_percentage) data.cbd_percentage = parseFloat(edits.cbd_percentage)
        if (edits.weight) data.weight = edits.weight
        if (edits.price) data.price = parseFloat(edits.price)
      }
      if (issueTags && issueTags.length > 0) data.issue_tags = issueTags
      await api.admin.flags.reject(flagId, data)
      setListFlags(prev => prev.filter(f => f.id !== flagId))
      loadListStats()
    } catch (err) {
      console.error('Failed to reject:', err)
      setListError('Failed to reject flag')
    }
  }

  const handleListDismiss = async (flagId: string, notes?: string, issueTags?: string[]) => {
    try {
      const data: Record<string, unknown> = { notes: notes || '' }
      if (issueTags && issueTags.length > 0) data.issue_tags = issueTags
      await api.admin.flags.dismiss(flagId, data)
      setListFlags(prev => prev.filter(f => f.id !== flagId))
      loadListStats()
    } catch (err) {
      console.error('Failed to dismiss:', err)
      setListError('Failed to dismiss flag')
    }
  }

  const loadListStats = async () => {
    try {
      const res = await api.admin.flags.stats()
      setListStats(res.data)
    } catch {}
  }

  return (
    <div>
      {/* Header with View Toggle */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Cleanup Queue</h2>
          <p className="text-gray-600 text-sm mt-1">
            Review and resolve product naming discrepancies from scraped data.
          </p>
        </div>
        <div className="flex bg-gray-100 rounded-lg p-0.5">
          <button
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              viewMode === 'swipe'
                ? 'bg-white shadow text-gray-900'
                : 'text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => setViewMode('swipe')}
          >
            Swipe
          </button>
          <button
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              viewMode === 'list'
                ? 'bg-white shadow text-gray-900'
                : 'text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => setViewMode('list')}
          >
            List
          </button>
        </div>
      </div>

      {/* Swipe View */}
      {viewMode === 'swipe' && <CleanupSwipeView />}

      {/* List View */}
      {viewMode === 'list' && (
        <>
          {listError && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6 text-sm">
              {listError}
            </div>
          )}

          {/* Stats Cards */}
          {listStats && (
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
              <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
                <p className="text-sm text-yellow-700 font-medium">Pending</p>
                <p className="text-3xl font-bold text-yellow-900">{listStats.pending}</p>
              </div>
              <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                <p className="text-sm text-green-700 font-medium">Approved</p>
                <p className="text-3xl font-bold text-green-900">{listStats.approved}</p>
              </div>
              <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                <p className="text-sm text-red-700 font-medium">Rejected</p>
                <p className="text-3xl font-bold text-red-900">{listStats.rejected}</p>
              </div>
              <div className="bg-gray-100 p-4 rounded-lg border border-gray-300">
                <p className="text-sm text-gray-600 font-medium">Dismissed</p>
                <p className="text-3xl font-bold text-gray-700">{listStats.dismissed}</p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                <p className="text-sm text-gray-700 font-medium">Total</p>
                <p className="text-3xl font-bold text-gray-900">{listStats.total}</p>
              </div>
            </div>
          )}

          {/* Flags List */}
          {listLoading ? (
            <div className="text-center py-8 text-gray-500">Loading...</div>
          ) : listFlags.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-8 text-center">
              <div className="text-4xl mb-3">{'\u2705'}</div>
              <p className="text-gray-700 text-lg font-medium">All caught up</p>
              <p className="text-gray-500 mt-1">Every flag has been reviewed. Check back after the next scraper run.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {listFlags.map(flag => (
                <FlagCard
                  key={flag.id}
                  flag={flag}
                  onApprove={handleListApprove}
                  onReject={handleListReject}
                  onDismiss={handleListDismiss}
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
