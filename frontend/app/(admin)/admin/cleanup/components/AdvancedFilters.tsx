'use client'

import React, { useState, useEffect } from 'react'
import { api } from '@/lib/api'

interface AdvancedFiltersProps {
  filters: {
    dispensary_id?: string
    min_confidence?: number
    max_confidence?: number
    match_type?: string
    data_quality?: string
    sort_by?: string
    sort_order?: string
  }
  onChange: (filters: any) => void
}

export function AdvancedFilters({ filters, onChange }: AdvancedFiltersProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [dispensaries, setDispensaries] = useState<any[]>([])

  // Fetch dispensaries for dropdown
  useEffect(() => {
    api.dispensaries.list().then(response => {
      setDispensaries(response.data || [])
    }).catch(err => {
      console.error('Failed to load dispensaries:', err)
    })
  }, [])

  const handleFilterChange = (key: string, value: any) => {
    onChange({ ...filters, [key]: value })
  }

  const handleClearFilters = () => {
    onChange({
      sort_by: 'created_at',
      sort_order: 'desc'
    })
  }

  const activeFilterCount = Object.keys(filters).filter(key =>
    !['sort_by', 'sort_order'].includes(key) && filters[key as keyof typeof filters]
  ).length

  return (
    <div className="mb-6 border rounded-lg bg-white">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="font-medium text-gray-700">Advanced Filters</span>
          {activeFilterCount > 0 && (
            <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs font-medium rounded-full">
              {activeFilterCount} active
            </span>
          )}
        </div>
        <svg
          className={`w-5 h-5 text-gray-500 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Filter Controls */}
      {isExpanded && (
        <div className="px-4 pb-4 space-y-4 border-t">
          {/* Dispensary Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Dispensary
            </label>
            <select
              value={filters.dispensary_id || ''}
              onChange={(e) => handleFilterChange('dispensary_id', e.target.value || undefined)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Dispensaries</option>
              {dispensaries.map(disp => (
                <option key={disp.id} value={disp.id}>
                  {disp.name}
                </option>
              ))}
            </select>
          </div>

          {/* Confidence Range */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Confidence Range
            </label>
            <div className="flex items-center gap-3">
              <div className="flex-1">
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="1"
                  placeholder="Min %"
                  value={filters.min_confidence ? Math.round(filters.min_confidence * 100) : ''}
                  onChange={(e) => handleFilterChange(
                    'min_confidence',
                    e.target.value ? parseFloat(e.target.value) / 100 : undefined
                  )}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <span className="text-gray-500">to</span>
              <div className="flex-1">
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="1"
                  placeholder="Max %"
                  value={filters.max_confidence ? Math.round(filters.max_confidence * 100) : ''}
                  onChange={(e) => handleFilterChange(
                    'max_confidence',
                    e.target.value ? parseFloat(e.target.value) / 100 : undefined
                  )}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Match Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Match Type
            </label>
            <div className="space-y-2">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="match_type"
                  value=""
                  checked={!filters.match_type}
                  onChange={() => handleFilterChange('match_type', undefined)}
                  className="mr-2"
                />
                <span className="text-sm">All</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="match_type"
                  value="cross_dispensary"
                  checked={filters.match_type === 'cross_dispensary'}
                  onChange={(e) => handleFilterChange('match_type', e.target.value)}
                  className="mr-2"
                />
                <span className="text-sm">Cross-Dispensary Only</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="match_type"
                  value="same_dispensary"
                  checked={filters.match_type === 'same_dispensary'}
                  onChange={(e) => handleFilterChange('match_type', e.target.value)}
                  className="mr-2"
                />
                <span className="text-sm">Same-Dispensary Only</span>
              </label>
            </div>
          </div>

          {/* Data Quality */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Data Quality
            </label>
            <div className="space-y-2">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={filters.data_quality?.includes('good') || !filters.data_quality}
                  onChange={(e) => {
                    const qualities = filters.data_quality?.split(',').filter(Boolean) || []
                    if (e.target.checked) {
                      if (!qualities.includes('good')) qualities.push('good')
                    } else {
                      const index = qualities.indexOf('good')
                      if (index > -1) qualities.splice(index, 1)
                    }
                    handleFilterChange('data_quality', qualities.length > 0 ? qualities.join(',') : undefined)
                  }}
                  className="mr-2"
                />
                <span className="text-sm">Good Quality</span>
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={filters.data_quality?.includes('fair') || !filters.data_quality}
                  onChange={(e) => {
                    const qualities = filters.data_quality?.split(',').filter(Boolean) || []
                    if (e.target.checked) {
                      if (!qualities.includes('fair')) qualities.push('fair')
                    } else {
                      const index = qualities.indexOf('fair')
                      if (index > -1) qualities.splice(index, 1)
                    }
                    handleFilterChange('data_quality', qualities.length > 0 ? qualities.join(',') : undefined)
                  }}
                  className="mr-2"
                />
                <span className="text-sm">Fair Quality</span>
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={filters.data_quality?.includes('poor') || !filters.data_quality}
                  onChange={(e) => {
                    const qualities = filters.data_quality?.split(',').filter(Boolean) || []
                    if (e.target.checked) {
                      if (!qualities.includes('poor')) qualities.push('poor')
                    } else {
                      const index = qualities.indexOf('poor')
                      if (index > -1) qualities.splice(index, 1)
                    }
                    handleFilterChange('data_quality', qualities.length > 0 ? qualities.join(',') : undefined)
                  }}
                  className="mr-2"
                />
                <span className="text-sm">Poor Quality</span>
              </label>
            </div>
          </div>

          {/* Sort Options */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Sort By
            </label>
            <div className="grid grid-cols-2 gap-2">
              <select
                value={filters.sort_by || 'created_at'}
                onChange={(e) => handleFilterChange('sort_by', e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="created_at">Date Created</option>
                <option value="confidence">Confidence Score</option>
              </select>
              <select
                value={filters.sort_order || 'desc'}
                onChange={(e) => handleFilterChange('sort_order', e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="desc">Descending</option>
                <option value="asc">Ascending</option>
              </select>
            </div>
          </div>

          {/* Clear Filters Button */}
          {activeFilterCount > 0 && (
            <button
              onClick={handleClearFilters}
              className="w-full px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-md transition-colors"
            >
              Clear All Filters
            </button>
          )}
        </div>
      )}
    </div>
  )
}
