'use client'

import React, { useEffect, useState } from 'react'
import { api } from '@/lib/api'

interface PriceHistory {
  date: string
  min: number
  max: number
  avg: number
}

interface PricingChartProps {
  productId: string
}

export default function PricingChart({ productId }: PricingChartProps) {
  const [history, setHistory] = useState<PriceHistory[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [days, setDays] = useState(30)

  useEffect(() => {
    loadHistory()
  }, [productId, days])

  const loadHistory = async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await api.products.getPricingHistory(productId, days)
      setHistory(res.data)
    } catch (err) {
      console.error('Failed to load pricing history:', err)
      setError('Unable to load price history')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-48 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6 text-center text-gray-600">
        {error}
      </div>
    )
  }

  if (history.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6 text-center text-gray-600">
        No price history available yet. Check back after prices have been tracked for a few days.
      </div>
    )
  }

  // Calculate chart dimensions
  const minPrice = Math.min(...history.map(h => h.min)) * 0.95
  const maxPrice = Math.max(...history.map(h => h.max)) * 1.05
  const priceRange = maxPrice - minPrice

  // Helper to calculate Y position (percentage from bottom)
  const getYPosition = (price: number) => {
    return ((price - minPrice) / priceRange) * 100
  }

  // Format date for display
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* Controls */}
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">Show:</span>
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="px-2 py-1 border border-gray-300 rounded text-sm"
          >
            <option value={7}>7 days</option>
            <option value={30}>30 days</option>
            <option value={90}>90 days</option>
          </select>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 bg-green-500 rounded-full"></span>
            Min
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 bg-cannabis-500 rounded-full"></span>
            Avg
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 bg-red-500 rounded-full"></span>
            Max
          </span>
        </div>
      </div>

      {/* Chart Area */}
      <div className="relative h-48 border-l border-b border-gray-200">
        {/* Y-axis labels */}
        <div className="absolute -left-12 top-0 h-full flex flex-col justify-between text-xs text-gray-500">
          <span>${maxPrice.toFixed(0)}</span>
          <span>${((maxPrice + minPrice) / 2).toFixed(0)}</span>
          <span>${minPrice.toFixed(0)}</span>
        </div>

        {/* Chart bars */}
        <div className="flex items-end h-full gap-1 px-2">
          {history.map((point, index) => (
            <div
              key={point.date}
              className="flex-1 relative group"
              style={{ minWidth: '20px' }}
            >
              {/* Price range bar (min to max) */}
              <div
                className="absolute w-full bg-gray-200 rounded"
                style={{
                  bottom: `${getYPosition(point.min)}%`,
                  height: `${getYPosition(point.max) - getYPosition(point.min)}%`,
                  minHeight: '4px'
                }}
              />

              {/* Average line marker */}
              <div
                className="absolute w-full h-1 bg-cannabis-500 rounded"
                style={{
                  bottom: `${getYPosition(point.avg)}%`
                }}
              />

              {/* Min dot */}
              <div
                className="absolute w-2 h-2 bg-green-500 rounded-full -translate-x-1/2 left-1/2"
                style={{
                  bottom: `${getYPosition(point.min)}%`
                }}
              />

              {/* Max dot */}
              <div
                className="absolute w-2 h-2 bg-red-500 rounded-full -translate-x-1/2 left-1/2"
                style={{
                  bottom: `${getYPosition(point.max)}%`
                }}
              />

              {/* Tooltip */}
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity z-10 pointer-events-none">
                <div className="bg-gray-900 text-white text-xs rounded px-2 py-1 whitespace-nowrap">
                  <p className="font-semibold">{formatDate(point.date)}</p>
                  <p className="text-green-400">Min: ${point.min.toFixed(2)}</p>
                  <p>Avg: ${point.avg.toFixed(2)}</p>
                  <p className="text-red-400">Max: ${point.max.toFixed(2)}</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* X-axis labels */}
        <div className="absolute -bottom-6 left-0 w-full flex justify-between text-xs text-gray-500 px-2">
          <span>{formatDate(history[0]?.date)}</span>
          {history.length > 1 && (
            <span>{formatDate(history[history.length - 1]?.date)}</span>
          )}
        </div>
      </div>

      {/* Summary Stats */}
      <div className="mt-8 grid grid-cols-3 gap-4 text-center">
        <div>
          <p className="text-sm text-gray-600">Lowest</p>
          <p className="text-lg font-bold text-green-600">
            ${Math.min(...history.map(h => h.min)).toFixed(2)}
          </p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Average</p>
          <p className="text-lg font-bold text-gray-700">
            ${(history.reduce((sum, h) => sum + h.avg, 0) / history.length).toFixed(2)}
          </p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Highest</p>
          <p className="text-lg font-bold text-red-600">
            ${Math.max(...history.map(h => h.max)).toFixed(2)}
          </p>
        </div>
      </div>
    </div>
  )
}
