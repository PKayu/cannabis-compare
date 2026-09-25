'use client'

import { useEffect, useId, useState } from 'react'
import { DEFAULT_FILTERS, PRODUCT_TYPES, SORT_OPTIONS, filterError, type SearchFilters } from '@/lib/search-state'

export default function FilterPanel({ filters, onChange }: { filters: SearchFilters; onChange: (filters: SearchFilters) => void }) {
  const [draft, setDraft] = useState(filters)
  const [error, setError] = useState<string | null>(null)
  const id = useId()
  useEffect(() => { setDraft(filters); setError(null) }, [filters])
  const input = (field: 'minPrice' | 'maxPrice' | 'minThc' | 'maxThc' | 'minCbd' | 'maxCbd', label: string, max?: number) => <div>
    <label className="mb-1 block text-xs font-bold text-bloom-cream/85" htmlFor={`${id}-${field}`}>{label}</label>
    <input id={`${id}-${field}`} type="number" min={0} max={max} step={field.includes('Price') ? '0.01' : '0.1'} className="bloom-input" placeholder="Any" value={draft[field] ?? ''} onChange={event => setDraft({ ...draft, [field]: event.target.value === '' ? undefined : Number(event.target.value) })} />
  </div>

  return <form className="rounded-[2rem] border border-bloom-cream/30 bg-bloom-navy p-5 text-bloom-cream shadow-[4px_4px_0_#102A32] sm:p-6" aria-label="Search filters" onSubmit={event => { event.preventDefault(); const problem = filterError(draft); setError(problem); if (!problem) onChange(draft) }}>
    <div className="mb-5 flex flex-wrap items-center justify-between gap-3"><div><p className="text-xs font-bold uppercase tracking-[0.18em] text-bloom-mustard">Make it yours</p><h2 className="bloom-title mt-1 text-3xl">Tune the menu</h2></div><button className="min-h-[44px] rounded-full px-3 text-sm font-bold underline decoration-bloom-mustard underline-offset-4 hover:text-bloom-mustard" type="button" onClick={() => { setDraft({ ...DEFAULT_FILTERS }); setError(null); onChange({ ...DEFAULT_FILTERS }) }}>Reset filters</button></div>
    <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
      <div><label htmlFor={`${id}-type`} className="mb-2 block text-sm font-bold">Product type</label><select id={`${id}-type`} className="bloom-input" value={draft.productType} onChange={event => setDraft({ ...draft, productType: event.target.value })}>{!PRODUCT_TYPES.includes(draft.productType) && <option value={draft.productType}>{draft.productType}</option>}{PRODUCT_TYPES.map(type => <option key={type} value={type}>{type === '' ? 'All types' : type === 'vaporizer' ? 'Vape' : type.charAt(0).toUpperCase() + type.slice(1)}</option>)}</select></div>
      <fieldset><legend className="mb-2 text-sm font-bold">Price range (USD)</legend><div className="grid grid-cols-2 gap-3">{input('minPrice', 'Minimum price')}{input('maxPrice', 'Maximum price')}</div></fieldset>
      <fieldset><legend className="mb-2 text-sm font-bold">THC range (%)</legend><div className="grid grid-cols-2 gap-3">{input('minThc', 'Minimum THC', 100)}{input('maxThc', 'Maximum THC', 100)}</div></fieldset>
      <div><label htmlFor={`${id}-sort`} className="mb-2 block text-sm font-bold">Sort results</label><select id={`${id}-sort`} className="bloom-input" value={draft.sortBy} onChange={event => setDraft({ ...draft, sortBy: event.target.value as SearchFilters['sortBy'] })}>{SORT_OPTIONS.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}</select><p className="mt-3 text-xs leading-relaxed text-bloom-cream/75">Potency filters exclude products whose potency is not reported.</p></div>
      <fieldset className="sm:col-span-2 xl:col-span-3"><legend className="mb-2 text-sm font-bold">CBD range (%)</legend><div className="grid max-w-sm grid-cols-2 gap-3">{input('minCbd', 'Minimum CBD', 100)}{input('maxCbd', 'Maximum CBD', 100)}</div></fieldset>
      <div className="flex items-end"><button type="submit" className="bloom-button-secondary w-full">Apply filters</button></div>
    </div>
    {error && <p role="alert" className="mt-4 text-sm font-bold text-bloom-mustard">{error}</p>}
  </form>
}
