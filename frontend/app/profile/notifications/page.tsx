'use client'

import React, { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'
import { ProtectedRoute } from '@/components/ProtectedRoute'

interface NotificationPreferences {
  user_id: string
  email_stock_alerts: boolean
  email_price_drops: boolean
  email_frequency: string
  app_notifications: boolean
}

function NotificationContent() {
  const router = useRouter()
  const [prefs, setPrefs] = useState<NotificationPreferences | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    loadPreferences()
  }, [])

  const loadPreferences = async () => {
    try {
      const response = await api.notifications.getPreferences()
      setPrefs(response.data)
    } catch (error) {
      console.error('Failed to load preferences:', error)
      // ProtectedRoute will handle 401 redirects
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!prefs) return

    setSaving(true)
    setSaved(false)
    try {
      await api.notifications.updatePreferences(prefs)
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (error) {
      console.error('Failed to save preferences:', error)
      alert('Failed to save preferences. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-2xl mx-auto px-4">
          <h1 className="text-3xl font-bold mb-8">Notification Preferences</h1>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (!prefs) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-2xl mx-auto px-4">
          <h1 className="text-3xl font-bold mb-8">Notification Preferences</h1>
          <p className="text-red-600">Failed to load preferences.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-2xl mx-auto px-4">
        <h1 className="text-3xl font-bold mb-2">Notification Preferences</h1>
        <p className="text-gray-600 mb-8">
          Manage how and when you receive alerts about products on your watchlist.
        </p>

        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-bold mb-6">Email Alerts</h2>

          <div className="space-y-4 mb-6">
            <label className="flex items-start">
              <input
                type="checkbox"
                checked={prefs.email_stock_alerts}
                onChange={(e) => setPrefs({ ...prefs, email_stock_alerts: e.target.checked })}
                className="mt-1 h-4 w-4 text-cannabis-600 focus:ring-cannabis-500 border-gray-300 rounded"
              />
              <span className="ml-3">
                <span className="block text-sm font-medium text-gray-700">
                  Stock availability alerts
                </span>
                <span className="block text-sm text-gray-500">
                  Get notified when watched products come back in stock
                </span>
              </span>
            </label>

            <label className="flex items-start">
              <input
                type="checkbox"
                checked={prefs.email_price_drops}
                onChange={(e) => setPrefs({ ...prefs, email_price_drops: e.target.checked })}
                className="mt-1 h-4 w-4 text-cannabis-600 focus:ring-cannabis-500 border-gray-300 rounded"
              />
              <span className="ml-3">
                <span className="block text-sm font-medium text-gray-700">
                  Price drop alerts
                </span>
                <span className="block text-sm text-gray-500">
                  Get notified when prices drop on watched products
                </span>
              </span>
            </label>
          </div>

          <div className="border-t pt-6">
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Email Frequency
            </label>
            <div className="space-y-3">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="frequency"
                  value="immediately"
                  checked={prefs.email_frequency === 'immediately'}
                  onChange={(e) => setPrefs({ ...prefs, email_frequency: e.target.value })}
                  className="h-4 w-4 text-cannabis-600 focus:ring-cannabis-500 border-gray-300"
                />
                <span className="ml-3">
                  <span className="block text-sm font-medium text-gray-700">
                    Immediately
                  </span>
                  <span className="block text-sm text-gray-500">
                    Get emails as soon as alerts are detected (checked hourly)
                  </span>
                </span>
              </label>

              <label className="flex items-center opacity-60">
                <input
                  type="radio"
                  name="frequency"
                  value="daily"
                  checked={prefs.email_frequency === 'daily'}
                  onChange={(e) => setPrefs({ ...prefs, email_frequency: e.target.value })}
                  className="h-4 w-4 text-cannabis-600 focus:ring-cannabis-500 border-gray-300"
                />
                <span className="ml-3">
                  <span className="block text-sm font-medium text-gray-700">
                    Daily Digest
                  </span>
                  <span className="block text-sm text-gray-500">
                    Receive one email per day with all alerts <span className="text-cannabis-600 font-medium">(Planned feature)</span>
                  </span>
                </span>
              </label>

              <label className="flex items-center opacity-60">
                <input
                  type="radio"
                  name="frequency"
                  value="weekly"
                  checked={prefs.email_frequency === 'weekly'}
                  onChange={(e) => setPrefs({ ...prefs, email_frequency: e.target.value })}
                  className="h-4 w-4 text-cannabis-600 focus:ring-cannabis-500 border-gray-300"
                />
                <span className="ml-3">
                  <span className="block text-sm font-medium text-gray-700">
                    Weekly Summary
                  </span>
                  <span className="block text-sm text-gray-500">
                    Receive one email per week with all alerts <span className="text-cannabis-600 font-medium">(Planned feature)</span>
                  </span>
                </span>
              </label>
            </div>
          </div>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-800">About Email Alerts</h3>
              <div className="mt-2 text-sm text-blue-700">
                <p>
                  Currently, only "Immediate" email delivery is available. Daily and weekly digests are planned for a future update.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-8 flex items-center justify-between">
          <button
            onClick={handleSave}
            disabled={saving}
            className={`px-6 py-3 rounded-lg font-medium transition ${
              saving
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-cannabis-600 hover:bg-cannabis-700'
            } text-white`}
          >
            {saving ? 'Saving...' : 'Save Preferences'}
          </button>

          {saved && (
            <p className="text-green-600 font-medium flex items-center gap-2">
              <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              Preferences saved!
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

export default function NotificationPreferencesPage() {
  return (
    <ProtectedRoute>
      <NotificationContent />
    </ProtectedRoute>
  )
}
