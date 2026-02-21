'use client'

import React, { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { FlagCard } from './components/FlagCard'
import { FilterTabs, FilterTab, TAB_FILTERS } from './components/FilterTabs'
import { AdvancedFilters } from './components/AdvancedFilters'
import { BulkActions } from './components/BulkActions'
import { ScraperFlag, FlagStats, EditableFields } from './hooks/useCleanupSession'

export default function CleanupQueuePage() {
  // List view state
  const [listFlags, setListFlags] = useState<ScraperFlag[]>([])
  const [listStats, setListStats] = useState<FlagStats | null>(null)
  const [listLoading, setListLoading] = useState(false)
  const [listError, setListError] = useState<string | null>(null)

  // Filter and bulk action state
  const [activeTab, setActiveTab] = useState<FilterTab>('data_cleanup')
  const [advancedFilters, setAdvancedFilters] = useState<any>({
    sort_by: 'created_at',
    sort_order: 'desc'
  })
  const [selectedFlagIds, setSelectedFlagIds] = useState<string[]>([])
  const [tabCounts, setTabCounts] = useState({
    data_cleanup: 0,
    legacy_review: 0,
    auto_linked: 0,
    all: 0
  })

  // Load list data on mount and when filters change
  useEffect(() => {
    loadListData()
    loadTabCounts()
  }, [activeTab, advancedFilters])

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
      // For auto_linked tab, include_auto_merged adds them to pending results —
      // filter client-side so only true auto_merged flags appear in this tab.
      const flags = activeTab === 'auto_linked'
        ? (flagsRes.data || []).filter((f: any) => f.status === 'auto_merged')
        : flagsRes.data
      setListFlags(flags)
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
      const [cleanupRes, legacyRes, autoLinkedRes, allRes] = await Promise.all([
        api.admin.flags.pending({ flag_type: 'data_cleanup', limit: 1000 }),
        api.admin.flags.pending({ flag_type: 'match_review', limit: 1000 }),
        api.admin.flags.pending({ include_auto_merged: true, limit: 1000 }),
        api.admin.flags.pending({ limit: 1000 })
      ])

      setTabCounts({
        data_cleanup: cleanupRes.data?.length || 0,
        legacy_review: legacyRes.data?.length || 0,
        auto_linked: autoLinkedRes.data?.filter((f: any) => f.status === 'auto_merged').length || 0,
        all: allRes.data?.length || 0
      })
    } catch (err) {
      console.error('Failed to load tab counts:', err)
    }
  }

  // --- Legacy match_review handlers ---

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

  // --- New data_cleanup handlers ---

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
      setListFlags(prev => prev.filter(f => f.id !== flagId))
      loadListStats()
    } catch (err) {
      console.error('Failed to clean and activate:', err)
      setListError('Failed to clean and activate product')
    }
  }

  const handleDeleteProduct = async (flagId: string, notes?: string) => {
    try {
      await api.admin.flags.deleteProduct(flagId, { notes: notes || '' })
      setListFlags(prev => prev.filter(f => f.id !== flagId))
      loadListStats()
    } catch (err) {
      console.error('Failed to delete product:', err)
      setListError('Failed to delete product')
    }
  }

  // --- Auto-linked handlers ---

  const handleRejectAutoMerge = async (flagId: string, notes?: string) => {
    try {
      await api.admin.flags.rejectAutoMerge(flagId, { notes: notes || '' })
      setListFlags(prev => prev.filter(f => f.id !== flagId))
      loadListStats()
    } catch (err) {
      console.error('Failed to reject auto-merge:', err)
      setListError('Failed to reject auto-merge')
    }
  }

  const loadListStats = async () => {
    try {
      const res = await api.admin.flags.stats()
      setListStats(res.data)
    } catch {}
  }

  // Bulk selection handlers
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

  // Bulk action handlers
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

  const handleBulkClean = async () => {
    try {
      await api.admin.flags.bulkAction({
        flag_ids: selectedFlagIds,
        action: 'clean'
      })
      setSelectedFlagIds([])
      loadListData()
      loadListStats()
    } catch (err) {
      console.error('Bulk clean failed:', err)
      setListError('Bulk activate operation failed')
    }
  }

  const handleBulkDelete = async () => {
    try {
      await api.admin.flags.bulkAction({
        flag_ids: selectedFlagIds,
        action: 'delete_product'
      })
      setSelectedFlagIds([])
      loadListData()
      loadListStats()
    } catch (err) {
      console.error('Bulk delete failed:', err)
      setListError('Bulk delete operation failed')
    }
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Cleanup Queue</h2>
        <p className="text-gray-600 text-sm mt-1">
          Review dirty product data and activate or delete flagged imports.
        </p>
      </div>

      {listError && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6 text-sm">
          {listError}
        </div>
      )}

      {/* Stats Cards */}
      {listStats && (
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-6">
          <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
            <p className="text-sm text-orange-700 font-medium">Needs Cleanup</p>
            <p className="text-3xl font-bold text-orange-900">{listStats.pending_cleanup}</p>
          </div>
          <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
            <p className="text-sm text-yellow-700 font-medium">Legacy Review</p>
            <p className="text-3xl font-bold text-yellow-900">{listStats.pending_review}</p>
          </div>
          <div className="bg-green-50 p-4 rounded-lg border border-green-200">
            <p className="text-sm text-green-700 font-medium">Cleaned</p>
            <p className="text-3xl font-bold text-green-900">{listStats.cleaned}</p>
          </div>
          <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
            <p className="text-sm text-blue-700 font-medium">Approved</p>
            <p className="text-3xl font-bold text-blue-900">{listStats.approved}</p>
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
        activeTab={activeTab}
        onSelectAll={handleSelectAll}
        onDeselectAll={handleDeselectAll}
        onBulkApprove={handleBulkApprove}
        onBulkReject={handleBulkReject}
        onBulkDismiss={handleBulkDismiss}
        onBulkClean={handleBulkClean}
        onBulkDelete={handleBulkDelete}
      />

      {/* Flags List */}
      {listLoading ? (
        <div className="text-center py-8 text-gray-500">Loading...</div>
      ) : listFlags.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <div className="text-4xl mb-3">{'\u2705'}</div>
          <p className="text-gray-700 text-lg font-medium">All caught up</p>
          <p className="text-gray-500 mt-1">
            {activeTab === 'data_cleanup'
              ? 'No dirty-data flags to clean up. Nice!'
              : activeTab === 'legacy_review'
              ? 'No legacy match-review flags remaining.'
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
              onCleanAndActivate={handleCleanAndActivate}
              onDeleteProduct={handleDeleteProduct}
              onRejectAutoMerge={handleRejectAutoMerge}
            />
          ))}
        </div>
      )}
    </div>
  )
}
