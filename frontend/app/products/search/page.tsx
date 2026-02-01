'use client'

import React, { useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import { api, apiClient } from '@/lib/api'
import SearchBar from '@/components/SearchBar'
import FilterPanel from '@/components/FilterPanel'
import ResultsTable from '@/components/ResultsTable'

// Fun loading phrases that rotate
const LOADING_PHRASES = [
  "Searching...",
  "Hunting for deals...",
  "Scouring dispensaries...",
  "Finding your perfect match...",
  "Gathering prices...",
]

// Empty state messages that rotate
const EMPTY_STATE_MESSAGES = [
  {
    title: "Search for cannabis products",
    subtitle: "Enter a strain name, brand, or product type to get started",
  },
  {
    title: "Your perfect strain is waiting to be found...",
    subtitle: "Try searching for a popular strain like 'Gorilla Glue' or 'Blue Dream'",
  },
  {
    title: "Every great search starts with a single query",
    subtitle: "What are you looking for today?",
  },
]

interface SearchFilters {
  productType: string
  minPrice: number | undefined
  maxPrice: number | undefined
  minThc: number | undefined
  maxThc: number | undefined
  minCbd: number | undefined
  maxCbd: number | undefined
  sortBy: string
}

export default function SearchPage() {
  const [results, setResults] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [loadingPhraseIndex, setLoadingPhraseIndex] = useState(0)
  const [emptyStateIndex, setEmptyStateIndex] = useState(0)
  const [query, setQuery] = useState('')
  const [filters, setFilters] = useState<SearchFilters>({
    productType: '',
    minPrice: undefined,
    maxPrice: undefined,
    minThc: undefined,
    maxThc: undefined,
    minCbd: undefined,
    maxCbd: undefined,
    sortBy: 'relevance'
  })

  // Cycle through loading phrases while loading
  useEffect(() => {
    if (!loading) {
      setLoadingPhraseIndex(0)
      return
    }

    const interval = setInterval(() => {
      setLoadingPhraseIndex((prev) => (prev + 1) % LOADING_PHRASES.length)
    }, 800) // Change phrase every 800ms

    return () => clearInterval(interval)
  }, [loading])

  // Cycle through empty state messages (only when not loading and no query)
  useEffect(() => {
    if (loading || query) {
      return
    }

    const interval = setInterval(() => {
      setEmptyStateIndex((prev) => (prev + 1) % EMPTY_STATE_MESSAGES.length)
    }, 5000) // Change message every 5 seconds

    return () => clearInterval(interval)
  }, [loading, query])

  // Read URL parameters and execute search on mount
  const searchParams = useSearchParams()
  useEffect(() => {
    const urlQuery = searchParams.get('q')
    if (urlQuery && urlQuery.length >= 2) {
      // Also read filter parameters from URL
      const urlFilters: SearchFilters = {
        productType: searchParams.get('product_type') || '',
        minPrice: searchParams.get('min_price') ? Number(searchParams.get('min_price')) : undefined,
        maxPrice: searchParams.get('max_price') ? Number(searchParams.get('max_price')) : undefined,
        minThc: searchParams.get('min_thc') ? Number(searchParams.get('min_thc')) : undefined,
        maxThc: searchParams.get('max_thc') ? Number(searchParams.get('max_thc')) : undefined,
        minCbd: searchParams.get('min_cbd') ? Number(searchParams.get('min_cbd')) : undefined,
        maxCbd: searchParams.get('max_cbd') ? Number(searchParams.get('max_cbd')) : undefined,
        sortBy: searchParams.get('sort_by') || 'relevance'
      }

      setFilters(urlFilters)
      handleSearch(urlQuery, urlFilters)
    }
  }, [searchParams])

  const handleSearch = async (searchQuery: string, overrideFilters?: SearchFilters) => {
    if (!searchQuery || searchQuery.length < 2) {
      return
    }

    setQuery(searchQuery)
    setLoading(true)

    try {
      const params: any = { q: searchQuery }

      // Use override filters if provided (for immediate filter changes), otherwise use state
      const filtersToUse = overrideFilters ?? filters

      // Add filters if they have values
      if (filtersToUse.productType) params.product_type = filtersToUse.productType
      if (filtersToUse.minPrice !== undefined) params.min_price = filtersToUse.minPrice
      if (filtersToUse.maxPrice !== undefined) params.max_price = filtersToUse.maxPrice
      if (filtersToUse.minThc !== undefined) params.min_thc = filtersToUse.minThc
      if (filtersToUse.maxThc !== undefined) params.max_thc = filtersToUse.maxThc
      if (filtersToUse.minCbd !== undefined) params.min_cbd = filtersToUse.minCbd
      if (filtersToUse.maxCbd !== undefined) params.max_cbd = filtersToUse.maxCbd
      if (filtersToUse.sortBy) params.sort_by = filtersToUse.sortBy

      const res = await api.products.search(params)
      setResults(res.data)
    } catch (error) {
      console.error('Search failed:', error)
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  // Re-run search when filters change (if we have a query)
  const handleFilterChange = (newFilters: SearchFilters) => {
    setFilters(newFilters)
    if (query) {
      // Pass newFilters directly to handleSearch to avoid stale state
      handleSearch(query, newFilters)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Compliance Banner */}
      <div className="bg-yellow-50 border-b border-yellow-200 py-2 px-4">
        <div className="max-w-7xl mx-auto">
          <p className="text-sm text-yellow-800 text-center">
            ⚠️ For informational purposes only. Not affiliated with any dispensary.
            This site does not sell controlled substances.
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold mb-2 text-cannabis-700">
          Find Your Strain
        </h1>
        <p className="text-gray-600 mb-8">
          Compare prices across Utah dispensaries and find the best deals.
        </p>

        <SearchBar onSearch={handleSearch} />

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 mt-8">
          {/* Filter Panel - Left Sidebar */}
          <div className="lg:col-span-1">
            <FilterPanel filters={filters} onChange={handleFilterChange} />
          </div>

          {/* Results - Main Content */}
          <div className="lg:col-span-3">
            {loading && (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-cannabis-600"></div>
                <p className="mt-4 text-gray-600 animate-pulse">{LOADING_PHRASES[loadingPhraseIndex]}</p>
              </div>
            )}

            {!loading && results.length === 0 && query && (
              <div className="text-center py-12 bg-white rounded-lg shadow">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <p className="mt-4 text-gray-600">No results found for "{query}"</p>
                <p className="text-sm text-gray-500 mt-2">Try adjusting your filters or search term</p>
              </div>
            )}

            {!loading && results.length > 0 && (
              <>
                <div className="flex justify-between items-center mb-4">
                  <p className="text-gray-600">
                    <span className="font-semibold">{results.length}</span> products found
                  </p>
                </div>
                <ResultsTable products={results} />
              </>
            )}

            {!loading && !query && (
              <div className="text-center py-12 bg-white rounded-lg shadow transition-all duration-500">
                <svg className="mx-auto h-16 w-16 text-cannabis-400 animate-float" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <p className="mt-4 text-xl text-gray-700 transition-opacity duration-500">{EMPTY_STATE_MESSAGES[emptyStateIndex].title}</p>
                <p className="text-sm text-gray-500 mt-2 transition-opacity duration-500">
                  {EMPTY_STATE_MESSAGES[emptyStateIndex].subtitle}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
