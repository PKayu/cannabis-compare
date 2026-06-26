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

const PLACEHOLDER_SUGGESTIONS = [
  "Search strains, brands, or effects...",
  "Try 'Gorilla Glue'...",
  "Search 'Blue Dream'...",
  "Find 'OG Kush'...",
  "Look up 'Girl Scout Cookies'...",
  "Search 'Sour Diesel'...",
]

export default function SearchBar({ onSearch }: SearchBarProps) {
  const [query, setQuery] = useState('')
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [loading, setLoading] = useState(false)
  const [placeholderIndex, setPlaceholderIndex] = useState(0)
  const wrapperRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setShowSuggestions(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  useEffect(() => {
    if (query) return
    const interval = setInterval(() => {
      setPlaceholderIndex((prev) => (prev + 1) % PLACEHOLDER_SUGGESTIONS.length)
    }, 3000)
    return () => clearInterval(interval)
  }, [query])

  useEffect(() => {
    if (query.length < 2) {
      setSuggestions([])
      setShowSuggestions(false)
      return
    }
    const timeoutId = setTimeout(async () => {
      setLoading(true)
      try {
        const res = await api.get('/api/products/autocomplete', { params: { q: query } })
        setSuggestions(res.data)
        setShowSuggestions(true)
      } catch {
        setSuggestions([])
      } finally {
        setLoading(false)
      }
    }, 300)
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
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={PLACEHOLDER_SUGGESTIONS[placeholderIndex]}
              className="input-groovy pl-12 placeholder-transition"
              aria-label="Search products"
            />
            <svg
              className={`absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 transition-colors duration-300 ${
                query ? 'text-groovy-amber' : 'text-stone-400'
              }`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <button
            type="submit"
            disabled={query.length < 2}
            className="btn-groovy-teal disabled:opacity-40 disabled:cursor-not-allowed disabled:translate-y-0 disabled:shadow-sticker"
          >
            Search
          </button>
        </div>
      </form>

      {/* Autocomplete dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute z-10 w-full bg-groovy-cream border-2 border-groovy-ink rounded-2xl shadow-sticker mt-1 max-h-80 overflow-y-auto">
          {suggestions.map((suggestion) => (
            <button
              key={suggestion.id}
              onClick={(e) => handleSuggestionClick(e, suggestion)}
              className="w-full text-left px-4 py-3 hover:bg-amber-50 border-b-2 border-stone-200 last:border-b-0 transition-colors font-body"
            >
              <div className="flex items-center justify-between">
                <div>
                  <span className="font-semibold text-groovy-ink">{suggestion.name}</span>
                  {suggestion.brand && (
                    <span className="text-sm text-stone-500 ml-2">by {suggestion.brand}</span>
                  )}
                </div>
                <span className="text-xs font-display font-semibold text-groovy-teal uppercase px-2 py-0.5 bg-teal-50 rounded-full border border-groovy-teal">
                  {suggestion.type}
                </span>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Loading */}
      {loading && showSuggestions && (
        <div className="absolute z-10 w-full bg-groovy-cream border-2 border-groovy-ink rounded-2xl shadow-sticker mt-1 px-4 py-3">
          <div className="flex items-center text-stone-500 font-body">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-groovy-teal mr-2"></div>
            Finding matches…
          </div>
        </div>
      )}
    </div>
  )
}
