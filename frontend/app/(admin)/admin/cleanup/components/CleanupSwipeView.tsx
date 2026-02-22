'use client'

import React, { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { ScraperFlag, EditableFields } from '../hooks/useCleanupSession'
import { FlagCard } from './FlagCard'

export function CleanupSwipeView() {
  const [flags, setFlags] = useState<ScraperFlag[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadFlags()
  }, [])

  const loadFlags = async () => {
    setLoading(true)
    try {
      // Default to data_cleanup flags first, then fall back to all pending
      const response = await api.admin.flags.pending({ flag_type: 'data_cleanup', limit: 50 })
      let data = response.data
      if (!data || data.length === 0) {
        // No cleanup flags — load legacy review flags
        const fallback = await api.admin.flags.pending({ flag_type: 'match_review', limit: 50 })
        data = fallback.data
      }
      setFlags(data || [])
      setError(null)
    } catch (err) {
      console.error('Failed to load flags:', err)
      setError('Failed to load pending flags')
    } finally {
      setLoading(false)
    }
  }

  const moveToNext = () => {
    if (currentIndex < flags.length - 1) {
      setCurrentIndex(currentIndex + 1)
    } else {
      loadFlags()
      setCurrentIndex(0)
    }
  }

  const handleApprove = async (
    flagId: string,
    edits?: Partial<EditableFields>,
    notes?: string,
    issueTags?: string[],
    matchedEdits?: { name?: string; brand?: string }
  ) => {
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
      if (matchedEdits?.name) data.matched_product_name = matchedEdits.name
      if (matchedEdits?.brand) data.matched_product_brand = matchedEdits.brand
      await api.admin.flags.approve(flagId, data)
      moveToNext()
    } catch (err) {
      console.error('Failed to approve:', err)
      setError('Failed to approve flag')
    }
  }

  const handleReject = async (flagId: string, edits?: Partial<EditableFields>, notes?: string, issueTags?: string[]) => {
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
      moveToNext()
    } catch (err) {
      console.error('Failed to reject:', err)
      setError('Failed to reject flag')
    }
  }

  const handleDismiss = async (flagId: string, notes?: string, issueTags?: string[]) => {
    try {
      const data: Record<string, unknown> = { notes: notes || '' }
      if (issueTags && issueTags.length > 0) data.issue_tags = issueTags
      await api.admin.flags.dismiss(flagId, data)
      moveToNext()
    } catch (err) {
      console.error('Failed to dismiss:', err)
      setError('Failed to dismiss flag')
    }
  }

  const handleCleanAndActivate = async (flagId: string, edits: Partial<EditableFields>, notes?: string, issueTags?: string[]) => {
    try {
      const data: Record<string, unknown> = { notes: notes || '' }
      if (edits.name) data.name = edits.name
      if (edits.brand_name) data.brand_name = edits.brand_name
      if (edits.product_type) data.product_type = edits.product_type
      if (edits.thc_percentage) data.thc_percentage = edits.thc_percentage
      if (edits.cbd_percentage) data.cbd_percentage = edits.cbd_percentage
      if (edits.weight) data.weight = edits.weight
      if (edits.price) data.price = edits.price
      if (issueTags && issueTags.length > 0) data.issue_tags = issueTags
      await api.admin.flags.clean(flagId, data)
      moveToNext()
    } catch (err) {
      console.error('Failed to clean and activate:', err)
      setError('Failed to clean and activate product')
    }
  }

  const handleDeleteProduct = async (flagId: string, notes?: string) => {
    try {
      await api.admin.flags.deleteProduct(flagId, { notes: notes || '' })
      moveToNext()
    } catch (err) {
      console.error('Failed to delete product:', err)
      setError('Failed to delete product')
    }
  }

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-500">Loading flags...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm">
        {error}
      </div>
    )
  }

  if (flags.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center">
        <div className="text-4xl mb-3">{'\u2705'}</div>
        <p className="text-gray-700 text-lg font-medium">All caught up</p>
        <p className="text-gray-500 mt-1">
          Every flag has been reviewed. Check back after the next scraper run.
        </p>
      </div>
    )
  }

  const currentFlag = flags[currentIndex]
  const isDataCleanup = currentFlag?.flag_type === 'data_cleanup'

  return (
    <div>
      {/* Progress Indicator */}
      <div className="mb-6">
        <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
          <span>
            Flag {currentIndex + 1} of {flags.length}
          </span>
          <span>{Math.round(((currentIndex + 1) / flags.length) * 100)}% complete</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-cannabis-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${((currentIndex + 1) / flags.length) * 100}%` }}
          />
        </div>
      </div>

      {/* Current Flag Card */}
      {currentFlag && (
        <FlagCard
          flag={currentFlag}
          tabMode={isDataCleanup ? 'data_cleanup' : 'legacy_review'}
          onApprove={handleApprove}
          onReject={handleReject}
          onDismiss={handleDismiss}
          onCleanAndActivate={handleCleanAndActivate}
          onDeleteProduct={handleDeleteProduct}
        />
      )}

      {/* Navigation Hints */}
      <div className="mt-4 text-center text-sm text-gray-500">
        <p>
          {isDataCleanup
            ? 'Edit the product data and Save & Activate, or Delete if garbage'
            : 'Review the product data and choose an action above'}
        </p>
      </div>
    </div>
  )
}
