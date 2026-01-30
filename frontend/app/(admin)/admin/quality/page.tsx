'use client'

import React, { useEffect, useState } from 'react'
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

export default function QualityPage() {
  const [metrics, setMetrics] = useState<QualityMetrics | null>(null)
  const [freshness, setFreshness] = useState<DispensaryFreshness[]>([])
  const [outliers, setOutliers] = useState<Outlier[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.get('/api/admin/scrapers/quality/metrics').catch(() => null),
      api.get('/api/admin/scrapers/dispensaries/freshness').catch(() => null),
      api.get('/api/admin/outliers?limit=20').catch(() => null),
    ]).then(([metricsRes, freshnessRes, outliersRes]) => {
      if (metricsRes) setMetrics(metricsRes.data)
      if (freshnessRes) setFreshness(freshnessRes.data)
      if (outliersRes) setOutliers(outliersRes.data?.outliers ?? [])
      setLoading(false)
    })
  }, [])

  if (loading) {
    return <div className="text-gray-500 py-12 text-center">Loading quality data...</div>
  }

  return (
    <div>
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
    </div>
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
