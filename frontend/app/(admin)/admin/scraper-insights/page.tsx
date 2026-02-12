'use client'

import React, { useEffect, useState } from 'react'
import { api } from '@/lib/api'

interface ScraperHealth {
  scraper_id: string
  scraper_name: string
  enabled: boolean
  total_runs_7d: number
  successful_runs_7d: number
  failed_runs_7d: number
  success_rate_7d: number
  avg_duration_seconds: number | null
  last_run_at: string | null
  last_run_status: string | null
  total_products_last_run: number
}

interface ScraperRun {
  id: string
  scraper_id: string
  scraper_name: string
  started_at: string
  completed_at: string | null
  duration_seconds: number | null
  status: string
  products_found: number
  products_processed: number
  flags_created: number
  error_message: string | null
  triggered_by: string | null
}

interface CorrectionPattern {
  field: string
  count: number
  common_pattern: { from: string | null; to: string | null } | null
}

interface DispensaryAnalytics {
  dispensary_id: string
  dispensary_name: string
  total_flags: number
  approved: number
  rejected: number
  dismissed: number
  correction_rate: number
  top_corrections: CorrectionPattern[]
}

interface FlagAnalyticsResponse {
  days: number
  by_dispensary: DispensaryAnalytics[]
}

const DAY_OPTIONS = [7, 14, 30, 90]

