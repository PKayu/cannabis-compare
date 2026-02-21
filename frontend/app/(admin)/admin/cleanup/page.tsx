'use client'

import React, { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { CleanupSwipeView } from './components/CleanupSwipeView'
import { FlagCard } from './components/FlagCard'
import { FilterTabs, FilterTab, TAB_FILTERS } from './components/FilterTabs'
import { AdvancedFilters } from './components/AdvancedFilters'
import { BulkActions } from './components/BulkActions'
import { ScraperFlag, FlagStats, EditableFields } from './hooks/useCleanupSession'

type ViewMode = 'swipe' | 'list'

export default function CleanupQueuePage() {
  const [viewMode, setViewMode] = useState<ViewMode>('swipe')

  // List view state (only loaded when in list mode)
  const [listFlags, setListFlags] = useState<ScraperFlag[]>([])
  const [listStats, setListStats] = useState<FlagStats | null>(null)
  const [listLoading, setListLoading] = useState(false)
  const [listError, setListError] = useState<string | null>(null)

  // NEW: Filter and bulk action state
  const [activeTab, setActiveTab] = useState<FilterTab>('priority')
  const [advancedFilters, setAdvancedFilters] = useState<any>({
    sort_by: 'created_at',
    sort_order: 'desc'
  })
  const [selectedFlagIds, setSelectedFlagIds] = useState<string[]>([])
  const [tabCounts, setTabCounts] = useState({
    priority: 0,
    cleanup: 0,
    duplicates: 0,
    auto_linked: 0,
    all: 0
  })

  // Load list data when switching to list view or filters change
  useEffect(() => {
    if (viewMode === 'list') {
      loadListData()
      loadTabCounts()
    }
  }, [viewMode, activeTab, advancedFilters])

  const loadListData = async () => {
    setListLoading(true)
    setSelectedFlagIds([]) // Clear selection when filters change
    try {
      const tabFilters = TAB_FILTERS[activeTab]
      const params = {
        ...tabFilters,
        ...advancedFilters,
        limit: 50
      }

      const [flagsRes, statsRes] = await Promise.all([
        api.admin.flags.pending(params),
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

  const loadTabCounts = async () => {
    try {
      // Fetch counts for each tab in parallel (using large limit to get accurate counts)
      const [priorityRes, cleanupRes, duplicatesRes, autoLinkedRes, allRes] = await Promise.all([
        api.admin.flags.pending({ match_type: 'cross_dispensary', limit: 1000 }),
        api.admin.flags.pending({ data_quality: 'poor,fair', limit: 1000 }),
        api.admin.flags.pending({ match_type: 'same_dispensary', limit: 1000 }),
        api.admin.flags.pending({ include_auto_merged: true, limit: 1000 }),
        api.admin.flags.pending({ limit: 1000 })
      ])

      setTabCounts({
        priority: priorityRes.data?.length || 0,
        cleanup: cleanupRes.data?.length || 0,
        duplicates: duplicatesRes.data?.length || 0,
        auto_linked: autoLinkedRes.data?.filter((f: any) => f.status === 'auto_merged').length || 0,
        all: allRes.data?.length || 0
      })
    } catch (err) {
      console.error('Failed to load tab counts:', err)
    }
  }

  const handleListApprove = async (
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

  const handleMergeDuplicate = async (flagId: string, keptProductId: string, notes?: string) => {
    try {
      await api.admin.flags.mergeDuplicate(flagId, { kept_product_id: keptProductId, notes })
      setListFlags(prev => prev.filter(f => f.id !== flagId))
      loadListStats()
    } catch (err) {
      console.error('Failed to merge duplicate:', err)
      setListError('Failed to merge duplicate')
    }
  }

  const loadListStats = async () => {
    try {
      const res = await api.admin.flags.stats()
      setListStats(res.data)
    } catch {}
  }

  // NEW: Bulk selection handlers
  const handleToggleSelect = (flagId: string) => {
    setSelectedFlagIds(prev =>
      prev.includes(flagId)
        ? prev.filter(id => id !== flagId)
        : [...prev, flagId]
    )
  }

  const handleSelectAll = () => {
    setSelectedFlagIds(listFlags.map(f => f.id))
  }

  const handleDeselectAll = () => {
    setSelectedFlagIds([])
  }

  // NEW: Bulk action handlers
  const handleBulkApprove = async () => {
    try {
      await api.admin.flags.bulkAction({
        flag_ids: selectedFlagIds,
        action: 'approve'
      })
      setSelectedFlagIds([])
      loadListData()
      loadListStats()
    } catch (err) {
      console.error('Bulk approve failed:', err)
      setListError('Bulk approve operation failed')
    }
  }

  const handleBulkReject = async () => {
    try {
      await api.admin.flags.bulkAction({
        flag_ids: selectedFlagIds,
        action: 'reject'
      })
      setSelectedFlagIds([])
      loadListData()
      loadListStats()
    } catch (err) {
      console.error('Bulk reject failed:', err)
      setListError('Bulk reject operation failed')
    }
  }

  const handleBulkDismiss = async () => {
    try {
      await api.admin.flags.bulkAction({
        flag_ids: selectedFlagIds,
        action: 'dismiss'
      })
      setSelectedFlagIds([])
      loadListData()
      loadListStats()
    } catch (err) {
      console.error('Bulk dismiss failed:', err)
      setListError('Bulk dismiss operation failed')
    }
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
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
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

          {/* Filter Tabs */}
          <FilterTabs
            activeTab={activeTab}
            counts={tabCounts}
            onTabChange={setActiveTab}
          />

          {/* Advanced Filters */}
          <AdvancedFilters
            filters={advancedFilters}
            onChange={setAdvancedFilters}
          />

          {/* Bulk Actions Toolbar */}
          <BulkActions
            selectedFlagIds={selectedFlagIds}
            totalFlags={listFlags.length}
            onSelectAll={handleSelectAll}
            onDeselectAll={handleDeselectAll}
            onBulkApprove={handleBulkApprove}
            onBulkReject={handleBulkReject}
            onBulkDismiss={handleBulkDismiss}
          />

          {/* Flags List */}
          {listLoading ? (
            <div className="text-center py-8 text-gray-500">Loading...</div>
          ) : listFlags.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-8 text-center">
              <div className="text-4xl mb-3">{'\u2705'}</div>
              <p className="text-gray-700 text-lg font-medium">All caught up</p>
              <p className="text-gray-500 mt-1">
                {activeTab === 'priority'
                  ? 'No cross-dispensary matches to link. Try the other tabs.'
                  : activeTab === 'cleanup'
                  ? 'No dirty-data flags found. Great job!'
                  : activeTab === 'duplicates'
                  ? 'No same-dispensary duplicates found.'
                  : activeTab === 'auto_linked'
                  ? 'No auto-linked products to review. Check back after the next scraper run.'
                  : 'Every flag has been reviewed. Check back after the next scraper run.'}
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {listFlags.map(flag => (
                <FlagCard
                  key={flag.id}
                  flag={flag}
                  selected={selectedFlagIds.includes(flag.id)}
                  tabMode={activeTab}
                  onToggleSelect={handleToggleSelect}
                  onApprove={handleListApprove}
                  onReject={handleListReject}
                  onDismiss={handleListDismiss}
                  onMergeDuplicate={handleMergeDuplicate}
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
