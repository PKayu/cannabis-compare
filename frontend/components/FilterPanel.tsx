'use client'

import { useEffect, useId, useState } from 'react'
import { DEFAULT_FILTERS, PRODUCT_TYPES, SORT_OPTIONS, filterError, type SearchFilters } from '@/lib/search-state'

export default function FilterPanel({ filters, onChange }: { filters: SearchFilters; onChange: (filters: SearchFilters) => void }) {
  const [draft, setDraft] = useState(filters)
  const [error, setError] = useState<string | null>(null)
  const id = useId()
  useEffect(() => { setDraft(filters); setError(null) }, [filters])
  const input = (field: 'minPrice' | 'maxPrice' | 'minThc' | 'maxThc' | 'minCbd' | 'maxCbd', label: string, max?: number) => <div>
    <label className="mb-1 block text-xs font-bold text-bloom-muted" htmlFor={`${id}-${field}`}>{label}</label>
    <input id={`${id}-${field}`} type="number" min={0} max={max} step={field.includes('Price') ? '0.01' : '0.1'} className="bloom-input" placeholder="Any" value={draft[field] ?? ''} onChange={event => setDraft({ ...draft, [field]: event.target.value === '' ? undefined : Number(event.target.value) })} />
  </div>
  return <form className="bloom-panel p-5" aria-label="Search filters" onSubmit={event => { event.preventDefault(); const problem = filterError(draft); setError(problem); if (!problem) onChange(draft) }}>
    <div className="mb-6 flex flex-wrap items-center justify-between gap-2"><h2 className="text-lg font-bold">Refine your search</h2><button className="min-h-[44px] text-sm font-bold underline underline-offset-4" type="button" onClick={() => { setDraft({ ...DEFAULT_FILTERS }); setError(null); onChange({ ...DEFAULT_FILTERS }) }}>Reset filters</button></div>
    <div className="space-y-5">
      <div><label htmlFor={`${id}-type`} className="mb-2 block text-sm font-bold">Product type</label><select id={`${id}-type`} className="bloom-input" value={draft.productType} onChange={event => setDraft({ ...draft, productType: event.target.value })}>{!PRODUCT_TYPES.includes(draft.productType) && <option value={draft.productType}>{draft.productType}</option>}{PRODUCT_TYPES.map(type => <option key={type} value={type}>{type === '' ? 'All types' : type === 'vaporizer' ? 'Vape' : type.charAt(0).toUpperCase() + type.slice(1)}</option>)}</select></div>
      <fieldset><legend className="mb-2 text-sm font-bold">Price range (USD)</legend><div className="grid grid-cols-2 gap-3">{input('minPrice', 'Minimum price')}{input('maxPrice', 'Maximum price')}</div></fieldset>
      <fieldset><legend className="mb-2 text-sm font-bold">THC range (%)</legend><div className="grid grid-cols-2 gap-3">{input('minThc', 'Minimum THC', 100)}{input('maxThc', 'Maximum THC', 100)}</div></fieldset>
      <fieldset><legend className="mb-2 text-sm font-bold">CBD range (%)</legend><div className="grid grid-cols-2 gap-3">{input('minCbd', 'Minimum CBD', 100)}{input('maxCbd', 'Maximum CBD', 100)}</div></fieldset>
      <div><label htmlFor={`${id}-sort`} className="mb-2 block text-sm font-bold">Sort results</label><select id={`${id}-sort`} className="bloom-input" value={draft.sortBy} onChange={event => setDraft({ ...draft, sortBy: event.target.value as SearchFilters['sortBy'] })}>{SORT_OPTIONS.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}</select></div>
      {error && <p role="alert" className="text-sm font-bold text-bloom-error">{error}</p>}
      <button type="submit" className="bloom-button w-full">Apply filters</button>
      <p className="text-xs leading-relaxed text-bloom-muted">Potency filters exclude products whose potency has not been reported.</p>
    </div>
  </form>
}
