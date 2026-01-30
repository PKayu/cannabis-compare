import React, { useState, useEffect, useRef } from 'react'
import { api } from '@/lib/api'

interface SearchBarProps {
  onSearch: (query: string) => Promise<void> | void
}

interface Suggestion {
  id: string
  name: string
  brand: string | null
  type: string
}

// Fun placeholder suggestions that rotate
const PLACEHOLDER_SUGGESTIONS = [
  "Search for strains, brands, or effects...",
  "Try 'Gorilla Glue'...",
  "Search for 'Blue Dream'...",
  "Find 'OG Kush'...",
  "Look up 'Girl Scout Cookies'...",
  "Search for 'Sour Diesel'...",
]

export default function SearchBar({ onSearch }: SearchBarProps) {
  const [query, setQuery] = useState('')
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [loading, setLoading] = useState(false)
  const [placeholderIndex, setPlaceholderIndex] = useState(0)
  const wrapperRef = useRef<HTMLDivElement>(null)

  // Handle click outside to close suggestions
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setShowSuggestions(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Rotate placeholder text every 3 seconds (only when not focused and empty)
  useEffect(() => {
    if (query) return // Don't rotate if user has typed something

    const interval = setInterval(() => {
      setPlaceholderIndex((prev) => (prev + 1) % PLACEHOLDER_SUGGESTIONS.length)
    }, 3000)

    return () => clearInterval(interval)
  }, [query])

  // Debounced autocomplete
  useEffect(() => {
    if (query.length < 2) {
      setSuggestions([])
      setShowSuggestions(false)
      return
    }

    const timeoutId = setTimeout(async () => {
      setLoading(true)
      try {
        const res = await api.get('/api/products/autocomplete', {
          params: { q: query }
        })
        setSuggestions(res.data)
        setShowSuggestions(true)
      } catch (error) {
        console.error('Autocomplete failed:', error)
        setSuggestions([])
      } finally {
        setLoading(false)
      }
    }, 300) // 300ms debounce

    return () => clearTimeout(timeoutId)
  }, [query])

  const handleSubmit = async (e: React.FormEvent, value?: string) => {
    e.preventDefault()
    const searchTerm = value || query
    if (searchTerm.length < 2) return

    setShowSuggestions(false)
    await onSearch(searchTerm)
  }

  const handleSuggestionClick = async (e: React.MouseEvent, suggestion: Suggestion) => {
    e.preventDefault()
    setQuery(suggestion.name)
    setShowSuggestions(false)
    await onSearch(suggestion.name)
  }

  return (
    <div ref={wrapperRef} className="relative">
      <form onSubmit={handleSubmit} className="mb-4">
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={PLACEHOLDER_SUGGESTIONS[placeholderIndex]}
              className="w-full px-4 py-3 pl-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-cannabis-500 focus:border-transparent placeholder-transition"
              aria-label="Search products"
            />
            <svg
              className={`absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 transition-all duration-300 ${
                query ? 'text-cannabis-600 animate-pulse-slow' : 'text-gray-400'
              }`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
          <button
            type="submit"
            disabled={query.length < 2}
            className="px-6 py-3 bg-cannabis-600 text-white rounded-lg hover:bg-cannabis-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-medium"
          >
            Search
          </button>
        </div>
      </form>

      {/* Autocomplete Dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute z-10 w-full bg-white border border-gray-200 rounded-lg shadow-lg mt-1 max-h-80 overflow-y-auto">
          {suggestions.map((suggestion) => (
            <button
              key={suggestion.id}
              onClick={(e) => handleSuggestionClick(e, suggestion)}
              className="w-full text-left px-4 py-3 hover:bg-gray-50 border-b border-gray-100 last:border-b-0 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div>
                  <span className="font-medium text-gray-900">{suggestion.name}</span>
                  {suggestion.brand && (
                    <span className="text-sm text-gray-500 ml-2">by {suggestion.brand}</span>
                  )}
                </div>
                <span className="text-xs text-gray-400 uppercase">{suggestion.type}</span>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Loading indicator */}
      {loading && showSuggestions && (
        <div className="absolute z-10 w-full bg-white border border-gray-200 rounded-lg shadow-lg mt-1 px-4 py-3">
          <div className="flex items-center text-gray-500">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-cannabis-600 mr-2"></div>
            Loading suggestions...
          </div>
        </div>
      )}
    </div>
  )
}
