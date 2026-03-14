'use client'

import React, { useEffect, useState } from 'react'
import Link from 'next/link'
import { api } from '@/lib/api'

interface QualityMetrics {
  total_master_products: number
  missing_thc_count: number
  missing_thc_pct: number
  missing_cbd_count: number
  missing_cbd_pct: number
  missing_brand_count: number
  missing_brand_pct: number
  low_confidence_count: number
  category_distribution: Record<string, number>
}

interface DispensaryFreshness {
  dispensary_id: string
  dispensary_name: string
  last_successful_scrape: string | null
  hours_since_last_scrape: number | null
  status: string
}

interface Outlier {
  product_name: string
  dispensary_name: string
  price: number
  severity: string
  reason: string
}

interface CrossDispensaryProduct {
  id: string
  name: string
  product_type: string
  brand: string | null
  dispensary_count: number
  variant_count: number
  dispensaries: string[]
}

interface DispensaryCoverage {
  total_active: number
  orphans: number
  single_dispensary: number
  two_dispensaries: number
  three_dispensaries: number
  four_plus_dispensaries: number
  multi_dispensary: number
}

interface DispensaryDuplicateEntry {
  id: string
  name: string
  location: string
  product_count: number
}

interface DispensaryDuplicateGroup {
  canonical: DispensaryDuplicateEntry
  duplicates: DispensaryDuplicateEntry[]
}

interface PotentialDuplicatePair {
  product_a_id: string
  product_a_name: string
  product_a_brand: string
  product_a_dispensaries: string[]
  product_a_dispensary_urls: Record<string, string>
  product_b_id: string
  product_b_name: string
  product_b_brand: string
  product_b_dispensaries: string[]
  product_b_dispensary_urls: Record<string, string>
  product_type: string
  confidence: number
}

type Tab = 'health' | 'cross-dispensary'

