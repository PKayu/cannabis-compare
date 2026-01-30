'use client'

import React, { useEffect, useState, useCallback } from 'react'
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
  error_message: string | null
  triggered_by: string | null
}

export default function ScrapersPage() {
  const [health, setHealth] = useState<ScraperHealth[]>([])
  const [runs, setRuns] = useState<ScraperRun[]>([])
  const [filterScraper, setFilterScraper] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [runningScrapers, setRunningScrapers] = useState<Set<string>>(new Set())

  const loadData = useCallback(async () => {
    try {
      const params = filterScraper ? `?scraper_id=${filterScraper}&limit=50` : '?limit=50'
      const [healthRes, runsRes] = await Promise.all([
        api.get('/api/admin/scrapers/health'),
        api.get(`/api/admin/scrapers/runs${params}`),
      ])
      setHealth(healthRes.data)
      setRuns(runsRes.data)
    } catch (err) {
      console.error('Failed to load scraper data:', err)
    } finally {
      setLoading(false)
    }
  }, [filterScraper])

  useEffect(() => {
    loadData()
  }, [loadData])

  const triggerRun = async (scraperId: string) => {
    setRunningScrapers(prev => new Set(prev).add(scraperId))
    try {
      await api.post(`/api/admin/scrapers/run/${scraperId}`)
      await loadData()
    } catch (err) {
      console.error('Failed to trigger scraper:', err)
    } finally {
      setRunningScrapers(prev => {
        const next = new Set(prev)
        next.delete(scraperId)
        return next
      })
    }
  }

  if (loading) {
    return <div className="text-gray-500 py-12 text-center">Loading scraper data...</div>
  }

  return (
    <div>
      {/* Scraper Health Cards */}
      <h2 className="text-lg font-semibold text-gray-900 mb-3">Scraper Health (7-day)</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        {health.map((s) => {
          const healthColor =
            s.success_rate_7d >= 90 ? 'border-green-300 bg-green-50' :
            s.success_rate_7d >= 70 ? 'border-yellow-300 bg-yellow-50' :
            'border-red-300 bg-red-50'
          const badgeColor =
            s.success_rate_7d >= 90 ? 'bg-green-100 text-green-800' :
            s.success_rate_7d >= 70 ? 'bg-yellow-100 text-yellow-800' :
            'bg-red-100 text-red-800'

          return (
            <div key={s.scraper_id} className={`rounded-lg border p-4 ${healthColor}`}>
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h3 className="font-semibold text-gray-900">{s.scraper_name}</h3>
                  <p className="text-xs text-gray-500">{s.scraper_id}</p>
                </div>
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${badgeColor}`}>
                  {s.success_rate_7d}%
                </span>
              </div>

              <div className="grid grid-cols-3 gap-2 text-sm mb-3">
                <div>
                  <p className="text-gray-500">Runs</p>
                  <p className="font-medium">{s.total_runs_7d}</p>
                </div>
                <div>
                  <p className="text-gray-500">Failed</p>
                  <p className="font-medium text-red-600">{s.failed_runs_7d}</p>
                </div>
                <div>
                  <p className="text-gray-500">Avg Time</p>
                  <p className="font-medium">
                    {s.avg_duration_seconds ? `${s.avg_duration_seconds}s` : '-'}
                  </p>
                </div>
              </div>

              <div className="text-xs text-gray-500 mb-3">
                Last run: {s.last_run_at ? new Date(s.last_run_at).toLocaleString() : 'Never'}
                {s.last_run_status && (
                  <span className="ml-1">({s.last_run_status})</span>
                )}
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => triggerRun(s.scraper_id)}
                  disabled={runningScrapers.has(s.scraper_id) || !s.enabled}
                  className="flex-1 px-3 py-1.5 bg-cannabis-600 text-white rounded text-sm font-medium hover:bg-cannabis-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {runningScrapers.has(s.scraper_id) ? 'Running...' : 'Run Now'}
                </button>
                <button
                  onClick={() => {
                    setFilterScraper(filterScraper === s.scraper_id ? null : s.scraper_id)
                  }}
                  className={`px-3 py-1.5 rounded text-sm font-medium border ${
                    filterScraper === s.scraper_id
                      ? 'bg-gray-800 text-white border-gray-800'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  {filterScraper === s.scraper_id ? 'Show All' : 'View Runs'}
                </button>
              </div>
            </div>
          )
        })}
      </div>

      {/* Run History Table */}
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-semibold text-gray-900">
          Run History
          {filterScraper && (
            <span className="ml-2 text-sm font-normal text-gray-500">
              filtered: {filterScraper}
            </span>
          )}
        </h2>
        {filterScraper && (
          <button
            onClick={() => setFilterScraper(null)}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            Clear filter
          </button>
        )}
      </div>

      {runs.length === 0 ? (
        <div className="bg-white rounded-lg border p-6 text-center text-gray-500">
          No scraper runs recorded yet.
        </div>
      ) : (
        <div className="bg-white rounded-lg border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-2 font-medium text-gray-700">Scraper</th>
                <th className="text-left px-4 py-2 font-medium text-gray-700">Started</th>
                <th className="text-left px-4 py-2 font-medium text-gray-700">Duration</th>
                <th className="text-left px-4 py-2 font-medium text-gray-700">Status</th>
                <th className="text-left px-4 py-2 font-medium text-gray-700">Found</th>
                <th className="text-left px-4 py-2 font-medium text-gray-700">Processed</th>
                <th className="text-left px-4 py-2 font-medium text-gray-700">Error</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {runs.map((run) => (
                <tr key={run.id} className="hover:bg-gray-50">
                  <td className="px-4 py-2 font-medium">{run.scraper_name}</td>
                  <td className="px-4 py-2 text-gray-600">
                    {new Date(run.started_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-2 text-gray-600">
                    {run.duration_seconds ? `${run.duration_seconds.toFixed(1)}s` : '-'}
                  </td>
                  <td className="px-4 py-2">
                    <StatusBadge status={run.status} />
                  </td>
                  <td className="px-4 py-2">{run.products_found}</td>
                  <td className="px-4 py-2">{run.products_processed}</td>
                  <td className="px-4 py-2 text-red-600 text-xs max-w-xs truncate">
                    {run.error_message ?? '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    success: 'bg-green-100 text-green-800',
    error: 'bg-red-100 text-red-800',
    warning: 'bg-yellow-100 text-yellow-800',
    running: 'bg-blue-100 text-blue-800',
  }
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${styles[status] ?? 'bg-gray-100 text-gray-700'}`}>
      {status}
    </span>
  )
}
