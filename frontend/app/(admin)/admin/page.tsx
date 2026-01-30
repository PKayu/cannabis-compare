'use client'

import React, { useEffect, useState } from 'react'
import Link from 'next/link'
import { api } from '@/lib/api'

interface DashboardData {
  flags: { pending: number }
  products: { total_master: number; total_prices: number }
  quality: { outliers_total: number; outliers_high_severity: number }
}

interface ScraperHealth {
  scraper_id: string
  scraper_name: string
  success_rate_7d: number
  last_run_at: string | null
  last_run_status: string | null
}

interface ScraperRunItem {
  id: string
  scraper_name: string
  started_at: string
  status: string
  products_found: number
  duration_seconds: number | null
  triggered_by: string | null
}

export default function AdminDashboardPage() {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [health, setHealth] = useState<ScraperHealth[]>([])
  const [recentRuns, setRecentRuns] = useState<ScraperRunItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.get('/api/admin/dashboard').catch(() => null),
      api.get('/api/admin/scrapers/health').catch(() => null),
      api.get('/api/admin/scrapers/runs?limit=10').catch(() => null),
    ]).then(([dashRes, healthRes, runsRes]) => {
      if (dashRes) setDashboard(dashRes.data)
      if (healthRes) setHealth(healthRes.data)
      if (runsRes) setRecentRuns(runsRes.data)
      setLoading(false)
    })
  }, [])

  if (loading) {
    return <div className="text-gray-500 py-12 text-center">Loading dashboard...</div>
  }

  const healthyScrapers = health.filter(h => h.success_rate_7d >= 70).length

  return (
    <div>
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <StatCard
          label="Pending Flags"
          value={dashboard?.flags.pending ?? 0}
          color="yellow"
          href="/admin/cleanup"
        />
        <StatCard
          label="Healthy Scrapers"
          value={`${healthyScrapers}/${health.length}`}
          color="green"
          href="/admin/scrapers"
        />
        <StatCard
          label="Master Products"
          value={dashboard?.products.total_master ?? 0}
          color="blue"
        />
        <StatCard
          label="Price Outliers"
          value={dashboard?.quality.outliers_high_severity ?? 0}
          color="red"
          href="/admin/quality"
        />
      </div>

      {/* Quick Actions */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Quick Actions</h2>
        <div className="flex flex-wrap gap-3">
          <Link
            href="/admin/cleanup"
            className="px-4 py-2 bg-yellow-100 text-yellow-800 rounded-lg text-sm font-medium hover:bg-yellow-200"
          >
            Review Flags ({dashboard?.flags.pending ?? 0})
          </Link>
          <Link
            href="/admin/scrapers"
            className="px-4 py-2 bg-green-100 text-green-800 rounded-lg text-sm font-medium hover:bg-green-200"
          >
            Manage Scrapers
          </Link>
          <Link
            href="/admin/quality"
            className="px-4 py-2 bg-blue-100 text-blue-800 rounded-lg text-sm font-medium hover:bg-blue-200"
          >
            View Data Quality
          </Link>
        </div>
      </div>

      {/* Recent Scraper Activity */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Recent Scraper Activity</h2>
        {recentRuns.length === 0 ? (
          <div className="bg-white rounded-lg border p-6 text-center text-gray-500">
            No scraper runs recorded yet.
          </div>
        ) : (
          <div className="bg-white rounded-lg border overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="text-left px-4 py-2 font-medium text-gray-700">Scraper</th>
                  <th className="text-left px-4 py-2 font-medium text-gray-700">Time</th>
                  <th className="text-left px-4 py-2 font-medium text-gray-700">Status</th>
                  <th className="text-left px-4 py-2 font-medium text-gray-700">Products</th>
                  <th className="text-left px-4 py-2 font-medium text-gray-700">Duration</th>
                  <th className="text-left px-4 py-2 font-medium text-gray-700">Trigger</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {recentRuns.map((run) => (
                  <tr key={run.id} className="hover:bg-gray-50">
                    <td className="px-4 py-2 font-medium">{run.scraper_name}</td>
                    <td className="px-4 py-2 text-gray-600">
                      {new Date(run.started_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-2">
                      <StatusBadge status={run.status} />
                    </td>
                    <td className="px-4 py-2">{run.products_found}</td>
                    <td className="px-4 py-2 text-gray-600">
                      {run.duration_seconds ? `${run.duration_seconds.toFixed(1)}s` : '-'}
                    </td>
                    <td className="px-4 py-2 text-gray-500 text-xs">{run.triggered_by ?? '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

function StatCard({
  label, value, color, href,
}: {
  label: string
  value: string | number
  color: 'yellow' | 'green' | 'blue' | 'red'
  href?: string
}) {
  const colorMap = {
    yellow: 'bg-yellow-50 border-yellow-200 text-yellow-900',
    green: 'bg-green-50 border-green-200 text-green-900',
    blue: 'bg-blue-50 border-blue-200 text-blue-900',
    red: 'bg-red-50 border-red-200 text-red-900',
  }
  const labelColorMap = {
    yellow: 'text-yellow-700',
    green: 'text-green-700',
    blue: 'text-blue-700',
    red: 'text-red-700',
  }

  const content = (
    <div className={`p-4 rounded-lg border ${colorMap[color]}`}>
      <p className={`text-sm font-medium ${labelColorMap[color]}`}>{label}</p>
      <p className="text-3xl font-bold mt-1">{value}</p>
    </div>
  )

  if (href) {
    return <Link href={href}>{content}</Link>
  }
  return content
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