export default function ScraperInsightsPage() {
  const [health, setHealth] = useState<ScraperHealth[]>([])
  const [runs, setRuns] = useState<ScraperRun[]>([])
  const [analytics, setAnalytics] = useState<FlagAnalyticsResponse | null>(null)
  const [selectedDays, setSelectedDays] = useState(30)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    Promise.all([
      api.get('/api/admin/scrapers/health').catch(() => null),
      api.get('/api/admin/scrapers/runs?limit=200').catch(() => null),
      api.get(`/api/admin/flags/analytics?days=${selectedDays}`).catch(() => null),
    ]).then(([healthRes, runsRes, analyticsRes]) => {
      if (healthRes) setHealth(healthRes.data)
      if (runsRes) setRuns(runsRes.data)
      if (analyticsRes) setAnalytics(analyticsRes.data)
      setLoading(false)
    })
  }, [selectedDays])

  if (loading) {
    return <div className="text-gray-500 py-12 text-center">Loading scraper insights...</div>
  }

  // Compute summary metrics from health data
  const totalRuns7d = health.reduce((sum, s) => sum + s.total_runs_7d, 0)
  const avgSuccessRate = health.length > 0
    ? health.reduce((sum, s) => sum + s.success_rate_7d, 0) / health.length
    : 0
  const totalProductsLastCycle = health.reduce((sum, s) => sum + s.total_products_last_run, 0)
  const avgDuration = health.filter(s => s.avg_duration_seconds != null).length > 0
    ? health.reduce((sum, s) => sum + (s.avg_duration_seconds ?? 0), 0) /
      health.filter(s => s.avg_duration_seconds != null).length
    : null

  // Compute per-scraper trends from run history
  const scraperTrends = computeScraperTrends(runs)

  // Compute matching quality from successful runs
  const successfulRuns = runs.filter(r => r.status === 'success' && r.products_found > 0)
  const totalFound = successfulRuns.reduce((sum, r) => sum + r.products_found, 0)
  const totalProcessed = successfulRuns.reduce((sum, r) => sum + r.products_processed, 0)
  const totalFlagged = successfulRuns.reduce((sum, r) => sum + r.flags_created, 0)
  const autoMergeCount = totalProcessed - totalFlagged
  const autoMergePct = totalFound > 0 ? (autoMergeCount / totalFound) * 100 : 0
  const flagPct = totalFound > 0 ? (totalFlagged / totalFound) * 100 : 0
  const newProductPct = totalFound > 0 ? ((totalFound - totalProcessed) / totalFound) * 100 : 0

  return (
    <div>
      {/* Summary Cards */}
      <h2 className="text-lg font-semibold text-gray-900 mb-3">Overview (7-day)</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <SummaryCard label="Total Runs" value={totalRuns7d} />
        <SummaryCard
          label="Avg Success Rate"
          value={`${avgSuccessRate.toFixed(0)}%`}
          color={avgSuccessRate >= 90 ? 'green' : avgSuccessRate >= 70 ? 'yellow' : 'red'}
        />
        <SummaryCard label="Products Last Cycle" value={totalProductsLastCycle} />
        <SummaryCard
          label="Avg Duration"
          value={avgDuration != null ? `${avgDuration.toFixed(1)}s` : '-'}
        />
      </div>

      {/* Matching Quality */}
      <h2 className="text-lg font-semibold text-gray-900 mb-3">Product Matching Quality</h2>
      {totalFound === 0 ? (
        <div className="bg-white rounded-lg border p-6 text-center text-gray-500 mb-8">
          No successful runs with products yet.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="p-4 rounded-lg border bg-green-50 border-green-200">
            <p className="text-sm font-medium text-green-700">Auto-Merged (&gt;90%)</p>
            <p className="text-3xl font-bold text-green-900 mt-1">{autoMergePct.toFixed(1)}%</p>
            <p className="text-xs text-green-600 mt-1">{autoMergeCount} of {totalFound} products</p>
          </div>
          <div className="p-4 rounded-lg border bg-yellow-50 border-yellow-200">
            <p className="text-sm font-medium text-yellow-700">Flagged (60-90%)</p>
            <p className="text-3xl font-bold text-yellow-900 mt-1">{flagPct.toFixed(1)}%</p>
            <p className="text-xs text-yellow-600 mt-1">{totalFlagged} of {totalFound} products</p>
          </div>
          <div className="p-4 rounded-lg border bg-blue-50 border-blue-200">
            <p className="text-sm font-medium text-blue-700">New Products (&lt;60%)</p>
            <p className="text-3xl font-bold text-blue-900 mt-1">{newProductPct.toFixed(1)}%</p>
            <p className="text-xs text-blue-600 mt-1">{totalFound - totalProcessed} of {totalFound} products</p>
          </div>
        </div>
      )}

      {/* Per-Scraper Trends */}
      <h2 className="text-lg font-semibold text-gray-900 mb-3">Per-Scraper Trends</h2>
      {scraperTrends.length === 0 ? (
        <div className="bg-white rounded-lg border p-6 text-center text-gray-500 mb-8">
          No run data available.
        </div>
      ) : (
        <div className="bg-white rounded-lg border overflow-hidden mb-8">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-2 font-medium text-gray-700">Scraper</th>
                <th className="text-left px-4 py-2 font-medium text-gray-700">Avg Products</th>
                <th className="text-left px-4 py-2 font-medium text-gray-700">Processing Rate</th>
                <th className="text-left px-4 py-2 font-medium text-gray-700">Flag Rate</th>
                <th className="text-left px-4 py-2 font-medium text-gray-700">Last 5 Runs</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {scraperTrends.map((trend) => (
                <tr key={trend.scraperId} className="hover:bg-gray-50">
                  <td className="px-4 py-2 font-medium">{trend.scraperName}</td>
                  <td className="px-4 py-2 text-gray-600">
                    {trend.avgProductsFound.toFixed(0)}
                    <TrendArrow current={trend.latestProductsFound} average={trend.avgProductsFound} />
                  </td>
                  <td className="px-4 py-2 text-gray-600">{trend.processingRate.toFixed(0)}%</td>
                  <td className="px-4 py-2 text-gray-600">{trend.flagRate.toFixed(1)}%</td>
                  <td className="px-4 py-2">
                    <div className="flex gap-1">
                      {trend.lastFiveStatuses.map((status, i) => (
                        <StatusDot key={i} status={status} />
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Flag Analytics by Dispensary */}
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-semibold text-gray-900">Flag Analytics by Dispensary</h2>
        <div className="flex gap-1">
          {DAY_OPTIONS.map((d) => (
            <button
              key={d}
              onClick={() => setSelectedDays(d)}
              className={`px-3 py-1 rounded text-sm font-medium ${
                selectedDays === d
                  ? 'bg-gray-800 text-white'
                  : 'bg-white text-gray-600 border border-gray-300 hover:bg-gray-50'
              }`}
            >
              {d}d
            </button>
          ))}
        </div>
      </div>

      {!analytics || analytics.by_dispensary.length === 0 ? (
        <div className="bg-white rounded-lg border p-6 text-center text-gray-500">
          No flag data for the last {selectedDays} days.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {analytics.by_dispensary.map((d) => (
            <div key={d.dispensary_id} className="bg-white rounded-lg border p-4">
              <div className="flex justify-between items-start mb-3">
                <h3 className="font-semibold text-gray-900">{d.dispensary_name}</h3>
                <span className="text-sm text-gray-500">{d.total_flags} flags</span>
              </div>

              {/* Resolution bar */}
              <div className="flex h-3 rounded-full overflow-hidden bg-gray-100 mb-2">
                {d.total_flags > 0 && (
                  <>
                    <div
                      className="bg-green-500"
                      style={{ width: `${(d.approved / d.total_flags) * 100}%` }}
                      title={`Approved: ${d.approved}`}
                    />
                    <div
                      className="bg-red-400"
                      style={{ width: `${(d.rejected / d.total_flags) * 100}%` }}
                      title={`Rejected: ${d.rejected}`}
                    />
                    <div
                      className="bg-gray-400"
                      style={{ width: `${(d.dismissed / d.total_flags) * 100}%` }}
                      title={`Dismissed: ${d.dismissed}`}
                    />
                  </>
                )}
              </div>

              <div className="flex gap-4 text-xs text-gray-500 mb-3">
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-green-500 inline-block" />
                  Approved {d.approved}
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-red-400 inline-block" />
                  Rejected {d.rejected}
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-gray-400 inline-block" />
                  Dismissed {d.dismissed}
                </span>
              </div>

              <div className="text-sm text-gray-600 mb-2">
                Correction rate: <span className="font-medium">{(d.correction_rate * 100).toFixed(0)}%</span>
              </div>

              {d.top_corrections.length > 0 && (
                <div className="mt-2">
                  <p className="text-xs font-medium text-gray-500 mb-1">Top Corrections</p>
                  <div className="space-y-1">
                    {d.top_corrections.slice(0, 3).map((c, i) => (
                      <div key={i} className="text-xs text-gray-600 flex justify-between">
                        <span className="font-medium">{c.field}</span>
                        <span>
                          {c.count}x
                          {c.common_pattern && (
                            <span className="ml-1 text-gray-400">
                              {c.common_pattern.from || '(empty)'} &rarr; {c.common_pattern.to || '(empty)'}
                            </span>
                          )}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// --- Helper components ---

function SummaryCard({
  label, value, color,
}: {
  label: string; value: string | number; color?: 'green' | 'yellow' | 'red'
}) {
  const colorMap = {
    green: 'bg-green-50 border-green-200',
    yellow: 'bg-yellow-50 border-yellow-200',
    red: 'bg-red-50 border-red-200',
  }
  const bg = color ? colorMap[color] : 'bg-white border-gray-200'

  return (
    <div className={`p-4 rounded-lg border ${bg}`}>
      <p className="text-sm font-medium text-gray-500">{label}</p>
      <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
    </div>
  )
}

function TrendArrow({ current, average }: { current: number; average: number }) {
  if (average === 0) return null
  const diff = ((current - average) / average) * 100
  if (Math.abs(diff) < 5) return null
  return (
    <span className={`ml-1 text-xs ${diff > 0 ? 'text-green-600' : 'text-red-600'}`}>
      {diff > 0 ? '\u2191' : '\u2193'}
    </span>
  )
}

function StatusDot({ status }: { status: string }) {
  const colors: Record<string, string> = {
    success: 'bg-green-500',
    error: 'bg-red-500',
    warning: 'bg-yellow-500',
    running: 'bg-blue-500',
  }
  return (
    <span
      className={`w-3 h-3 rounded-full inline-block ${colors[status] ?? 'bg-gray-300'}`}
      title={status}
    />
  )
}

// --- Data processing ---

interface ScraperTrend {
  scraperId: string
  scraperName: string
  avgProductsFound: number
  latestProductsFound: number
  processingRate: number
  flagRate: number
  lastFiveStatuses: string[]
}

function computeScraperTrends(runs: ScraperRun[]): ScraperTrend[] {
  const byScraperId: Record<string, ScraperRun[]> = {}
  for (const run of runs) {
    if (!byScraperId[run.scraper_id]) byScraperId[run.scraper_id] = []
    byScraperId[run.scraper_id].push(run)
  }

  return Object.entries(byScraperId).map(([scraperId, scraperRuns]) => {
    const successRuns = scraperRuns.filter(r => r.status === 'success' && r.products_found > 0)
    const totalFound = successRuns.reduce((s, r) => s + r.products_found, 0)
    const totalProcessed = successRuns.reduce((s, r) => s + r.products_processed, 0)
    const totalFlagged = successRuns.reduce((s, r) => s + r.flags_created, 0)

    return {
      scraperId,
      scraperName: scraperRuns[0]?.scraper_name ?? scraperId,
      avgProductsFound: successRuns.length > 0 ? totalFound / successRuns.length : 0,
      latestProductsFound: successRuns[0]?.products_found ?? 0,
      processingRate: totalFound > 0 ? (totalProcessed / totalFound) * 100 : 0,
      flagRate: totalFound > 0 ? (totalFlagged / totalFound) * 100 : 0,
      lastFiveStatuses: scraperRuns.slice(0, 5).map(r => r.status),
    }
  })
}
