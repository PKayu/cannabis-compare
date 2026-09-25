'use client'

import { Suspense, useEffect, useMemo, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { api } from '@/lib/api'
import SearchBar from '@/components/SearchBar'
import FilterPanel from '@/components/FilterPanel'
import ResultsTable from '@/components/ResultsTable'
import JourneyState from '@/components/bloom/JourneyState'
import { activeFilterCount, DEFAULT_FILTERS, filterError, readSearch, searchParams, type SearchFilters } from '@/lib/search-state'
import type { SearchProduct } from '@/lib/product-contracts'

function SearchPageContent() {
  const router = useRouter()
  const url = useSearchParams().toString()
  const { query, filters } = useMemo(() => readSearch(new URLSearchParams(url)), [url])
  const [results, setResults] = useState<SearchProduct[]>([])
  const [state, setState] = useState<'initial' | 'loading' | 'success' | 'error'>('initial')
  const [retry, setRetry] = useState(0)
  const [showFilters, setShowFilters] = useState(false)
  const invalidRange = filterError(filters)
  useEffect(() => {
    let current = true
    if (query.length < 2 || invalidRange) { setState('initial'); setResults([]); return }
    setState('loading'); setResults([])
    const params = Object.fromEntries(searchParams(query, filters))
    api.products.search(params).then(response => {
      if (current) { setResults(response.data); setState('success') }
    }).catch(() => { if (current) setState('error') })
    return () => { current = false }
  }, [query, filters, invalidRange, retry])
  const navigate = (nextQuery: string, nextFilters: SearchFilters) => {
    const next = searchParams(nextQuery, nextFilters).toString()
    if (next === url) setRetry(value => value + 1)
    else router.push(`/products/search${next ? `?${next}` : ''}`, { scroll: false })
  }
  const count = activeFilterCount(filters)
  return <div className="bloom-page pb-16">
    <section className="relative overflow-hidden bg-bloom-navy text-bloom-cream">
      <div aria-hidden="true" className="absolute -right-12 -top-32 h-96 w-96 rounded-full border-[48px] border-bloom-blue opacity-40" />
      <div className="bloom-container relative py-10 sm:py-14"><p className="text-xs font-bold uppercase tracking-[0.2em] text-bloom-mustard">Find your next good thing</p><h1 className="bloom-title mt-3 text-5xl sm:text-6xl">A clearer way to compare.</h1><p className="mt-4 max-w-xl text-base leading-relaxed">Find a product. Explore its sizes. Compare what Utah dispensaries are listing before you make your next stop.</p></div>
    </section>
    <div className="bloom-container pt-8">
      <div className="max-w-3xl"><SearchBar initialQuery={query} onSearch={next => navigate(next, filters)} /></div>
      <div className="mt-8 grid min-w-0 gap-7 lg:grid-cols-[17rem_minmax(0,1fr)]">
        <aside aria-label="Product filters" className="min-w-0"><button className="bloom-button-secondary mb-3 w-full lg:hidden" aria-controls="search-filters" aria-expanded={showFilters} onClick={() => setShowFilters(value => !value)}>{showFilters ? 'Hide filters' : 'Show filters'}{count ? ` (${count} active)` : ''}</button><div id="search-filters" className={`${showFilters ? 'block' : 'hidden'} lg:block`}><FilterPanel filters={filters} onChange={next => navigate(query, next)} /></div></aside>
        <section aria-labelledby="search-results-title" className="min-w-0">
          <div className="mb-5 flex flex-wrap items-center justify-between gap-3"><h2 id="search-results-title" className="text-xl font-bold">{query ? `Results for “${query}”` : 'Your discovery starts here'}</h2>{count > 0 && <span className="rounded-full bg-bloom-parchment px-3 py-1 text-sm font-bold">{count} active {count === 1 ? 'filter' : 'filters'}</span>}</div>
          {invalidRange ? <JourneyState title="Check your filters" error><p>{invalidRange}</p><button className="bloom-button-secondary mt-4" onClick={() => navigate(query, { ...DEFAULT_FILTERS })}>Reset filters</button></JourneyState> : query.length < 2 ? <JourneyState title={query ? 'A little more to go on' : 'What are you looking for?'}><p>{query ? 'Enter at least 2 characters to search.' : 'Search a product name or brand, then narrow by format, price, or potency. We’ll show the available sizes and dispensaries together.'}</p></JourneyState> : state === 'loading' ? <JourneyState title="Gathering prices…" busy><p>Checking the latest available listings.</p></JourneyState> : state === 'error' ? <JourneyState title="We couldn’t load your results" error><p>Your search and filters are still here. Try again in a moment.</p><button className="bloom-button mt-5" onClick={() => setRetry(value => value + 1)}>Try again</button></JourneyState> : state === 'success' && results.length === 0 ? <JourneyState title="No matching products"><p>Try a different name or widen your price and potency ranges.</p>{count > 0 && <button className="bloom-button-secondary mt-5" onClick={() => navigate(query, { ...DEFAULT_FILTERS })}>Clear filters</button>}</JourneyState> : state === 'success' ? <><p role="status" className="mb-5 text-sm text-bloom-muted">{results.length} {results.length === 1 ? 'product' : 'products'} found{results.length === 50 ? ' · Showing up to 50 matches. Refine your search to narrow the list.' : ''}</p><ResultsTable products={results} returnTo={`/products/search?${url}`} /></> : null}
        </section>
      </div>
    </div>
  </div>
}

export default function SearchPage() {
  return <Suspense fallback={<div className="bloom-page p-8"><JourneyState title="Loading search…" busy /></div>}><SearchPageContent /></Suspense>
}
