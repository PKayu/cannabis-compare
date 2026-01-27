'use client'

import React, { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { useAuth } from '@/lib/AuthContext'

interface WatchlistButtonProps {
  productId: string
  initialWatched?: boolean
}

export default function WatchlistButton({ productId, initialWatched = false }: WatchlistButtonProps) {
  const { user } = useAuth()
  const [watched, setWatched] = useState(initialWatched)
  const [loading, setLoading] = useState(false)
  const [showConfig, setShowConfig] = useState(false)
  const [threshold, setThreshold] = useState(10)

  // Check watchlist status when user or productId changes
  useEffect(() => {
    if (user) {
      checkWatchlistStatus()
    } else {
      setWatched(false)
    }
  }, [productId, user])

  const checkWatchlistStatus = async () => {
    try {
      const response = await api.watchlist.check(productId)
      setWatched(response.data.is_watched)
      if (response.data.alert_settings?.price_drop_threshold) {
        setThreshold(response.data.alert_settings.price_drop_threshold)
      }
    } catch (error) {
      // User might not be logged in, that's okay
      console.log('Not logged in or error checking watchlist')
    }
  }

  const handleToggle = async () => {
    setLoading(true)

    try {
      if (watched) {
        await api.watchlist.remove(productId)
        setWatched(false)
        setShowConfig(false)
      } else {
        await api.watchlist.add({
          product_id: productId,
          alert_on_stock: true,
          alert_on_price_drop: true,
          price_drop_threshold: threshold
        })
        setWatched(true)
      }
    } catch (error: any) {
      if (error.response?.status === 401) {
        // Redirect to login
        window.location.href = `/auth/login?returnUrl=${encodeURIComponent(window.location.pathname)}`
      } else {
        console.error('Failed to toggle watchlist:', error)
        alert('Failed to update watchlist. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleThresholdChange = async (newThreshold: number) => {
    setThreshold(newThreshold)
    if (watched) {
      try {
        // Remove and re-add with new threshold
        await api.watchlist.remove(productId)
        await api.watchlist.add({
          product_id: productId,
          alert_on_stock: true,
          alert_on_price_drop: true,
          price_drop_threshold: newThreshold
        })
      } catch (error) {
        console.error('Failed to update threshold:', error)
      }
    }
  }

  return (
    <div className="inline-block">
      <button
        onClick={handleToggle}
        disabled={loading}
        className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
          watched
            ? 'bg-cannabis-100 text-cannabis-700 border-2 border-cannabis-300 hover:bg-cannabis-200'
            : 'bg-white text-gray-700 border-2 border-gray-300 hover:bg-gray-50'
        } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <span className="text-xl">{watched ? '★' : '☆'}</span>
        <span className="font-medium">{watched ? 'Watching' : 'Watch'}</span>
      </button>

      {watched && (
        <div className="mt-2">
          <button
            onClick={() => setShowConfig(!showConfig)}
            className="text-sm text-cannabis-600 hover:text-cannabis-700 underline"
          >
            {showConfig ? 'Hide' : 'Configure'} alerts
          </button>

          {showConfig && (
            <div className="mt-3 p-4 bg-gray-50 rounded-lg border border-gray-200">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Price drop alert threshold:
              </label>
              <select
                value={threshold}
                onChange={(e) => handleThresholdChange(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-cannabis-500 focus:border-transparent"
              >
                <option value={5}>5% or more</option>
                <option value={10}>10% or more</option>
                <option value={15}>15% or more</option>
                <option value={20}>20% or more</option>
                <option value={25}>25% or more</option>
              </select>
              <p className="mt-2 text-xs text-gray-500">
                You'll get an email when the price drops by this amount or more.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
