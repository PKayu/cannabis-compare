'use client'

import React, { useEffect, useState, useCallback } from 'react'
import { api } from '@/lib/api'
import { useDebounce } from '@/lib/useDebounce'
import { FlagCard } from './components/FlagCard'
import { DuplicatePairCard } from './components/DuplicatePairCard'
import { FilterTabs, FilterTab, TAB_FILTERS } from './components/FilterTabs'
import { AdvancedFilters } from './components/AdvancedFilters'
import { BulkActions } from './components/BulkActions'
import { ScraperFlag, FlagStats, EditableFields } from './hooks/useCleanupSession'

const PAGE_SIZE = 50

/** Stable name-based key matching the legacy quality-page localStorage format */
function pairNameKey(a: string, b: string): string {
  return [a, b].map(n => n.toLowerCase().trim()).sort().join('::')
}

export default function CleanupQueuePage() {
  // List view state
  const [listFlags, setListFlags] = useState<ScraperFlag[]>([])
  const [listStats, setListStats] = useState<FlagStats | null>(null)
  const [listLoading, setListLoading] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [hasMore, setHasMore] = useState(false)
  const [listError, setListError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  // Filter and bulk action state
  const [activeTab, setActiveTab] = useState<FilterTab>('data_cleanup')
  const [advancedFilters, setAdvancedFilters] = useState<any>({
    sort_by: 'created_at',
    sort_order: 'desc'
  })
  const debouncedFilters = useDebounce(advancedFilters, 400)
  const [selectedFlagIds, setSelectedFlagIds] = useState<string[]>([])

  // Duplicates tab state
  const [duplicateWinners, setDuplicateWinners] = useState<Record<string, string>>({})
  const [scanRunning, setScanRunning] = useState(false)
  const [pairLoading, setPairLoading] = useState<string | null>(null)

  // Tab counts derived from the single stats fetch in loadListData
  const tabCounts = {
    data_cleanup: listStats?.pending_cleanup || 0,
    duplicates: listStats?.pending_duplicates || 0,
    legacy_review: listStats?.pending_review || 0,
    auto_linked: listStats?.auto_merged || 0,
    all: (listStats?.pending || 0) + (listStats?.auto_merged || 0),
  }

  const loadListData = useCallback(async (append = false) => {
    if (append) {
      setLoadingMore(true)
    } else {
      setListLoading(true)
      setSelectedFlagIds([]) // Clear selection when filters change
    }
    try {
      const tabFilters = TAB_FILTERS[activeTab]
      const params = {
        ...tabFilters,
        ...debouncedFilters,
        limit: PAGE_SIZE,
        skip: append ? listFlags.length : 0,
      }

      const [flagsRes, statsRes] = await Promise.all([
        api.admin.flags.pending(params),
        api.admin.flags.stats(),
      ])
      // For auto_linked tab, include_auto_merged adds them to pending results —
      // filter client-side so only true auto_merged flags appear in this tab.
      const flags = activeTab === 'auto_linked'
        ? (flagsRes.data || []).filter((f: any) => f.status === 'auto_merged')
        : (flagsRes.data || [])
      setListFlags(prev => append ? [...prev, ...flags] : flags)
      setHasMore((flagsRes.data || []).length === PAGE_SIZE)
      setListStats(statsRes.data)
      setListError(null)
    } catch (err) {
      console.error('Failed to load flags:', err)
      setListError('Failed to load pending flags')
    } finally {
      setListLoading(false)
      setLoadingMore(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, debouncedFilters, listFlags.length])

  // Load list data on mount and when tab or (debounced) filters change
  useEffect(() => {
    loadListData(false)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, debouncedFilters])

  const loadListStats = async () => {
    try {
      const res = await api.admin.flags.stats()
      setListStats(res.data)
    } catch {}
  }

  /** Optimistically remove flags from the list and refresh stats only */
  const removeFlags = (flagIds: string[]) => {
    setListFlags(prev => prev.filter(f => !flagIds.includes(f.id)))
    setSelectedFlagIds(prev => prev.filter(id => !flagIds.includes(id)))
    loadListStats()
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
      removeFlags([flagId])
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
      removeFlags([flagId])
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
      removeFlags([flagId])
    } catch (err) {
      console.error('Failed to dismiss:', err)
      setListError('Failed to dismiss flag')
    }
  }

  const handleMergeDuplicate = async (flagId: string, keptProductId: string, notes?: string) => {
    try {
      await api.admin.flags.mergeDuplicate(flagId, { kept_product_id: keptProductId, notes })
      removeFlags([flagId])
    } catch (err) {
      console.error('Failed to merge duplicate:', err)
      setListError('Failed to merge duplicate')
    }
  }

  // --- Data cleanup handlers ---

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
      removeFlags([flagId])
    } catch (err) {
      console.error('Failed to clean and activate:', err)
      setListError('Failed to clean and activate product')
    }
  }

  const handleDeleteProduct = async (flagId: string, notes?: string) => {
    try {
      await api.admin.flags.deleteProduct(flagId, { notes: notes || '' })
      removeFlags([flagId])
    } catch (err) {
      console.error('Failed to delete product:', err)
      setListError('Failed to delete product')
    }
  }

  // --- Auto-linked handlers ---

  const handleRejectAutoMerge = async (flagId: string, notes?: string) => {
    try {
      await api.admin.flags.rejectAutoMerge(flagId, { notes: notes || '' })
      removeFlags([flagId])
    } catch (err) {
      console.error('Failed to reject auto-merge:', err)
      setListError('Failed to reject auto-merge')
    }
  }

  // --- Duplicates tab handlers ---

  const handleDuplicateScan = async () => {
    setScanRunning(true)
    setListError(null)
    setNotice(null)
    try {
      const res = await api.admin.quality.duplicateScan()
      const { created, skipped_existing } = res.data || {}
      setNotice(
        `Scan complete: ${created ?? 0} new pair${created === 1 ? '' : 's'} found` +
        (skipped_existing ? `, ${skipped_existing} already tracked` : '')
      )
      await loadListData(false)
      await migrateLegacyDismissals()
    } catch (err: any) {
      console.error('Duplicate scan failed:', err)
      setListError(err?.response?.data?.detail || 'Duplicate scan failed')
    } finally {
      setScanRunning(false)
    }
  }

  /**
   * One-time migration of "keep separate" decisions from the old quality-page
   * localStorage store: bulk-dismiss pending pair flags whose name key matches,
   * then drop the localStorage key.
   */
  const migrateLegacyDismissals = async () => {
    let savedKeys: string[] = []
    try {
      savedKeys = JSON.parse(localStorage.getItem('dismissed_duplicate_pairs_v2') || '[]')
    } catch { return }
    if (savedKeys.length === 0) return

    try {
      const res = await api.admin.flags.pending({ flag_type: 'duplicate_pair', limit: 100 })
      const keySet = new Set(savedKeys)
      const toDismiss = (res.data || [])
        .filter((f: ScraperFlag) =>
          f.duplicate_pair?.product_a && f.duplicate_pair?.product_b &&
          keySet.has(pairNameKey(f.duplicate_pair.product_a.name, f.duplicate_pair.product_b.name))
        )
        .map((f: ScraperFlag) => f.id)
      if (toDismiss.length > 0) {
        await api.admin.flags.bulkAction({
          flag_ids: toDismiss,
          action: 'dismiss',
          admin_notes: 'Migrated "keep separate" decision from legacy quality page',
        })
        removeFlags(toDismiss)
        setNotice(prev => `${prev || ''} (${toDismiss.length} previously-dismissed pairs carried over)`)
      }
      localStorage.removeItem('dismissed_duplicate_pairs_v2')
    } catch (err) {
      console.error('Legacy dismissal migration failed:', err)
    }
  }

  const handlePickWinner = (flagId: string, productId: string) => {
    setDuplicateWinners(prev => ({ ...prev, [flagId]: productId }))
  }

  const handleMergePair = async (flag: ScraperFlag, winnerId: string) => {
    const loserId = winnerId === flag.matched_product_id
      ? flag.secondary_product_id
      : flag.matched_product_id
    if (!loserId) return
    setPairLoading(flag.id)
    try {
      const res = await api.admin.quality.mergeBatch([
        { winner_id: winnerId, loser_id: loserId, flag_id: flag.id },
      ])
      const result = res.data?.results?.[0]
      if (result && !result.ok) {
        setListError(`Merge failed: ${result.error}`)
      } else {
        removeFlags([flag.id])
      }
    } catch (err: any) {
      console.error('Merge failed:', err)
      setListError(err?.response?.data?.detail || 'Merge failed')
    } finally {
      setPairLoading(null)
    }
  }

  const handleDismissPair = async (flagId: string) => {
    setPairLoading(flagId)
    try {
      await api.admin.flags.dismiss(flagId, { notes: 'Not duplicates' })
      removeFlags([flagId])
    } catch (err) {
      console.error('Failed to dismiss pair:', err)
      setListError('Failed to dismiss pair')
    } finally {
      setPairLoading(null)
    }
  }

  const selectedWithWinners = selectedFlagIds.filter(id => duplicateWinners[id])
  const bulkMergeReady = selectedFlagIds.length > 0 &&
    selectedWithWinners.length === selectedFlagIds.length

  const handleBulkMergeDuplicates = async () => {
    const merges = selectedFlagIds
      .map(flagId => {
        const flag = listFlags.find(f => f.id === flagId)
        const winnerId = duplicateWinners[flagId]
        if (!flag || !winnerId) return null
        const loserId = winnerId === flag.matched_product_id
          ? flag.secondary_product_id
          : flag.matched_product_id
        if (!loserId) return null
        return { winner_id: winnerId, loser_id: loserId, flag_id: flagId }
      })
      .filter(Boolean) as { winner_id: string; loser_id: string; flag_id: string }[]

    if (merges.length === 0) return
    try {
      const res = await api.admin.quality.mergeBatch(merges)
      const results = res.data?.results || []
      const succeededFlagIds = merges
        .filter((_, i) => results[i]?.ok)
        .map(m => m.flag_id)
      const failed = results.filter((r: any) => !r.ok)
      removeFlags(succeededFlagIds)
      if (failed.length > 0) {
        setListError(
          `${failed.length} of ${merges.length} merges failed: ` +
          failed.map((f: any) => f.error).join('; ')
        )
      } else {
        setNotice(`Merged ${merges.length} pair${merges.length === 1 ? '' : 's'}`)
      }
    } catch (err: any) {
      console.error('Bulk merge failed:', err)
      setListError(err?.response?.data?.detail || 'Bulk merge failed')
    }
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

  // Bulk action handlers — optimistic removal + stats refresh, no full reload
  const runBulkAction = async (
    action: 'approve' | 'reject' | 'dismiss' | 'clean' | 'delete_product',
    errorMessage: string
  ) => {
    const ids = [...selectedFlagIds]
    try {
      const res = await api.admin.flags.bulkAction({ flag_ids: ids, action })
      const failures: { flag_id: string }[] = res.data?.errors || []
      const failedIds = new Set(failures.map(f => f.flag_id))
      removeFlags(ids.filter(id => !failedIds.has(id)))
      if (failures.length > 0) {
        setListError(`${failures.length} of ${ids.length} flags failed — they remain in the list`)
      }
    } catch (err) {
      console.error(`Bulk ${action} failed:`, err)
      setListError(errorMessage)
    }
  }

  const handleBulkApprove = () => runBulkAction('approve', 'Bulk approve operation failed')
  const handleBulkReject = () => runBulkAction('reject', 'Bulk reject operation failed')
  const handleBulkDismiss = () => runBulkAction('dismiss', 'Bulk dismiss operation failed')
  const handleBulkClean = () => runBulkAction('clean', 'Bulk activate operation failed')
  const handleBulkDelete = () => runBulkAction('delete_product', 'Bulk delete operation failed')

  return (
    <div>
      {/* Header */}
      <div className="mb-6 flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Dedup &amp; Review</h2>
          <p className="text-gray-600 text-sm mt-1">
            Review dirty imports, merge duplicate products, and spot-check auto-links.
          </p>
        </div>
        {activeTab === 'duplicates' && (
          <button
            onClick={handleDuplicateScan}
            disabled={scanRunning}
            className="px-4 py-2 text-sm font-medium bg-cannabis-600 text-white rounded-lg hover:bg-cannabis-700 disabled:opacity-50"
            title="Pairwise fuzzy comparison across all products — takes 10–20 seconds"
          >
            {scanRunning ? 'Scanning…' : 'Scan for Duplicates'}
          </button>
        )}
      </div>

      {listError && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6 text-sm flex items-start justify-between gap-3">
          <span>{listError}</span>
          <button onClick={() => setListError(null)} className="text-red-400 hover:text-red-600 shrink-0">✕</button>
        </div>
      )}
      {notice && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded mb-6 text-sm flex items-start justify-between gap-3">
          <span>{notice}</span>
          <button onClick={() => setNotice(null)} className="text-green-400 hover:text-green-600 shrink-0">✕</button>
        </div>
      )}

      {/* Stats Cards */}
      {listStats && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 mb-6">
          <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
            <p className="text-sm text-orange-700 font-medium">Needs Cleanup</p>
            <p className="text-3xl font-bold text-orange-900">{listStats.pending_cleanup}</p>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
            <p className="text-sm text-purple-700 font-medium">Duplicates</p>
            <p className="text-3xl font-bold text-purple-900">{listStats.pending_duplicates}</p>
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

      {/* Advanced Filters — not useful for duplicate pairs (no dispensary/quality) */}
      {activeTab !== 'duplicates' && (
        <AdvancedFilters
          filters={advancedFilters}
          onChange={setAdvancedFilters}
        />
      )}

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
        onBulkMergeDuplicates={handleBulkMergeDuplicates}
        bulkMergeReady={bulkMergeReady}
        bulkMergePendingWinners={selectedFlagIds.length - selectedWithWinners.length}
      />

      {/* Flags List */}
      {listLoading ? (
        <div className="text-center py-8 text-gray-500">Loading...</div>
      ) : listFlags.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <div className="text-4xl mb-3">{'✅'}</div>
          <p className="text-gray-700 text-lg font-medium">All caught up</p>
          <p className="text-gray-500 mt-1">
            {activeTab === 'data_cleanup'
              ? 'No dirty-data flags to clean up. Nice!'
              : activeTab === 'duplicates'
              ? 'No duplicate pairs to review. Run a scan to check for new ones.'
              : activeTab === 'legacy_review'
              ? 'No legacy match-review flags remaining.'
              : activeTab === 'auto_linked'
              ? 'No auto-linked products to review. Check back after the next scraper run.'
              : 'Every flag has been reviewed. Check back after the next scraper run.'}
          </p>
        </div>
      ) : (
        <>
          <div className="space-y-4">
            {listFlags.map(flag => (
              flag.flag_type === 'duplicate_pair' ? (
                <DuplicatePairCard
                  key={flag.id}
                  flag={flag}
                  selected={selectedFlagIds.includes(flag.id)}
                  winnerId={duplicateWinners[flag.id] || null}
                  loading={pairLoading === flag.id}
                  onToggleSelect={handleToggleSelect}
                  onPickWinner={handlePickWinner}
                  onMerge={handleMergePair}
                  onDismiss={handleDismissPair}
                />
              ) : (
                <FlagCard
                  key={flag.id}
                  flag={flag}
                  selected={selectedFlagIds.includes(flag.id)}
                  tabMode={activeTab === 'duplicates' ? 'all' : activeTab}
                  onToggleSelect={handleToggleSelect}
                  onApprove={handleListApprove}
                  onReject={handleListReject}
                  onDismiss={handleListDismiss}
                  onMergeDuplicate={handleMergeDuplicate}
                  onCleanAndActivate={handleCleanAndActivate}
                  onDeleteProduct={handleDeleteProduct}
                  onRejectAutoMerge={handleRejectAutoMerge}
                />
              )
            ))}
          </div>

          {/* Load more */}
          {hasMore && (
            <div className="text-center mt-6">
              <button
                onClick={() => loadListData(true)}
                disabled={loadingMore}
                className="px-6 py-2 text-sm font-medium bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50"
              >
                {loadingMore ? 'Loading…' : `Load More (showing ${listFlags.length})`}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