export default function QualityPage() {
  const [activeTab, setActiveTab] = useState<Tab>('health')

  // Health tab state
  const [metrics, setMetrics] = useState<QualityMetrics | null>(null)
  const [freshness, setFreshness] = useState<DispensaryFreshness[]>([])
  const [outliers, setOutliers] = useState<Outlier[]>([])
  const [healthLoading, setHealthLoading] = useState(true)

  // Cross-dispensary tab state
  const [crossProducts, setCrossProducts] = useState<CrossDispensaryProduct[]>([])
  const [coverage, setCoverage] = useState<DispensaryCoverage | null>(null)
  const [crossLoading, setCrossLoading] = useState(false)
  const [crossLoaded, setCrossLoaded] = useState(false)
  const [sortBy, setSortBy] = useState<'dispensary_count' | 'name'>('dispensary_count')

  // Potential duplicates state
  const [dupPairs, setDupPairs] = useState<PotentialDuplicatePair[]>([])
  const [dupLoading, setDupLoading] = useState(false)
  const [dupLoaded, setDupLoaded] = useState(false)
  const [dupError, setDupError] = useState<string | null>(null)
  // v2 key: name-based so dismissals survive ID changes from merges/deduplication reordering
  const [dismissedPairs, setDismissedPairs] = useState<Set<string>>(() => {
    if (typeof window === 'undefined') return new Set()
    try {
      const saved = localStorage.getItem('dismissed_duplicate_pairs_v2')
      return new Set(saved ? JSON.parse(saved) : [])
    } catch { return new Set() }
  })
  const [merging, setMerging] = useState<string | null>(null)
  const [selectedPairs, setSelectedPairs] = useState<Set<string>>(new Set())
  const [bulkMerging, setBulkMerging] = useState(false)
  const [bulkProgress, setBulkProgress] = useState<{ done: number; total: number } | null>(null)
  const [repairing, setRepairing] = useState(false)
  const [repairResult, setRepairResult] = useState<string | null>(null)

  // Duplicate dispensary state
  const [dispDupGroups, setDispDupGroups] = useState<DispensaryDuplicateGroup[]>([])
  const [dispDupLoading, setDispDupLoading] = useState(false)
  const [dispDupLoaded, setDispDupLoaded] = useState(false)
  const [dispDupError, setDispDupError] = useState<string | null>(null)
  const [mergingDisp, setMergingDisp] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([
      api.get('/api/admin/scrapers/quality/metrics').catch(() => null),
      api.get('/api/admin/scrapers/dispensaries/freshness').catch(() => null),
      api.get('/api/admin/outliers?limit=20').catch(() => null),
    ]).then(([metricsRes, freshnessRes, outliersRes]) => {
      if (metricsRes) setMetrics(metricsRes.data)
      if (freshnessRes) setFreshness(freshnessRes.data)
      if (outliersRes) setOutliers(outliersRes.data?.outliers ?? [])
      setHealthLoading(false)
    })
  }, [])

  function fetchCrossData() {
    setCrossLoading(true)
    Promise.all([
      api.admin.quality.crossDispensaryProducts({ min_dispensaries: 2, limit: 500 }).catch(() => null),
      api.admin.quality.dispensaryCoverage().catch(() => null),
    ]).then(([crossRes, coverageRes]) => {
      if (crossRes) setCrossProducts(crossRes.data?.products ?? [])
      if (coverageRes) setCoverage(coverageRes.data)
      setCrossLoading(false)
      setCrossLoaded(true)
    })
  }

  function loadCrossDispensary() {
    if (crossLoaded) return
    fetchCrossData()
  }

  function handleTabChange(tab: Tab) {
    setActiveTab(tab)
    if (tab === 'cross-dispensary') loadCrossDispensary()
  }

  function loadPotentialDuplicates() {
    setDupLoading(true)
    setDupError(null)
    api.admin.quality.potentialDuplicates({ limit: 100 })
      .then((res) => {
        setDupPairs(res.data?.pairs ?? [])
        setDupLoaded(true)
      })
      .catch((err) => {
        setDupError(err?.response?.data?.detail ?? 'Failed to load potential duplicates.')
      })
      .finally(() => setDupLoading(false))
  }

  /** Stable dismiss key by sorted product names — survives ID changes across re-analyses */
  function getDismissKey(pair: PotentialDuplicatePair): string {
    return [pair.product_a_name, pair.product_b_name]
      .map(n => n.toLowerCase().trim())
      .sort()
      .join('::')
  }

  function dismissPair(dismissKeyOrPair: string | PotentialDuplicatePair) {
    const key = typeof dismissKeyOrPair === 'string' ? dismissKeyOrPair : getDismissKey(dismissKeyOrPair)
    const next = new Set(dismissedPairs)
    next.add(key)
    setDismissedPairs(next)
    try {
      localStorage.setItem('dismissed_duplicate_pairs_v2', JSON.stringify([...next]))
    } catch { /* ignore */ }
  }

  function clearDismissed() {
    setDismissedPairs(new Set())
    try { localStorage.removeItem('dismissed_duplicate_pairs_v2') } catch { /* ignore */ }
  }

  function togglePair(pairKey: string) {
    const next = new Set(selectedPairs)
    if (next.has(pairKey)) next.delete(pairKey); else next.add(pairKey)
    setSelectedPairs(next)
  }

  function toggleAll(visible: PotentialDuplicatePair[]) {
    const allKeys = visible.map(p => `${p.product_a_id}:${p.product_b_id}`)
    if (selectedPairs.size === visible.length && visible.length > 0) {
      setSelectedPairs(new Set())
    } else {
      setSelectedPairs(new Set(allKeys))
    }
  }

  async function mergePair(sourceId: string, targetId: string, pairKey: string, pair: PotentialDuplicatePair) {
    setMerging(pairKey)
    try {
      await api.admin.quality.mergeProducts(sourceId, targetId)
      dismissPair(pair)
      setSelectedPairs(prev => { const n = new Set(prev); n.delete(pairKey); return n })
      fetchCrossData()
    } catch (err: any) {
      alert(err?.response?.data?.detail ?? 'Merge failed.')
    } finally {
      setMerging(null)
    }
  }

  async function mergeSelected() {
    const keys = [...selectedPairs]
    setBulkMerging(true)
    setBulkProgress({ done: 0, total: keys.length })
    let anyMerged = false
    for (const key of keys) {
      const pair = dupPairs.find(p => `${p.product_a_id}:${p.product_b_id}` === key)
      if (!pair) continue
      try {
        await api.admin.quality.mergeProducts(pair.product_a_id, pair.product_b_id)
        dismissPair(pair)
        setSelectedPairs(prev => { const n = new Set(prev); n.delete(key); return n })
        anyMerged = true
      } catch { /* leave failed merges in list */ }
      setBulkProgress(prev => prev ? { ...prev, done: prev.done + 1 } : null)
    }
    setBulkMerging(false)
    setBulkProgress(null)
    if (anyMerged) fetchCrossData()
  }

  function dismissSelected() {
    for (const key of selectedPairs) {
      const pair = dupPairs.find(p => `${p.product_a_id}:${p.product_b_id}` === key)
      if (pair) dismissPair(pair)
    }
    setSelectedPairs(new Set())
  }

  async function runRepair() {
    setRepairing(true)
    setRepairResult(null)
    try {
      const res = await api.admin.quality.repairOrphanedVariants()
      const n = res.data?.repaired ?? 0
      setRepairResult(n > 0 ? `Repaired ${n} orphaned variant${n !== 1 ? 's' : ''} — list refreshed.` : 'No orphaned variants found.')
      fetchCrossData()
    } catch {
      setRepairResult('Repair failed — check server logs.')
    } finally {
      setRepairing(false)
    }
  }

  function loadDispensaryDuplicates() {
    setDispDupLoading(true)
    setDispDupError(null)
    api.admin.quality.dispensaryDuplicates()
      .then((res) => {
        setDispDupGroups(res.data?.groups ?? [])
        setDispDupLoaded(true)
      })
      .catch((err) => {
        setDispDupError(err?.response?.data?.detail ?? 'Failed to load duplicate dispensaries.')
      })
      .finally(() => setDispDupLoading(false))
  }

  async function mergeDispensaryGroup(group: DispensaryDuplicateGroup) {
    const key = group.canonical.id
    setMergingDisp(key)
    try {
      const sourceIds = group.duplicates.map((d) => d.id)
      await api.admin.quality.mergeDispensaries(sourceIds, group.canonical.id)
      // Refresh the list and cross-dispensary data
      loadDispensaryDuplicates()
      fetchCrossData()
    } catch (err: any) {
      alert(err?.response?.data?.detail ?? 'Dispensary merge failed.')
    } finally {
      setMergingDisp(null)
    }
  }

  const visibleDupPairs = dupPairs.filter(
    (p) => !dismissedPairs.has(getDismissKey(p))
  )

  const sortedProducts = [...crossProducts].sort((a, b) => {
    if (sortBy === 'dispensary_count') return b.dispensary_count - a.dispensary_count
    return a.name.localeCompare(b.name)
  })

  return (
    <div>
      {/* Tab Bar */}
      <div className="flex border-b border-gray-200 mb-6 gap-0">
        <TabButton
          active={activeTab === 'health'}
          onClick={() => handleTabChange('health')}
          label="Data Health"
        />
        <TabButton
          active={activeTab === 'cross-dispensary'}
          onClick={() => handleTabChange('cross-dispensary')}
          label="Cross-Dispensary Links"
        />
      </div>

      {/* Health Tab */}
      {activeTab === 'health' && (
        <div>
          {healthLoading ? (
            <div className="text-gray-500 py-12 text-center">Loading quality data...</div>
          ) : (
            <>
              {/* Data Completeness */}
              <h2 className="text-lg font-semibold text-gray-900 mb-3">Data Completeness</h2>
              {metrics && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                  <CompletenessCard
                    label="Missing THC%"
                    count={metrics.missing_thc_count}
                    pct={metrics.missing_thc_pct}
                    total={metrics.total_master_products}
                  />
                  <CompletenessCard
                    label="Missing CBD%"
                    count={metrics.missing_cbd_count}
                    pct={metrics.missing_cbd_pct}
                    total={metrics.total_master_products}
                  />
                  <CompletenessCard
                    label="Missing Brand"
                    count={metrics.missing_brand_count}
                    pct={metrics.missing_brand_pct}
                    total={metrics.total_master_products}
                  />
                  <div className="p-4 rounded-lg border bg-purple-50 border-purple-200">
                    <p className="text-sm font-medium text-purple-700">Low Confidence</p>
                    <p className="text-3xl font-bold text-purple-900 mt-1">{metrics.low_confidence_count}</p>
                    <p className="text-xs text-purple-600 mt-1">
                      of {metrics.total_master_products} products
                    </p>
                  </div>
                </div>
              )}

              {/* Category Distribution */}
              {metrics && Object.keys(metrics.category_distribution).length > 0 && (
                <div className="mb-8">
                  <h2 className="text-lg font-semibold text-gray-900 mb-3">Category Distribution</h2>
                  <div className="bg-white rounded-lg border p-4">
                    {Object.entries(metrics.category_distribution)
                      .sort(([, a], [, b]) => b - a)
                      .map(([category, count]) => {
                        const pct = metrics.total_master_products > 0
                          ? (count / metrics.total_master_products) * 100
                          : 0
                        return (
                          <div key={category} className="flex items-center gap-3 py-2">
                            <span className="w-24 text-sm font-medium text-gray-700">{category}</span>
                            <div className="flex-1 bg-gray-100 rounded-full h-5 overflow-hidden">
                              <div
                                className="bg-cannabis-500 h-full rounded-full"
                                style={{ width: `${pct}%` }}
                              />
                            </div>
                            <span className="text-sm text-gray-600 w-20 text-right">
                              {count} ({pct.toFixed(0)}%)
                            </span>
                          </div>
                        )
                      })}
                  </div>
                </div>
              )}

              {/* Dispensary Freshness */}
              <div className="mb-8">
                <h2 className="text-lg font-semibold text-gray-900 mb-3">Dispensary Data Freshness</h2>
                {freshness.length === 0 ? (
                  <div className="bg-white rounded-lg border p-6 text-center text-gray-500">
                    No dispensary data available.
                  </div>
                ) : (
                  <div className="bg-white rounded-lg border overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50 border-b">
                        <tr>
                          <th className="text-left px-4 py-2 font-medium text-gray-700">Dispensary</th>
                          <th className="text-left px-4 py-2 font-medium text-gray-700">Last Scrape</th>
                          <th className="text-left px-4 py-2 font-medium text-gray-700">Hours Ago</th>
                          <th className="text-left px-4 py-2 font-medium text-gray-700">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {freshness.map((d) => (
                          <tr key={d.dispensary_id} className="hover:bg-gray-50">
                            <td className="px-4 py-2 font-medium">{d.dispensary_name}</td>
                            <td className="px-4 py-2 text-gray-600">
                              {d.last_successful_scrape
                                ? new Date(d.last_successful_scrape).toLocaleString()
                                : 'Never'}
                            </td>
                            <td className="px-4 py-2 text-gray-600">
                              {d.hours_since_last_scrape != null
                                ? `${d.hours_since_last_scrape}h`
                                : '-'}
                            </td>
                            <td className="px-4 py-2">
                              <FreshnessBadge status={d.status} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Price Outliers */}
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-3">Price Outliers</h2>
                {outliers.length === 0 ? (
                  <div className="bg-white rounded-lg border p-6 text-center text-gray-500">
                    No price outliers detected.
                  </div>
                ) : (
                  <div className="bg-white rounded-lg border overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50 border-b">
                        <tr>
                          <th className="text-left px-4 py-2 font-medium text-gray-700">Product</th>
                          <th className="text-left px-4 py-2 font-medium text-gray-700">Dispensary</th>
                          <th className="text-left px-4 py-2 font-medium text-gray-700">Price</th>
                          <th className="text-left px-4 py-2 font-medium text-gray-700">Severity</th>
                          <th className="text-left px-4 py-2 font-medium text-gray-700">Reason</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {outliers.map((o, i) => (
                          <tr key={i} className="hover:bg-gray-50">
                            <td className="px-4 py-2 font-medium">{o.product_name}</td>
                            <td className="px-4 py-2 text-gray-600">{o.dispensary_name}</td>
                            <td className="px-4 py-2">${o.price?.toFixed(2)}</td>
                            <td className="px-4 py-2">
                              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                                o.severity === 'high'
                                  ? 'bg-red-100 text-red-800'
                                  : 'bg-yellow-100 text-yellow-800'
                              }`}>
                                {o.severity}
                              </span>
                            </td>
                            <td className="px-4 py-2 text-gray-600 text-xs">{o.reason}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      )}

      {/* Cross-Dispensary Tab */}
      {activeTab === 'cross-dispensary' && (
        <div>
          {crossLoading ? (
            <div className="text-gray-500 py-12 text-center">Loading cross-dispensary data...</div>
          ) : (
            <>
              {/* Data Repair */}
              <div className="mb-4 flex items-center gap-3">
                <button
                  onClick={runRepair}
                  disabled={repairing}
                  className="px-3 py-1.5 text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200 rounded-lg hover:bg-amber-100 disabled:opacity-50"
                  title="Re-parent variants that were orphaned by merges done before the fix was deployed"
                >
                  {repairing ? 'Repairing…' : '🔧 Repair Orphaned Variants'}
                </button>
                {repairResult && (
                  <span className="text-xs text-gray-500">{repairResult}</span>
                )}
              </div>

              {/* Coverage Summary Cards */}
              {coverage && (
                <div className="mb-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-3">Dispensary Coverage</h2>
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                    <CoverageCard
                      label="Orphans"
                      count={coverage.orphans}
                      total={coverage.total_active}
                      color="gray"
                      hint="No prices at any dispensary"
                    />
                    <CoverageCard
                      label="1 Dispensary"
                      count={coverage.single_dispensary}
                      total={coverage.total_active}
                      color="yellow"
                      hint="Unique to one dispensary"
                    />
                    <CoverageCard
                      label="2 Dispensaries"
                      count={coverage.two_dispensaries}
                      total={coverage.total_active}
                      color="blue"
                    />
                    <CoverageCard
                      label="3 Dispensaries"
                      count={coverage.three_dispensaries}
                      total={coverage.total_active}
                      color="green"
                    />
                    <CoverageCard
                      label="4+ Dispensaries"
                      count={coverage.four_plus_dispensaries}
                      total={coverage.total_active}
                      color="cannabis"
                    />
                  </div>
                  <p className="text-sm text-gray-500 mt-2">
                    <span className="font-medium text-gray-700">{coverage.multi_dispensary}</span> of{' '}
                    {coverage.total_active} active products are linked across 2+ dispensaries (
                    {coverage.total_active > 0
                      ? ((coverage.multi_dispensary / coverage.total_active) * 100).toFixed(1)
                      : 0}
                    %)
                  </p>
                </div>
              )}

              {/* Potential Duplicates */}
              <div className="mb-8">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900">Potential Duplicates</h2>
                    <p className="text-xs text-gray-500 mt-0.5">
                      Products with 65–84% name similarity within the same category that may have been imported separately.
                    </p>
                  </div>
                  {!dupLoaded && (
                    <button
                      onClick={loadPotentialDuplicates}
                      disabled={dupLoading}
                      className="px-4 py-2 text-sm font-medium bg-cannabis-600 text-white rounded-lg hover:bg-cannabis-700 disabled:opacity-50"
                    >
                      {dupLoading ? 'Analyzing…' : 'Run Analysis'}
                    </button>
                  )}
                  {dupLoaded && (
                    <button
                      onClick={loadPotentialDuplicates}
                      disabled={dupLoading}
                      className="px-3 py-1.5 text-xs font-medium bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 disabled:opacity-50"
                    >
                      {dupLoading ? 'Refreshing…' : 'Refresh'}
                    </button>
                  )}
                </div>

                {dupError && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
                    {dupError}
                  </div>
                )}

                {dupLoading && (
                  <div className="text-gray-500 py-8 text-center text-sm">
                    Running O(n²) fuzzy comparison across all products… this may take 10–20 seconds.
                  </div>
                )}

                {!dupLoading && !dupLoaded && !dupError && (
                  <div className="bg-gray-50 border border-dashed border-gray-200 rounded-lg p-8 text-center">
                    <p className="text-sm text-gray-500">
                      Click <strong>Run Analysis</strong> to compare all existing products for near-matches.
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                      Takes 10–20 seconds for ~1,000+ products.
                    </p>
                  </div>
                )}

                {dupLoaded && !dupLoading && (
                  visibleDupPairs.length === 0 ? (
                    <div className="bg-white rounded-lg border p-6 text-center text-gray-500 text-sm">
                      No potential duplicates found. Either products are distinct or all pairs have been dismissed.
                    </div>
                  ) : (
                    <div className="bg-white rounded-lg border overflow-x-auto">
                      {/* Toolbar: count + bulk actions */}
                      <div className="px-4 py-2 bg-gray-50 border-b flex items-center justify-between gap-3">
                        <div className="flex items-center gap-3">
                          <span className="text-xs text-gray-500">
                            Showing {visibleDupPairs.length} pair{visibleDupPairs.length !== 1 ? 's' : ''} in near-miss range (65–84% confidence)
                          </span>
                          {dismissedPairs.size > 0 && (
                            <button
                              onClick={clearDismissed}
                              className="text-xs text-gray-400 hover:text-gray-600 underline"
                              title="Show previously dismissed pairs again"
                            >
                              Clear dismissed ({dismissedPairs.size})
                            </button>
                          )}
                        </div>
                        {selectedPairs.size > 0 && (
                          <div className="flex items-center gap-2">
                            {bulkProgress && (
                              <span className="text-xs text-gray-500">
                                {bulkProgress.done}/{bulkProgress.total} merged…
                              </span>
                            )}
                            <button
                              onClick={mergeSelected}
                              disabled={bulkMerging}
                              className="px-3 py-1 text-xs font-medium bg-cannabis-600 text-white rounded hover:bg-cannabis-700 disabled:opacity-50"
                            >
                              {bulkMerging ? 'Merging…' : `Merge Selected (${selectedPairs.size})`}
                            </button>
                            <button
                              onClick={dismissSelected}
                              disabled={bulkMerging}
                              className="px-3 py-1 text-xs font-medium bg-gray-100 text-gray-600 rounded hover:bg-gray-200 disabled:opacity-50"
                            >
                              Dismiss Selected ({selectedPairs.size})
                            </button>
                          </div>
                        )}
                      </div>
                      <table className="w-full text-sm min-w-[750px]">
                        <thead className="bg-gray-50 border-b">
                          <tr>
                            <th className="px-3 py-2 w-8">
                              <input
                                type="checkbox"
                                className="rounded border-gray-300"
                                checked={selectedPairs.size === visibleDupPairs.length && visibleDupPairs.length > 0}
                                onChange={() => toggleAll(visibleDupPairs)}
                                title="Select all"
                              />
                            </th>
                            <th className="text-left px-4 py-2 font-medium text-gray-700">Product A</th>
                            <th className="text-center px-3 py-2 font-medium text-gray-700 whitespace-nowrap">Confidence</th>
                            <th className="text-left px-4 py-2 font-medium text-gray-700">Product B</th>
                            <th className="text-left px-3 py-2 font-medium text-gray-700">Type</th>
                            <th className="text-right px-4 py-2 font-medium text-gray-700">Actions</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y">
                          {visibleDupPairs.map((p) => {
                            const pairKey = `${p.product_a_id}:${p.product_b_id}`
                            const isMerging = merging === pairKey
                            const isSelected = selectedPairs.has(pairKey)
                            const pct = Math.round(p.confidence * 100)
                            return (
                              <tr key={pairKey} className={`hover:bg-gray-50 ${isSelected ? 'bg-cannabis-50' : ''}`}>
                                <td className="px-3 py-3">
                                  <input
                                    type="checkbox"
                                    className="rounded border-gray-300"
                                    checked={isSelected}
                                    onChange={() => togglePair(pairKey)}
                                  />
                                </td>
                                <td className="px-4 py-3">
                                  <Link
                                    href={`/products/${p.product_a_id}`}
                                    className="font-medium text-cannabis-700 hover:underline block"
                                  >
                                    {p.product_a_name}
                                  </Link>
                                  <span className="text-xs text-gray-400">{p.product_a_brand || '—'}</span>
                                  {p.product_a_dispensaries.length > 0 && (
                                    <div className="flex flex-wrap gap-1 mt-1">
                                      {p.product_a_dispensaries.map((d) => {
                                        const url = p.product_a_dispensary_urls?.[d]
                                        return url ? (
                                          <a
                                            key={d}
                                            href={url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="px-1.5 py-0.5 bg-blue-50 text-blue-600 rounded text-xs hover:bg-blue-100 hover:underline"
                                            title={`Open on ${d} website`}
                                          >{d} ↗</a>
                                        ) : (
                                          <span key={d} className="px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded text-xs">{d}</span>
                                        )
                                      })}
                                    </div>
                                  )}
                                </td>
                                <td className="px-3 py-3 text-center">
                                  <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                                    pct >= 80 ? 'bg-orange-100 text-orange-800' :
                                    pct >= 70 ? 'bg-yellow-100 text-yellow-800' :
                                    'bg-gray-100 text-gray-600'
                                  }`}>
                                    {pct}%
                                  </span>
                                </td>
                                <td className="px-4 py-3">
                                  <Link
                                    href={`/products/${p.product_b_id}`}
                                    className="font-medium text-cannabis-700 hover:underline block"
                                  >
                                    {p.product_b_name}
                                  </Link>
                                  <span className="text-xs text-gray-400">{p.product_b_brand || '—'}</span>
                                  {p.product_b_dispensaries.length > 0 && (
                                    <div className="flex flex-wrap gap-1 mt-1">
                                      {p.product_b_dispensaries.map((d) => {
                                        const url = p.product_b_dispensary_urls?.[d]
                                        return url ? (
                                          <a
                                            key={d}
                                            href={url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="px-1.5 py-0.5 bg-blue-50 text-blue-600 rounded text-xs hover:bg-blue-100 hover:underline"
                                            title={`Open on ${d} website`}
                                          >{d} ↗</a>
                                        ) : (
                                          <span key={d} className="px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded text-xs">{d}</span>
                                        )
                                      })}
                                    </div>
                                  )}
                                </td>
                                <td className="px-3 py-3 text-gray-500 text-xs capitalize">{p.product_type}</td>
                                <td className="px-4 py-3 text-right">
                                  <div className="flex items-center justify-end gap-2">
                                    <button
                                      onClick={() => mergePair(p.product_a_id, p.product_b_id, pairKey, p)}
                                      disabled={isMerging || bulkMerging}
                                      title="Merge A into B (B becomes canonical)"
                                      className="px-2 py-1 text-xs font-medium bg-cannabis-50 text-cannabis-700 border border-cannabis-200 rounded hover:bg-cannabis-100 disabled:opacity-50"
                                    >
                                      {isMerging ? '…' : 'Merge A→B'}
                                    </button>
                                    <button
                                      onClick={() => dismissPair(p)}
                                      disabled={bulkMerging}
                                      title="Keep as separate products"
                                      className="px-2 py-1 text-xs font-medium bg-gray-50 text-gray-600 border border-gray-200 rounded hover:bg-gray-100 disabled:opacity-50"
                                    >
                                      Keep Separate
                                    </button>
                                  </div>
                                </td>
                              </tr>
                            )
                          })}
                        </tbody>
                      </table>
                    </div>
                  )
                )}
              </div>

              {/* Duplicate Dispensaries */}
              <div className="mb-8">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900">Duplicate Dispensary Records</h2>
                    <p className="text-xs text-gray-500 mt-0.5">
                      Dispensary DB records with similar names that likely represent the same physical store.
                      Merging consolidates all prices and scraper logs under the canonical record.
                    </p>
                  </div>
                  {!dispDupLoaded && (
                    <button
                      onClick={loadDispensaryDuplicates}
                      disabled={dispDupLoading}
                      className="px-4 py-2 text-sm font-medium bg-cannabis-600 text-white rounded-lg hover:bg-cannabis-700 disabled:opacity-50"
                    >
                      {dispDupLoading ? 'Scanning…' : 'Scan for Duplicates'}
                    </button>
                  )}
                  {dispDupLoaded && (
                    <button
                      onClick={loadDispensaryDuplicates}
                      disabled={dispDupLoading}
                      className="px-3 py-1.5 text-xs font-medium bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 disabled:opacity-50"
                    >
                      {dispDupLoading ? 'Refreshing…' : 'Refresh'}
                    </button>
                  )}
                </div>

                {dispDupError && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
                    {dispDupError}
                  </div>
                )}

                {dispDupLoading && (
                  <div className="text-gray-500 py-8 text-center text-sm">Scanning dispensary names…</div>
                )}

                {!dispDupLoading && dispDupLoaded && (
                  dispDupGroups.length === 0 ? (
                    <div className="bg-white rounded-lg border p-6 text-center text-gray-500 text-sm">
                      No duplicate dispensary records detected.
                    </div>
                  ) : (
                    <div className="bg-white rounded-lg border overflow-hidden">
                      <table className="w-full text-sm">
                        <thead className="bg-gray-50 border-b">
                          <tr>
                            <th className="text-left px-4 py-2 font-medium text-gray-700">Canonical (keep)</th>
                            <th className="text-left px-4 py-2 font-medium text-gray-700">Duplicates (merge away)</th>
                            <th className="text-right px-4 py-2 font-medium text-gray-700">Actions</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y">
                          {dispDupGroups.map((group) => {
                            const isMerging = mergingDisp === group.canonical.id
                            return (
                              <tr key={group.canonical.id} className="hover:bg-gray-50">
                                <td className="px-4 py-3">
                                  <span className="font-medium text-gray-900">{group.canonical.name}</span>
                                  {group.canonical.location && (
                                    <span className="ml-1 text-xs text-gray-400">({group.canonical.location})</span>
                                  )}
                                  <span className="ml-2 text-xs text-gray-400">{group.canonical.product_count} products</span>
                                </td>
                                <td className="px-4 py-3">
                                  <div className="flex flex-wrap gap-1">
                                    {group.duplicates.map((d) => (
                                      <span key={d.id} className="px-2 py-0.5 bg-red-50 text-red-700 border border-red-200 rounded text-xs">
                                        {d.name}
                                        <span className="ml-1 text-red-400">({d.product_count})</span>
                                      </span>
                                    ))}
                                  </div>
                                </td>
                                <td className="px-4 py-3 text-right">
                                  <button
                                    onClick={() => mergeDispensaryGroup(group)}
                                    disabled={isMerging || mergingDisp !== null}
                                    className="px-3 py-1 text-xs font-medium bg-cannabis-50 text-cannabis-700 border border-cannabis-200 rounded hover:bg-cannabis-100 disabled:opacity-50"
                                    title={`Merge ${group.duplicates.length} duplicate(s) into "${group.canonical.name}"`}
                                  >
                                    {isMerging ? 'Merging…' : 'Merge into Canonical'}
                                  </button>
                                </td>
                              </tr>
                            )
                          })}
                        </tbody>
                      </table>
                    </div>
                  )
                )}
              </div>

              {/* Product Table */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h2 className="text-lg font-semibold text-gray-900">
                    Multi-Dispensary Products
                    {crossProducts.length > 0 && (
                      <span className="ml-2 text-sm font-normal text-gray-500">
                        ({crossProducts.length} products)
                      </span>
                    )}
                  </h2>
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-gray-500">Sort by:</span>
                    <button
                      onClick={() => setSortBy('dispensary_count')}
                      className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                        sortBy === 'dispensary_count'
                          ? 'bg-cannabis-600 text-white'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      # Dispensaries
                    </button>
                    <button
                      onClick={() => setSortBy('name')}
                      className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                        sortBy === 'name'
                          ? 'bg-cannabis-600 text-white'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      Name
                    </button>
                  </div>
                </div>

                {sortedProducts.length === 0 ? (
                  <div className="bg-white rounded-lg border p-8 text-center">
                    <p className="text-gray-500 text-sm">
                      No products found at 2+ dispensaries.
                    </p>
                    <p className="text-gray-400 text-xs mt-1">
                      Run scrapers and check the Cleanup Queue for auto-merged flags.
                    </p>
                  </div>
                ) : (
                  <div className="bg-white rounded-lg border overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50 border-b">
                        <tr>
                          <th className="text-left px-4 py-2 font-medium text-gray-700">Product</th>
                          <th className="text-left px-4 py-2 font-medium text-gray-700">Brand</th>
                          <th className="text-left px-4 py-2 font-medium text-gray-700">Type</th>
                          <th className="text-left px-4 py-2 font-medium text-gray-700">Dispensaries</th>
                          <th className="text-left px-4 py-2 font-medium text-gray-700">Variants</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {sortedProducts.map((p) => (
                          <tr key={p.id} className="hover:bg-gray-50">
                            <td className="px-4 py-2">
                              <Link
                                href={`/products/${p.id}`}
                                className="font-medium text-cannabis-700 hover:underline"
                              >
                                {p.name}
                              </Link>
                            </td>
                            <td className="px-4 py-2 text-gray-600">{p.brand ?? '—'}</td>
                            <td className="px-4 py-2 text-gray-600">{p.product_type}</td>
                            <td className="px-4 py-2">
                              <div className="flex items-center gap-2">
                                <DispensaryCountBadge count={p.dispensary_count} />
                                <div className="flex flex-wrap gap-1">
                                  {p.dispensaries.map((name) => (
                                    <span
                                      key={name}
                                      className="px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded text-xs"
                                    >
                                      {name}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            </td>
                            <td className="px-4 py-2 text-gray-500">{p.variant_count}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}

function TabButton({
  active, onClick, label,
}: {
  active: boolean; onClick: () => void; label: string
}) {
  return (
    <button
      onClick={onClick}
      className={`px-5 py-2.5 text-sm font-medium border-b-2 transition-colors ${
        active
          ? 'border-cannabis-600 text-cannabis-700'
          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
      }`}
    >
      {label}
    </button>
  )
}

function CompletenessCard({
  label, count, pct, total,
}: {
  label: string; count: number; pct: number; total: number
}) {
  const color = pct < 10 ? 'green' : pct < 30 ? 'yellow' : 'red'
  const colorMap = {
    green: 'bg-green-50 border-green-200 text-green-900',
    yellow: 'bg-yellow-50 border-yellow-200 text-yellow-900',
    red: 'bg-red-50 border-red-200 text-red-900',
  }
  const labelMap = {
    green: 'text-green-700',
    yellow: 'text-yellow-700',
    red: 'text-red-700',
  }

  return (
    <div className={`p-4 rounded-lg border ${colorMap[color]}`}>
      <p className={`text-sm font-medium ${labelMap[color]}`}>{label}</p>
      <p className="text-3xl font-bold mt-1">{pct}%</p>
      <p className="text-xs mt-1 opacity-75">{count} of {total} products</p>
    </div>
  )
}

function FreshnessBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    fresh: 'bg-green-100 text-green-800',
    stale: 'bg-yellow-100 text-yellow-800',
    critical: 'bg-red-100 text-red-800',
    never: 'bg-gray-100 text-gray-600',
  }
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${styles[status] ?? 'bg-gray-100 text-gray-700'}`}>
      {status}
    </span>
  )
}

function CoverageCard({
  label, count, total, color, hint,
}: {
  label: string; count: number; total: number; color: string; hint?: string
}) {
  const colorMap: Record<string, string> = {
    gray: 'bg-gray-50 border-gray-200',
    yellow: 'bg-yellow-50 border-yellow-200',
    blue: 'bg-blue-50 border-blue-200',
    green: 'bg-green-50 border-green-200',
    cannabis: 'bg-cannabis-50 border-cannabis-200',
  }
  const textMap: Record<string, string> = {
    gray: 'text-gray-700',
    yellow: 'text-yellow-700',
    blue: 'text-blue-700',
    green: 'text-green-700',
    cannabis: 'text-cannabis-700',
  }
  const numMap: Record<string, string> = {
    gray: 'text-gray-900',
    yellow: 'text-yellow-900',
    blue: 'text-blue-900',
    green: 'text-green-900',
    cannabis: 'text-cannabis-900',
  }

  return (
    <div className={`p-3 rounded-lg border ${colorMap[color]}`}>
      <p className={`text-xs font-medium ${textMap[color]}`}>{label}</p>
      <p className={`text-2xl font-bold mt-1 ${numMap[color]}`}>{count}</p>
      {hint && <p className="text-xs mt-0.5 text-gray-400">{hint}</p>}
      {!hint && total > 0 && (
        <p className="text-xs mt-0.5 text-gray-400">
          {((count / total) * 100).toFixed(0)}% of total
        </p>
      )}
    </div>
  )
}

function DispensaryCountBadge({ count }: { count: number }) {
  const style =
    count >= 4 ? 'bg-cannabis-100 text-cannabis-800' :
    count === 3 ? 'bg-green-100 text-green-800' :
    'bg-blue-100 text-blue-800'
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-bold whitespace-nowrap ${style}`}>
      {count}x
    </span>
  )
}
