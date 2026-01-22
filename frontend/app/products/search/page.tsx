'use client'

import React, { useState } from 'react'
import { api, apiClient } from '@/lib/api'
import SearchBar from '@/components/SearchBar'
import FilterPanel from '@/components/FilterPanel'
import ResultsTable from '@/components/ResultsTable'

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

  const handleSearch = async (searchQuery: string) => {
    if (!searchQuery || searchQuery.length < 2) {
      return
    }

    setQuery(searchQuery)
    setLoading(true)

    try {
      const params: any = { q: searchQuery }

      // Add filters if they have values
      if (filters.productType) params.product_type = filters.productType
      if (filters.minPrice !== undefined) params.min_price = filters.minPrice
      if (filters.maxPrice !== undefined) params.max_price = filters.maxPrice
      if (filters.minThc !== undefined) params.min_thc = filters.minThc
      if (filters.maxThc !== undefined) params.max_thc = filters.maxThc
      if (filters.minCbd !== undefined) params.min_cbd = filters.minCbd
      if (filters.maxCbd !== undefined) params.max_cbd = filters.maxCbd
      if (filters.sortBy) params.sort_by = filters.sortBy

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
      // Trigger search with new filters
      handleSearch(query)
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
                <p className="mt-4 text-gray-600">Searching...</p>
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
              <div className="text-center py-12 bg-white rounded-lg shadow">
                <svg className="mx-auto h-16 w-16 text-cannabis-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <p className="mt-4 text-xl text-gray-700">Search for cannabis products</p>
                <p className="text-sm text-gray-500 mt-2">
                  Enter a strain name, brand, or product type to get started
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
